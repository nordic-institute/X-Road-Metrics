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

from pymongo import MongoClient
import pymongo
import datetime
import traceback
import urllib.parse
import sys


class MongoDbManager(object):

    def __init__(self, settings, logger):
        self.settings = settings
        xroad = settings['xroad']['instance']
        self._logger = logger

        self.client = MongoClient(self.get_mongo_uri(settings))
        self.query_db = self.client[f"query_db_{xroad}"]
        self.state_db = self.client[f"anonymizer_state_{xroad}"]

        self.last_processed_timestamp = self.get_last_processed_timestamp()

    @staticmethod
    def get_mongo_uri(settings):
        user = settings['mongodb']['user']
        password = urllib.parse.quote(settings['mongodb']['password'], safe='')
        host = settings['mongodb']['host']
        return f"mongodb://{user}:{password}@{host}/auth_db"

    def get_records(self, allowed_fields):
        collection = self.query_db.clean_data

        min_timestamp = self.get_last_processed_timestamp()

        projection = {field: True for field in allowed_fields}
        projection['correctorTime'] = True

        batch_idx = 0

        current_timestamp = datetime.datetime.now().timestamp()

        documents = collection.find(
            {
                'correctorTime': {'$gt': min_timestamp, '$lte': current_timestamp},
                'correctorStatus': 'done',
                'client.clientXRoadInstance': {'$ne': None}
            },
            projection=projection,
            no_cursor_timeout=True
        ).sort('correctorTime', pymongo.ASCENDING)

        for document in documents:
            if batch_idx == 1000:
                self.set_last_processed_timestamp()
                batch_idx = 0

            self.last_processed_timestamp = document['correctorTime']
            del document['_id']
            del document['correctorTime']
            yield self._add_missing_fields(document, allowed_fields)
            batch_idx += 1

        self.set_last_processed_timestamp()

    def is_alive(self):
        try:
            self.query_db.clean_data.find_one()
            return True

        except Exception:
            trace = traceback.format_exc().replace('\n', '')
            self._logger.log_error('mongodb_connection_failed',
                                   f"Failed to connect to mongodb at {self.client.address}. ERROR: {trace}")
            return False

    def _add_missing_fields(self, document, allowed_fields):
        try:
            existing_agents = [agent for agent in ['client', 'producer'] if agent in document]

            for field in allowed_fields:
                field_path = field.split('.')
                if len(field_path) == 2 and field_path[0] in existing_agents:
                    if field_path[0] not in document:
                        document[field_path[0]] = {}
                    if field_path[1] not in document[field_path[0]]:
                        document[field_path[0]][field_path[1]] = None
                elif len(field_path) == 1:
                    if field_path[0] not in document:
                        document[field_path[0]] = None

            return document
        except Exception:
            self._logger.log_error('adding_missing_fields_failed',
                                   ("Failed adding missing fields from {0} to document {1}. ERROR: {2}".format(
                                       str(allowed_fields), str(document), traceback.format_exc().replace('\n', ''))))
            raise

    def get_last_processed_timestamp(self):
        state = self.state_db.state.find_one({'key': 'last_mongodb_timestamp'}) or {}
        return float(state.get('value') or 0.0)

    def set_last_processed_timestamp(self):
        if not self.last_processed_timestamp:
            return

        self.state_db.state.update(
            {'key': 'last_mongodb_timestamp'},
            {'key': 'last_mongodb_timestamp', 'value': str(self.last_processed_timestamp)},
            upsert=True
        )

    def handle_signal(self, signum, frame):
        print('signal', signum, frame)
        self.save_on_exit()
        sys.exit(1)
