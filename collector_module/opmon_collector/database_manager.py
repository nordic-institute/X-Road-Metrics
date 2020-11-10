""" Database Manager - Collector Module
"""

import time
import pymongo


class DatabaseManager:

    def __init__(self, mongo_settings, xroad_instance, logger_manager):
        self.mongo_uri = \
            f"mongodb://{mongo_settings['user']}:{mongo_settings['password']}@{mongo_settings['host']}/auth_db"
        self.db_name = f'query_db_{xroad_instance}'
        self.db_collector_state = f'collector_state_{xroad_instance}'
        self.collector_id = f'collector_{xroad_instance}'
        self.logger_m = logger_manager

    @staticmethod
    def get_timestamp():
        return float(time.time())

    def save_server_list_to_database(self, server_list):
        try:
            client = pymongo.MongoClient(self.mongo_uri)
            db = client[self.db_collector_state]
            collection = db['server_list']
            data = dict()
            data['timestamp'] = self.get_timestamp()
            data['server_list'] = server_list
            data['collector_id'] = self.collector_id
            collection.insert(data)
        except Exception as e:
            self.logger_m.log_error('ServerManager.get_server_list_database', '{0}'.format(repr(e)))
            raise e

    def get_server_list_from_database(self):
        """
        Get the most recent server list from MongoDB
        """
        try:
            client = pymongo.MongoClient(self.mongo_uri)
            db = client[self.db_collector_state]
            data = db['server_list'].find({'collector_id': self.collector_id}).sort([('timestamp', -1)]).limit(1)[0]
            return data['server_list'], data['timestamp']
        except Exception as e:
            self.logger_m.log_error('ServerManager.get_server_list_database', '{0}'.format(repr(e)))
            raise e

    def get_next_records_timestamp(self, server_key, records_from_offset):
        """ Returns next records_from pointer for the given server
        """
        try:
            client = pymongo.MongoClient(self.mongo_uri)
            db = client[self.db_collector_state]
            collection = db['collector_pointer']
            cur = collection.find_one({'server': server_key})
            if cur is None:
                # If server not in MongoDB
                data = dict()
                data['server'] = server_key
                data['records_from'] = self.get_timestamp() - records_from_offset
                collection.insert(data)
            else:
                data = cur
            # Return pointers
            records_from = data['records_from']
        except Exception as e:
            self.logger_m.log_error('ServerManager.get_next_records_timestamp', '{0}'.format(repr(e)))
            raise e
        return records_from

    def set_next_records_timestamp(self, server_key, records_from):
        try:
            client = pymongo.MongoClient(self.mongo_uri)
            db = client[self.db_collector_state]
            collection = db['collector_pointer']
            data = dict()
            data['server'] = server_key
            data['records_from'] = records_from
            collection.find_and_modify(query={'server': server_key},
                                       update=data, upsert=True)
        except Exception as e:
            self.logger_m.log_error('ServerManager.set_next_records_timestamp', '{0}'.format(repr(e)))
            raise e

    def insert_data_to_raw_messages(self, data_list):
        try:
            client = pymongo.MongoClient(self.mongo_uri)
            db = client[self.db_name]
            raw_msg = db['raw_messages']
            # Add timestamp to data list
            for data in data_list:
                timestamp = self.get_timestamp()
                data['insertTime'] = timestamp
            # Save all
            raw_msg.insert_many(data_list)
        except Exception as e:
            self.logger_m.log_error('ServerManager.insert_data_to_raw_messages', '{0}'.format(repr(e)))
            raise e
