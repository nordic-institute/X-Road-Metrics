import logging
import sqlite3
from datetime import datetime

import pytest
from freezegun import freeze_time

from metrics_statistics.statistics_manager import collect_statistics

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
        'database-name': 'test',
        'readonly-users': []
    },
    'mongodb': {
        'user': 'test-user',
        'password': 'test-password',
        'host': 'test host'
    }
}


class MockPsyContextManager(object):
    def __init__(self, mock_cursor):
        self._mock_cursor = mock_cursor

    def __enter__(self):
        return self

    def cursor(self):
        return self._mock_cursor

    def __exit__(self, _, __, ___):
        pass


class MockSQLiteCursor(object):
    def __init__(self, sql_session):
        self._sql_session = sql_session

    def execute(self, *args, **kwargs):
        return self._sql_session.execute(*args, **kwargs)

    def mogrify(self, sql, parameters):
        # SQlite does not support LIMIT NULL or OFFSET NULL
        new_parameters = []
        for parameter in parameters:
            if isinstance(parameter, datetime):
                new_parameters.append(parameter.strftime('%Y-%m-%d %H:%M:%S'))
            else:
                new_parameters.append(parameter)

        if len(new_parameters) == 1 and new_parameters[0] is None:
            if 'LIMIT' in sql:
                # disable limiting, get all records
                new_parameters = ('10000000',)
            if 'OFFSET' in sql:
                # disable offset, get all range of records
                new_parameters = ('0',)
        formatted_parameters = ','.join([f"'{param}'" if isinstance(param, str) else str(param) for param in new_parameters])
        return f'({formatted_parameters})'.encode('utf-8')

    def fetchall(self, *args, **kwargs):
        return self._sql_session.fetchall(*args, **kwargs)

    def fetchone(self, *args, **kwargs):
        return self._sql_session.fetchone(*args, **kwargs)


@pytest.fixture
def pg(mocker):
    mocker.patch('metrics_statistics.postgresql_manager.PostgreSqlManager._ensure_table')
    mocker.patch('metrics_statistics.postgresql_manager.PostgreSqlManager._ensure_privileges')
    connection = sqlite3.connect(':memory:', detect_types=sqlite3.PARSE_COLNAMES)
    db_session = connection.cursor()
    db_session.row_factory = sqlite3.Row
    db_session.execute("""
        CREATE TABLE metrics_statistics (
        -- id SERIAL PRIMARY KEY, not supported in SQLite3
        id INTEGER PRIMARY KEY AUTOINCREMENT, -- this is equivalent for SQLite3
        current_month_request_count integer,
        current_year_request_count integer,
        previous_month_request_count integer,
        previous_year_request_count integer,
        today_request_count integer,
        total_request_count integer,
        update_time timestamp);
    """)
    mocker.patch(
        'psycopg2.connect',
        return_value=MockPsyContextManager(MockSQLiteCursor(db_session))
    )
    yield db_session
    connection.close()


@freeze_time('2022-12-10')
def test_statistics_collector(pg, mocker):
    mock_statistics = {
        'current_month_request_count': 100,
        'current_year_request_count': 2000,
        'previous_month_request_count': 1111,
        'previous_year_request_count': 4000,
        'today_request_count': 10,
        'total_request_count': 100000,
    }
    mocker.patch(
        'metrics_statistics.mongodb_manager.DatabaseManager.get_requests_counts',
        return_value=mock_statistics
    )
    collect_statistics(TEST_SETTINGS, logger)
    cursor = pg.execute('SELECT * FROM metrics_statistics')
    rows = cursor.fetchall()
    assert len(rows) == 1
    expected_data = dict(rows[0])
    assert expected_data == {
        'id': 1,
        'current_month_request_count': 100,
        'current_year_request_count': 2000,
        'previous_month_request_count': 1111,
        'previous_year_request_count': 4000,
        'today_request_count': 10,
        'total_request_count': 100000,
        'update_time': '2022-12-10 00:00:00'
    }
