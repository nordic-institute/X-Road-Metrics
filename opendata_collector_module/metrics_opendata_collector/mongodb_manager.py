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
from typing import List, Optional

from pymongo import MongoClient


class MongoDbManager:
    """
    A class for managing MongoDB connections and operations.

    Args:
        settings (dict): A dictionary containing MongoDB and X-Road instance settings.
        instance_id (str): A unique identifier for the OpenData instance.
    """

    def __init__(self, settings: dict, instance_id: str) -> None:
        self.settings = settings
        self.instance_id = instance_id
        xroad = settings['xroad']['instance']

        connect_args = {
            'tls': bool(settings['mongodb'].get('tls')),
            'tlsCAFile': settings['mongodb'].get('tls-ca-file'),
        }
        self.client = MongoClient(self.get_mongo_uri(settings), **connect_args)
        self.query_db = self.client[f'query_db_{xroad}']
        self.state_db = self.client[f'opendata_collector_state_{xroad}']

    @staticmethod
    def get_mongo_uri(settings: dict) -> str:
        user = settings['mongodb']['user']
        password = urllib.parse.quote(settings['mongodb']['password'], safe='')
        host = settings['mongodb']['host']
        return f'mongodb://{user}:{password}@{host}/auth_db'

    def insert_documents(self, documents: List[dict]) -> None:
        for document in documents:
            document['insertTime'] = MongoDbManager.get_timestamp()
        self.query_db.opendata_data.insert_many(documents)

    def get_last_inserted_entry(self) -> Optional[dict]:
        state = self.state_db.state.find_one({'instance_id': self.instance_id}) or {}
        return {
            'last_inserted_requestints': state['last_inserted_requestints'],
            'last_inserted_row_id': state['last_inserted_row_id']
        } if state else None

    def set_last_inserted_entry(self, document: dict) -> None:
        self.state_db.state.update_one(
            {'instance_id': self.instance_id},
            {
                '$set': {
                    'last_inserted_requestints': document['requestInTs'],
                    'last_inserted_row_id': document['id']
                }
            },
            upsert=True
        )

    @staticmethod
    def get_timestamp():
        """
        Returns current timestamp.
        :return: Returns current timestamp.
        """
        return float(time.time())
