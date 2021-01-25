from pymongo import MongoClient
import pymongo
import datetime
import sqlite3 as sql
import os
import signal
from signal import SIGABRT, SIGILL, SIGINT, SIGSEGV, SIGTERM, SIGHUP
import traceback
from anonymizer.utils import logger_manager
import sys

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

ATEXIT_SINGLETON = None


def store_last_processed_timestamp(*args):
    ATEXIT_SINGLETON.update_last_processed_timestamp(max_timestamp=ATEXIT_SINGLETON.last_processed_timestamp)
    sys.exit(1)

for sig in (SIGABRT, SIGILL, SIGINT, SIGSEGV, SIGTERM, SIGHUP):
    signal.signal(sig, store_last_processed_timestamp)


class MongoDB_Manager(object):

    def __init__(self, config, previous_run_manager=None):
        self._logger = logger_manager.LoggerManager(logger_name='opendata-anonymizer', module_name='opendata')

        global ATEXIT_SINGLETON
        ATEXIT_SINGLETON = self

        self._config = config
        self.mongo_connection_string = "mongodb://{user}:{password}@{host}:{port}/{database}".format(
            **{'user': config.mongo_db['user'],
               'password': config.mongo_db['password'],
               'host': config.mongo_db['host_address'],
               'port': config.mongo_db['port'],
               'database': config.mongo_db['auth_db']})
        self._mongo_client = MongoClient(self.mongo_connection_string)

        self._previous_run_manager = previous_run_manager if previous_run_manager else PreviousRunManager(config)
        self.last_processed_timestamp = self._get_last_processed_timestamp()

    def get_records(self, allowed_fields):
        collection = self._mongo_client[self._config.mongo_db['database_name']][self._config.mongo_db['table_name']]

        min_timestamp = self._get_last_processed_timestamp()

        projection = {field: True for field in allowed_fields}
        projection['correctorTime'] = True

        batch_idx = 0

        current_timestamp = datetime.datetime.now().timestamp()

        for document in collection.find({
            'correctorTime': {'$gt': min_timestamp, '$lte': current_timestamp},
            'correctorStatus': 'done',
            'client.clientXRoadInstance': {'$ne': None}
        }, projection=projection, no_cursor_timeout=True).sort('correctorTime', pymongo.ASCENDING):
            if batch_idx == 1000:
                self.update_last_processed_timestamp(max_timestamp=self.last_processed_timestamp)
                batch_idx = 0

            self.last_processed_timestamp = document['correctorTime']
            del document['_id']
            del document['correctorTime']
            yield self._add_missing_fields(document, allowed_fields)
            batch_idx += 1

        self.update_last_processed_timestamp(max_timestamp=self.last_processed_timestamp)

    def is_alive(self):
        try:
            self._mongo_client[self._config.mongo_db['database_name']][self._config.mongo_db['table_name']].find_one()
            return True

        except Exception:
            self._logger.log_error('mongodb_connection_failed',
                                   ("Failed to connect to mongodb with connection string {0}. ERROR: {1}".format(
                                       self.mongo_connection_string, traceback.format_exc().replace('\n', '')))
                                   )
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
                        document[field_path[0]][field_path[1]] = self._get_default_value(field_path)
                elif len(field_path) == 1:
                    if field_path[0] not in document:
                        document[field_path[0]] = self._get_default_value(field_path)

            return document
        except Exception:
            self._logger.log_error('adding_missing_fields_failed',
                                   ("Failed adding missing fields from {0} to document {1}. ERROR: {2}".format(
                                       str(allowed_fields), str(document), traceback.format_exc().replace('\n', ''))))
            raise

    def _get_default_value(self, field_path):
        return None

    def _get_last_processed_timestamp(self):
        min_timestamp = self._previous_run_manager.get_previous_run()
        return min_timestamp

    def update_last_processed_timestamp(self, max_timestamp):
        if max_timestamp:
            self._previous_run_manager.set_previous_run(max_timestamp)

    def __del__(self):
        self.update_last_processed_timestamp(max_timestamp=self.last_processed_timestamp)


class PreviousRunManager(object):

    initial_value = 0.0

    def __init__(self, config):
        self._config = config

        self.mongo_connection_string = "mongodb://{user}:{password}@{host}:{port}/{database}".format(
            **{'user': config.mongo_db['user'],
               'password': config.mongo_db['password'],
               'host': config.mongo_db['host_address'],
               'port': config.mongo_db['port'],
               'database': config.mongo_db['auth_db']})

        self._mongo_client = MongoClient(self.mongo_connection_string)

    def get_previous_run(self):
        collection = self._mongo_client[self._config.mongo_db['state']['database_name']][
            self._config.mongo_db['state']['table_name']]
        entry = collection.find_one({'key': 'last_mongodb_timestamp'})
        if entry:
            return float(entry['value'])
        else:
            return self.initial_value

    def set_previous_run(self, max_timestamp):
        collection = self._mongo_client[self._config.mongo_db['state']['database_name']][
            self._config.mongo_db['state']['table_name']]
        collection.update(
            {'key': 'last_mongodb_timestamp'},
            {'key': 'last_mongodb_timestamp', 'value': str(max_timestamp)},
            upsert=True
        )
