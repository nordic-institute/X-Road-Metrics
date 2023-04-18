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
from operator import itemgetter

import requests

from metrics_opendata_collector.logger_manager import LoggerManager
from metrics_opendata_collector.mongodbmanager import MongoDbManager
from metrics_opendata_collector.opendata_api_client import OpenDataAPIClient

from . import __version__


def collect_opendata(source_id: str, settings: dict, source_settings: dict):
    logger_m = LoggerManager(settings['logger'], settings['xroad']['instance'], __version__)
    mongo_manager = MongoDbManager(settings, source_id)
    client = OpenDataAPIClient(settings, source_settings)

    state = mongo_manager.get_last_inserted_entry()
    params_overrides = {}
    if state:
        params_overrides['from_dt'] = _ts_to_isoformat_string(
            state['last_inserted_requestints'] / 1000
        )
        params_overrides['from_row_id'] = state['last_inserted_row_id']

    params = client.get_request_params(params_overrides)
    logger_m.log_info(
        'get_opendata',
        (
            f'{source_id}: fetching opendata for {source_id} '
            f'from_dt: {params["from_dt"]}, '
            f'from_row_id: {params.get("from_row_id")}'
        )
    )
    try:
        data = client.get_opendata(params)
    except requests.exceptions.HTTPError as http_error:
        logger_m.log_error('get_opendata_main_failed', str(http_error))
        return
    total_inserted = 0
    rows = data['data']
    columns = data['columns']
    row_range = data['row_range']
    total_query_count = data['total_query_count']
    if rows:
        logger_m.log_info(
            'get_opendata',
            f'{source_id}: received {len(rows)} rows from total {total_query_count} within range {row_range}'
        )
        documents = _prepare_documents(rows, columns)
        _insert_documents(mongo_manager, documents)
        logger_m.log_info(
            'get_opendata',
            f'{source_id}: inserted {len(documents)} opendata documents into MongoDB'
        )
        total_inserted += len(documents)
        if total_query_count > len(documents):
            limit = source_settings['limit']
            offset = limit
            while total_inserted < total_query_count:
                params['offset'] = offset
                try:
                    data = client.get_opendata(params)
                except requests.exceptions.HTTPError as http_error:
                    logger_m.log_error('get_opendata_failed', str(http_error))
                    break
                rows = data['data']
                row_range = data['row_range']
                total_query_count = data['total_query_count']
                logger_m.log_info(
                    'get_opendata',
                    f'{source_id}: received {len(rows)} rows from total {total_query_count} within range {row_range}'
                )
                documents = _prepare_documents(rows, columns)
                _insert_documents(mongo_manager, documents)
                logger_m.log_info(
                    'get_opendata',
                    f'{source_id}: inserted {len(documents)} opendata documents into MongoDB'
                )
                total_inserted += len(documents)
                offset += limit

    logger_m.log_info(
        'get_opendata',
        f'{source_id}: total inserted {total_inserted} opendata documents into MongoDB'
    )


def _ts_to_isoformat_string(ts: int) -> str:
    iso_format = '%Y-%m-%dT%H:%M:%S%z'
    dt_object = datetime.datetime.fromtimestamp(ts)
    return dt_object.strftime(iso_format)


def _insert_documents(mongo_manager, documents):
    mongo_manager.insert_documents(documents)
    docs_sorted = sorted(documents, key=itemgetter('requestInTs', 'id'), reverse=True)
    mongo_manager.set_last_inserted_entry(docs_sorted[0])


def _prepare_documents(rows, columns):
    documents = []
    for data in rows:
        normalized = [None if entry == 'None' else entry for entry in data]
        doc = dict(zip(columns, normalized))
        doc['requestInTs'] = int(doc['requestInTs'])
        if doc.get('totalDuration'):
            doc['totalDuration'] = int(doc.get('totalDuration') or 0)
        if doc.get('producerDurationProducerView'):
            doc['producerDurationProducerView'] = int(doc.get('producerDurationProducerView') or 0)
        documents.append(doc)
    return documents
