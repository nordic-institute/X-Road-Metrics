#  The MIT License
#  Copyright (c) 2021- Nordic Institute for Interoperability Solutions (NIIS)
#  Copyright (c) 2017-2020 Estonian Information System Authority (RIA)
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

import datetime
import requests
import urllib
from operator import itemgetter

import pymongo


def get_mongo_uri(settings: dict) -> str:
    user = settings['mongodb']['user']
    password = urllib.parse.quote(settings['mongodb']['password'], safe='')
    host = settings['mongodb']['host']
    return f'mongodb://{user}:{password}@{host}/auth_db'


def get_query_db(client) -> pymongo.database.Database:
    query_db = 'query_db_PLAYGROUND'
    db = client[query_db]
    return db


def do_request(source_settings, from_dt, limit=None, from_row_id=None, offset=None):
    url = source_settings['url']

    params = {
        'from_dt': from_dt,
        'timestamp_tz': source_settings.get('timestamp_tz')
    }
    if limit:
        params['limit'] = limit

    if from_row_id:
        params['from_row_id'] = from_row_id

    if offset:
        params['offset'] = offset

    encoded_params = urllib.parse.urlencode(params)
    url = f'{url}?{encoded_params}'

    response = requests.get(url)

    if response.status_code != 200:
        response = response.json()
        raise Exception(f'Something wrong: {response}')
    return response.json()


def collect_opendata(settings: dict, source_settings: dict):

    from_dt = source_settings['from_dt'].isoformat()
    limit = source_settings['limit']
    from_row_id = None

    client = pymongo.MongoClient(get_mongo_uri(settings))
    state_db = client['opendata_collector_PLAYGROUND']  # FIX name
    state = state_db.state.find_one({'instance_id': 'PLAYGROUND-TEST'}) or {}

    if state:
        forma = '%Y-%m-%dT%H:%M:%S'
        dt_object = datetime.datetime.fromtimestamp(state['last_inserted_requestints']/1000)

        from_dt = dt_object.strftime(forma)
        from_row_id = state['last_inserted_row_id']

    data = do_request(
        source_settings, from_dt=from_dt, limit=limit,
        from_row_id=from_row_id
    )

    rows = data['data']
    if not rows:
        return
    columns = data['columns']
    total_query_count = data['total_query_count']

    documents = get_documents(rows, columns)
    inserted = insert_into_db(client, documents)
    docs = sorted(documents, key=itemgetter('requestInTs', 'id'), reverse=True)
    state_db.state.update_one(
        {'instance_id': 'PLAYGROUND-TEST'},
        {
            '$set': {
                'last_inserted_requestints': docs[0]['requestInTs'],
                'last_inserted_row_id': docs[0]['id']
            }
        },
        upsert=True
        )

    if total_query_count > inserted:
        total_inserted = inserted
        limit = source_settings['limit']
        offset = limit
        while total_inserted < total_query_count:
            data = do_request(source_settings, from_dt, limit, from_row_id, offset)
            rows = data['data']
            columns = data['columns']
            documents = get_documents(rows, columns)
            inserted = insert_into_db(client, documents)
            docs = sorted(documents, key=itemgetter('requestInTs', 'id'), reverse=True)
            state_db.state.update_one(
                {'instance_id': 'PLAYGROUND-TEST'},
                {
                    '$set': {
                        'last_inserted_requestints': docs[0]['requestInTs'],
                        'last_inserted_row_id': docs[0]['id']
                    }
                },
                upsert=True
            )

            total_inserted += inserted
            offset += limit


def get_documents(rows, columns):
    documents = []
    for data in rows:
        normalized = []
        for entry in data:
            if entry == 'None':
                normalized.append(None)
            else:
                normalized.append(entry)
        doc = dict(zip(columns, normalized))
        # doc.pop('id', None)
        doc['requestInTs'] = int(doc['requestInTs'])
        if doc.get('totalDuration'):
            doc['totalDuration'] = int(doc['totalDuration'])
        if doc.get('producerDurationProducerView'):
            doc['producerDurationProducerView'] = int(doc['producerDurationProducerView'])
        documents.append(doc)
    return documents

def insert_into_db(client, documents):
    db = get_query_db(client)
    opendata_col = db['opendata_data']
    opendata_col.insert_many(documents)
    return len(documents)
