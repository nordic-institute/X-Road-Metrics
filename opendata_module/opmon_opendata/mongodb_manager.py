""" MongoDB Manager - Opendata Module"""

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

import logging
import urllib.parse
from datetime import datetime, timedelta
from typing import Mapping, Optional, TypedDict

from pymongo import MongoClient


class StatisticsDataNotFoundError(Exception):
    pass


class DatabaseManager:

    def __init__(self, mongo_settings: dict,
                 xroad_instance: str, logger: logging.Logger) -> None:
        self.mongo_uri = self.get_mongo_uri(mongo_settings)
        self.db_name = f'query_db_{xroad_instance}'
        self.logger = logger
        self.connect_args: dict = {
            'tls': bool(mongo_settings.get('tls')),
            'tlsCAFile': mongo_settings.get('tls-ca-file'),
        }

    @staticmethod
    def get_mongo_uri(mongo_settings: dict) -> str:
        user = mongo_settings['user']
        password = urllib.parse.quote(mongo_settings['password'], safe='')
        host = mongo_settings['host']
        return f'mongodb://{user}:{password}@{host}/auth_db'

    def get_statistics_data(self):
        client = MongoClient(self.mongo_uri, **self.connect_args)
        db = client[self.db_name]
        result = db.metrics_statistics.find_one({})
        if not result:
            raise StatisticsDataNotFoundError('Statistics data was not found in database')

        statistical_data = {
            'current_month_request_count': result['currentMonthRequestCount'],
            'current_year_request_count': result['currentYearRequestCount'],
            'previous_month_request_count': result['previousMonthRequestCount'],
            'previous_year_request_count': result['previousYearRequestCount'],
            'today_request_count': result['todayRequestCount'],
            'total_request_count': result['totalRequestCount'],
            'update_time': result['updateTime'],
        }

        return statistical_data
