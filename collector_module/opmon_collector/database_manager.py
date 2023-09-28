""" Database Manager - Collector Module
"""

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

import time
import urllib.parse
import pymongo
from pymongo import ReturnDocument


class DatabaseManager:

    def __init__(self, mongo_settings, xroad_instance, logger_manager):
        self.mongo_uri = self.get_mongo_uri(mongo_settings)
        self.db_name = f'query_db_{xroad_instance}'
        self.db_collector_state = f'collector_state_{xroad_instance}'
        self.collector_id = f'collector_{xroad_instance}'
        self.logger_m = logger_manager
        self.connect_args = {
            'tls': bool(mongo_settings.get('tls')),
            'tlsCAFile': mongo_settings.get('tls-ca-file'),
        }

    @staticmethod
    def get_mongo_uri(mongo_settings):
        user = mongo_settings['user']
        password = urllib.parse.quote(mongo_settings['password'], safe='')
        host = mongo_settings['host']
        return f"mongodb://{user}:{password}@{host}/auth_db"

    @staticmethod
    def get_timestamp():
        return float(time.time())

    def save_server_list_to_database(self, server_list):
        try:
            client = pymongo.MongoClient(self.mongo_uri, **self.connect_args)
            db = client[self.db_collector_state]
            collection = db['server_list']
            data = dict()
            data['timestamp'] = self.get_timestamp()
            data['server_list'] = server_list
            data['collector_id'] = self.collector_id
            collection.insert_one(data)
        except Exception as e:
            self.logger_m.log_exception('ServerManager.get_server_list_database', repr(e))
            raise e

    def get_server_list_from_database(self):
        """
        Get the most recent server list from MongoDB
        """
        try:
            client = pymongo.MongoClient(self.mongo_uri, **self.connect_args)
            db = client[self.db_collector_state]
            data = db['server_list'].find({'collector_id': self.collector_id}).sort([('timestamp', -1)]).limit(1)[0]
            return data['server_list'], data['timestamp']
        except Exception as e:
            self.logger_m.log_exception('ServerManager.get_server_list_database', repr(e))
            raise e

    def get_next_records_timestamp(self, server_key, records_from_offset):
        """ Returns next records_from pointer for the given server
        """
        try:
            client = pymongo.MongoClient(self.mongo_uri, **self.connect_args)
            db = client[self.db_collector_state]
            collection = db['collector_pointer']
            cur = collection.find_one({'server': server_key})
            if cur is None:
                # If server not in MongoDB
                data = dict()
                data['server'] = server_key
                data['records_from'] = self.get_timestamp() - records_from_offset
                collection.insert_one(data)
            else:
                data = cur
            # Return pointers
            records_from = data['records_from']
        except Exception as e:
            self.logger_m.log_exception('ServerManager.get_next_records_timestamp', repr(e))
            raise e
        return records_from

    def set_next_records_timestamp(self, server_key, records_from):
        try:
            client = pymongo.MongoClient(self.mongo_uri, **self.connect_args)
            db = client[self.db_collector_state]
            collection = db['collector_pointer']

            update_operations = {'$set': {
                'server': server_key,
                'records_from': records_from
            }}

            if collection.find_one_and_update(
                    {'server': server_key},
                    update_operations,
                    return_document=ReturnDocument.AFTER,
                    upsert=True
            ) is None:
                raise IndexError(f"Document not found. MongoDb collection {str(collection)}, server key {server_key}.")

        except Exception as e:
            self.logger_m.log_exception('ServerManager.set_next_records_timestamp', repr(e))
            raise e

    def insert_data_to_raw_messages(self, data_list):
        try:
            client = pymongo.MongoClient(self.mongo_uri, **self.connect_args)
            db = client[self.db_name]
            raw_msg = db['raw_messages']
            # Add timestamp to data list
            for data in data_list:
                timestamp = self.get_timestamp()
                data['insertTime'] = timestamp
            # Save all
            raw_msg.insert_many(data_list)
        except Exception as e:
            self.logger_m.log_exception('ServerManager.insert_data_to_raw_messages', repr(e))
            raise e
