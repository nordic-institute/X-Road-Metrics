from pymongo import MongoClient
import pymongo
import datetime
import signal
from signal import SIGABRT, SIGILL, SIGINT, SIGSEGV, SIGTERM, SIGHUP
import traceback
from opmon_anonymizer.utils import logger_manager
import sys


class MongoDbManager(object):

    def __init__(self, settings):
        self.settings = settings
        xroad = settings['xroad']['instance']
        self._logger = logger_manager.LoggerManager(settings['logger'], xroad)

        self.client = MongoClient(self.get_mongo_uri(settings))
        self.query_db = self.client[f"query_db_{xroad}"]
        self.state_db = self.client[f"anonymizer_state_{xroad}"]

        self.last_processed_timestamp = self.get_previous_run()
        for sig in (SIGABRT, SIGILL, SIGINT, SIGSEGV, SIGTERM, SIGHUP):
            signal.signal(sig, self.handle_signal)

    @staticmethod
    def get_mongo_uri(settings):
        user = settings['mongodb']['user']
        password = settings['mongodb']['password']
        host = settings['mongodb']['host']
        return f"mongodb://{user}:{password}@{host}/auth_db"

    def get_records(self, allowed_fields):
        collection = self.query_db.clean_data

        min_timestamp = self.get_previous_run()

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
                self.set_previous_run(max_timestamp=self.last_processed_timestamp)
                batch_idx = 0

            self.last_processed_timestamp = document['correctorTime']
            del document['_id']
            del document['correctorTime']
            yield self._add_missing_fields(document, allowed_fields)
            batch_idx += 1

        self.set_previous_run(max_timestamp=self.last_processed_timestamp)

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

    def get_previous_run(self):
        return float(self.state_db.state.find_one({'key': 'last_mongodb_timestamp'}) or 0.0)

    def set_previous_run(self, max_timestamp):
        if not max_timestamp:
            return

        self.state_db.state.update(
            {'key': 'last_mongodb_timestamp'},
            {'key': 'last_mongodb_timestamp', 'value': str(max_timestamp)},
            upsert=True
        )

    def __del__(self):
        self.set_previous_run(max_timestamp=self.last_processed_timestamp)

    def handle_signal(self, signum, frame):
        self.set_previous_run(max_timestamp=self.last_processed_timestamp)
        sys.exit(1)
