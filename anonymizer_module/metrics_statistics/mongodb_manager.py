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
from typing import Any, Dict, List, Mapping, Optional, Sequence, TypedDict

from pymongo import MongoClient
from pymongo.command_cursor import CommandCursor

# All ts in metrics are in milliseconds.
METRICS_TS_MULTIPLIER = 1000


def metrics_ts(dt: datetime) -> float:
    return dt.timestamp() * METRICS_TS_MULTIPLIER


class RequestsCountData(TypedDict):
    total_request_count: int
    previous_year_request_count: int
    current_year_request_count: int
    previous_month_request_count: int
    current_month_request_count: int
    today_request_count: int
    update_time: Optional[datetime]


class RequestCountDateTimeRange(TypedDict):
    total_request_count: None
    previous_year_request_count: 'DateTimeRange'
    current_year_request_count: 'DateTimeRange'
    previous_month_request_count: 'DateTimeRange'
    current_month_request_count: 'DateTimeRange'
    today_request_count: 'DateTimeRange'


class ServiceRequestCount(TypedDict):
    title: str
    count: int


class DateTimeRange:
    def __init__(self, from_dt: datetime, to_dt: Optional[datetime] = None) -> None:
        """
            Represents a range of datetime values.

            Parameters:
                from_ (datetime): The starting datetime of the range.
                to_ (datetime, optional): The ending datetime of the range. Defaults to None.
        """
        self.from_dt = from_dt
        self.to_dt = to_dt

    def from_ts(self) -> float:
        return metrics_ts(self.from_dt)

    def to_ts(self) -> float:
        if not self.to_dt:
            self.to_dt = datetime.now()
        return metrics_ts(self.to_dt)


class DateTimeRangeManager:

    @staticmethod
    def get_prev_year_range() -> DateTimeRange:
        prev = datetime.now() - timedelta(days=365)
        prev_year_start = datetime(prev.year, 1, 1, 0, 0, 0)
        prev_year_end = datetime(prev.year, 12, 31, 23, 59, 59)
        return DateTimeRange(prev_year_start, prev_year_end)

    @staticmethod
    def get_curr_year_range() -> DateTimeRange:
        curr_year = datetime.now()
        curr_year_start = datetime(curr_year.year, 1, 1, 0, 0, 0)
        return DateTimeRange(curr_year_start)

    @staticmethod
    def get_prev_month_range() -> DateTimeRange:
        now = datetime.now()
        # Get previous month
        first_curr_month_day = now.replace(day=1)
        last_prev_month_day_dt = first_curr_month_day - timedelta(days=1)

        prev_month_start_dt = datetime(last_prev_month_day_dt.year,
                                       last_prev_month_day_dt.month, 1, 0, 0, 0)
        prev_month_end_dt = datetime(last_prev_month_day_dt.year,
                                     last_prev_month_day_dt.month,
                                     last_prev_month_day_dt.day, 23, 59, 59)
        return DateTimeRange(prev_month_start_dt, prev_month_end_dt)

    @staticmethod
    def get_curr_month_range() -> DateTimeRange:
        now = datetime.now()
        curr_month_start = datetime(now.year, now.month, 1, 0, 0, 0)
        return DateTimeRange(curr_month_start)

    @staticmethod
    def get_today_range() -> DateTimeRange:
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day, 0, 0, 0)
        return DateTimeRange(today_start)


class DatabaseManager:

    def __init__(self, mongo_settings: Dict[str, str],
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

    @staticmethod
    def generate_pipeline() -> List[Mapping[str, Any]]:

        """
        Generate a MongoDB aggregation pipeline for generating facets based on time ranges.

        Returns:
            A list of dictionary objects representing the MongoDB aggregation pipeline.
        """

        requests_counts_time_ranges: RequestCountDateTimeRange = {
            'total_request_count': None,
            'previous_year_request_count': DateTimeRangeManager().get_prev_year_range(),
            'current_year_request_count': DateTimeRangeManager().get_curr_year_range(),
            'previous_month_request_count': DateTimeRangeManager().get_prev_month_range(),
            'current_month_request_count': DateTimeRangeManager().get_curr_month_range(),
            'today_request_count': DateTimeRangeManager().get_today_range()
        }

        def generate_facet(range: Optional[DateTimeRange] = None) -> List[Optional[Dict[str, Any]]]:
            """
            Generate individual facet stages for a given time range.

            Args:
                range: DateTimeRange object representing the time range to filter data.

            Returns:
                List of dictionaries representing the facet stages for the given time range.
            """
            facet = [
                {
                    '$match': {
                        'client.requestInTs':
                            {
                                '$gte': range.from_ts(),
                                '$lte': range.to_ts(),
                            }
                    }
                } if range else None,
                {
                    '$group': {'_id': '$_id'}
                },
                {
                    '$group': {'_id': 1, 'count': {'$sum': 1}}
                }
            ]
            return [facet_item for facet_item in facet if facet_item is not None]
        return [
            {
                '$facet': {
                    key: generate_facet(value)
                    for key, value in requests_counts_time_ranges.items()
                    if isinstance(value, DateTimeRange) or value is None
                }
            }
        ]

    def get_requests_counts(self) -> RequestsCountData:
        """
        Retrieves the counts of requests based on different time ranges.

        Returns:
            A dictionary containing the counts of requests for different time ranges.
            The keys in the dictionary represent the time ranges, and the values represent the corresponding request counts.
        """
        client: MongoClient = MongoClient(self.mongo_uri, **dict(self.connect_args))
        db = client[self.db_name]
        collection = db['clean_data']

        pipeline = DatabaseManager.generate_pipeline()
        result = collection.aggregate(pipeline)

        rows = [row for row in result]
        request_counts_raw = {
            key: value[0]['count']
            if value else 0
            for key, value in rows[0].items()
        }
        requests_counts: RequestsCountData = {
            'today_request_count': request_counts_raw['today_request_count'],
            'current_month_request_count': request_counts_raw['current_month_request_count'],
            'previous_month_request_count': request_counts_raw['previous_month_request_count'],
            'current_year_request_count': request_counts_raw['current_year_request_count'],
            'previous_year_request_count': request_counts_raw['previous_year_request_count'],
            'total_request_count': request_counts_raw['total_request_count'],
            'update_time': None
        }

        return requests_counts

    def get_services_counts(self, services: List[str],
                            max_services_by_requests: Optional[int] = None) -> Sequence[ServiceRequestCount]:
        service_count_data = []
        result = self._get_db_service_request_counts(services)
        rows = [row for row in result]
        service_count = {
            key: value[0]['count']
            if value else 0
            for key, value in rows[0].items()
        }
        # sort dict by max counts
        sorted_counts = sorted(service_count.items(), key=lambda x: x[1], reverse=True)

        # get top services by max_services_by_requests
        if max_services_by_requests and len(sorted_counts) > max_services_by_requests:
            sorted_counts = sorted_counts[:max_services_by_requests]

        service_count = dict(sorted_counts)
        service_key_map = self._get_service_key_map(services)

        for service_key, title in service_key_map.items():
            if not service_count.get(service_key):
                continue
            service_count_data.append(
                ServiceRequestCount(
                    title=title,
                    count=service_count[service_key]
                )
            )
        return service_count_data

    @staticmethod
    def _get_service_key_map(services: List[str]) -> Dict[str, str]:
        return {
            f'service_{service.strip().replace(" ","_").lower()}': service
            for service in services
        }

    def _get_db_service_request_counts(self, services: List[str]) -> CommandCursor:
        client: MongoClient = MongoClient(self.mongo_uri, **dict(self.connect_args))
        db = client[self.db_name]
        collection = db['clean_data']
        pipeline = self.generate_services_count_pipeline(services)
        result = collection.aggregate(pipeline)
        return result

    def generate_services_count_pipeline(self, services) -> List[Mapping[str, Any]]:
        service_key_map = self._get_service_key_map(services)

        def generate_facet(service: str) -> List[Dict[str, Any]]:
            facet = [
                {
                    '$match': {
                        'client.serviceSubsystemCode': service,
                    }
                },
                {
                    '$group': {'_id': '$_id'}
                },
                {
                    '$group': {'_id': 1, 'count': {'$sum': 1}}
                }
            ]
            return [facet_item for facet_item in facet if isinstance(facet_item, dict)]
        return [
            {
                '$facet': {
                    key: generate_facet(value)
                    for key, value in service_key_map.items()
                }
            }
        ]
