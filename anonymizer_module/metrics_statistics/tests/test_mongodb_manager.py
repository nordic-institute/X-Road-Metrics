import logging
from datetime import datetime

import pytest
from freezegun import freeze_time

from metrics_statistics.mongodb_manager import DatabaseManager, metrics_ts

logger = logging.getLogger()

TEST_SETTINGS = {
    'logger': {
        'name': 'test',
        'module': 'test',
        'level': 2,
        'log-path': 'test',
        'heartbeat-path': 'test',
    },
    'xroad': {
        'instance': 'TEST'
    },
    'postgres': {
        'table-name': 'logs',
        'host': 'test',
        'database-name': 'test'
    },
    'mongodb': {
        'user': 'test-user',
        'password': 'test-password',
        'host': 'test host'
    }
}


class MockCollection:
    def __init__(self):
        self._storage = []

    def insert_one(self, document):
        self._storage.append(document)

    def _find(self, query):
        return [
            item for item in self._storage
            if all(
                query_item in item.items()
                for query_item
                in query.items()
            )
        ]

    def find_one(self, query: None):
        if query:
            result = self._find(query)
        else:
            result = self._storage
        try:
            return result[0]
        except IndexError:
            return None

    def get_all(self):
        return self._storage

    def update_one(self, query, update, upsert=False):
        entry_to_upsert = {}
        found = self.find_one(query)
        if found:
            entry_to_upsert.update(found)
            if upsert:
                self._storage.remove(found)

        else:
            entry_to_upsert.update(query)

        entry_to_upsert.update(update['$set'])
        self._storage.append(entry_to_upsert)


@pytest.fixture
def mock_mongo_db(mocker):
    mock_client = mocker.MagicMock()
    db_mock = mocker.MagicMock()

    db_mock.metrics_statistics = MockCollection()

    mock_client.__getitem__.return_value = db_mock
    mocker.patch(
        'metrics_statistics.mongodb_manager.MongoClient',
        return_value=mock_client
    )
    yield db_mock


@freeze_time('2012-01-14 12:00:00')
def test_update_statistics(mock_mongo_db):
    db_manager = DatabaseManager(TEST_SETTINGS['mongodb'], 'TEST', logger)
    data_to_update = {
        'today_request_count': 10,
        'current_month_request_count': 333,
        'previous_month_request_count': 732,
        'current_year_request_count': 500,
        'previous_year_request_count': 500,
        'total_request_count': 1000,
    }
    db_manager.update_statistics(data_to_update)
    upserted_data = mock_mongo_db.metrics_statistics.get_all()
    assert upserted_data == [
        {
            'todayRequestCount': 10,
            'currentMonthRequestCount': 333,
            'previousMonthRequestCount': 732,
            'currentYearRequestCount': 500,
            'previousYearRequestCount': 500,
            'totalRequestCount': 1000,
            'updateTime': metrics_ts(datetime(2012, 1, 14, 12, 0, 0))
        }
    ]


@freeze_time('2012-01-14 12:00:00')
def test_generate_pipeline():
    pipeline = DatabaseManager.generate_pipeline()
    assert pipeline == [
        {
            '$facet': {
                'total_request_count': [
                    {
                        '$group': {'_id': '$_id'}
                    },
                    {
                        '$group': {'_id': 1, 'count': {'$sum': 1}}
                    }
                ],
                'previous_year_request_count': [
                    {
                        '$match': {
                            'client.requestInTs': {
                                '$gte': metrics_ts(datetime(2011, 1, 1, 0, 0, 0)),
                                '$lte': metrics_ts(datetime(2011, 12, 31, 23, 59, 59))
                            }
                        }
                    },
                    {
                        '$group': {'_id': '$_id'}},
                    {
                        '$group': {'_id': 1, 'count': {'$sum': 1}}
                    }
                ],
                'current_year_request_count': [
                    {
                        '$match': {
                            'client.requestInTs': {
                                '$gte': metrics_ts(datetime(2012, 1, 1, 0, 0, 0)),
                                '$lte': metrics_ts(datetime(2012, 1, 14, 12, 0, 0, 0))  # now
                            }
                        }
                    },
                    {
                        '$group': {'_id': '$_id'}},
                    {
                        '$group': {'_id': 1, 'count': {'$sum': 1}}
                    }
                ],
                'previous_month_request_count': [
                    {
                        '$match': {
                            'client.requestInTs': {
                                '$gte': metrics_ts(datetime(2011, 12, 1, 0, 0, 0)),
                                '$lte': metrics_ts(datetime(2011, 12, 31, 23, 59, 59))
                            }
                        }
                    },
                    {
                        '$group': {'_id': '$_id'}},
                    {
                        '$group': {'_id': 1, 'count': {'$sum': 1}}
                    }
                ],
                'current_month_request_count': [
                    {
                        '$match': {
                            'client.requestInTs': {
                                '$gte': metrics_ts(datetime(2012, 1, 1, 0, 0, 0)),
                                '$lte': metrics_ts(datetime(2012, 1, 14, 12, 0, 0))  # now
                            }
                        }
                    },
                    {
                        '$group': {'_id': '$_id'}},
                    {
                        '$group': {'_id': 1, 'count': {'$sum': 1}}
                    }
                ],
                'today_request_count': [
                    {
                        '$match': {
                            'client.requestInTs': {
                                '$gte': metrics_ts(datetime(2012, 1, 14, 0, 0, 0)),
                                '$lte': metrics_ts(datetime(2012, 1, 14, 12, 0, 0))  # now
                            }
                        }
                    },
                    {
                        '$group': {'_id': '$_id'}},
                    {
                        '$group': {'_id': 1, 'count': {'$sum': 1}}
                    }
                ]
            }
        }
    ]
