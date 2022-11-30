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

import urllib.parse
import pymongo


class MongoDBHandler:
    """ Reports MongoDB Handler
    """

    def __init__(self, mongo_settings, xroad_instance):
        self.db_name = f'query_db_{xroad_instance}'
        self.db_reports_state_name = f'reports_state_{xroad_instance}'

        self.user = mongo_settings['user']
        pwd = urllib.parse.quote(mongo_settings['password'], safe='')
        server = mongo_settings['host']
        self.uri = f"mongodb://{self.user}:{pwd}@{server}/auth_db"
        self.connect_args = {
            'tls': bool(mongo_settings.get('tls')),
            'tlsCAFile': mongo_settings.get('tls-ca-file'),
        }

    def get_query_db(self):
        client = pymongo.MongoClient(self.uri, **self.connect_args)
        db = client[self.db_name]
        return db

    def get_reports_state_db(self):
        client = pymongo.MongoClient(self.uri, **self.connect_args)
        db = client[self.db_reports_state_name]
        return db
