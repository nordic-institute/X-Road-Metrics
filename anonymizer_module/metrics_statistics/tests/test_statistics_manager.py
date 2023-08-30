import json
import logging
import sqlite3
from datetime import datetime
from typing import Union

import pytest
from freezegun import freeze_time

from metrics_statistics.statistics_manager import collect_statistics

logger = logging.getLogger()

MOCK_CONFIG_MEMBERS = [
    {
        'class_name': 'COM',
        'description': 'Test companies'
    },
    {
        'class_name': 'GOV',
        'description': 'Test govermental entities'
    },
    {
        'class_name': 'ORG',
        'description': 'Test organizations'
    },
    {
        'class_name': 'UNUSED',
        'description': 'Just for test'
    },

]

MOCK_MEMBERS = [
    {
        'member_class': 'COM',
        'member_code': '234567-8'
    },
    {
        'member_class': 'COM',
        'member_code': '999999-1'
    },
    {
        'member_class': 'GOV',
        'member_code': '876543-2'
    },
    {
        'member_class': 'ORG',
        'member_code': ''
    },
    {
        'member_class': 'ORPHAN',
        'member_code': 'ABCD-1234'
    }
]

TEST_SETTINGS = {
    'logger': {
        'name': 'test',
        'module': 'test',
        'level': 2,
        'log-path': 'test',
        'heartbeat-path': 'test',
    },
    'xroad': {
        'instance': 'TEST',
        'central-server': {
            'host': 'test',
            'protocol': 'test',
            'timeout': 0,
        }
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
    },
    'metrics-statistics': {
    }
}


def log_factory(db_session: sqlite3.Cursor,
                request_in_dt: Union[str, datetime, None] = None, **kwargs) -> None:
    overrides: dict = {}
    overrides.update(**kwargs)
    if request_in_dt:
        if isinstance(request_in_dt, str):
            forma = '%Y-%m-%dT%H:%M:%S'
            request_in_dt = datetime.strptime(request_in_dt, forma)
        request_in_ts = int(request_in_dt.timestamp() * 1000)
        overrides.update(
            {
                'requestints': request_in_ts,
                'requestindate': request_in_dt.strftime('%Y-%m-%d')
            }
        )

    make_log(db_session, **overrides)


def make_log(db_session, **kwargs):
    defaults = {
        'id': 0,
        'requestints': 1667854800000,
        'clientmemberclass': 'ORG',
        'clientmembercode': '2908758-4',
        'clientsubsystemcode': 'MonitoringClient',
        'clientxroadinstance': 'TEST',
        'messageid': 'ce724af7-b2cf-4a3d-a60f-0979578b1434',
        'messageprotocolversion': '4.0',
        'producerdurationproducerview': '',
        'representedpartyclass': '',
        'representedpartycode': '',
        'requestattachmentcount': 0,
        'requestindate': '2022-11-07',
        'requestmimesize': 1089,
        'requestsize': 0,
        'responseattachmentcount': 2439,
        'responsemimesize': '',
        'responsesize': '2439',
        'securityservertype': 'Client',
        'servicecode': 'listMethods',
        'servicememberclass': 'ORG',
        'servicemembercode': '2908758-4',
        'servicesubsystemcode': 'Management',
        'servicetype': 'WSDL',
        'serviceversion': '',
        'servicexroadinstance': 'TEST',
        'succeeded': 'TRUE',
        'totalduration': 469
    }
    defaults.update(**kwargs)
    db_session.execute(
        """INSERT INTO LOGS(
        id, requestints, clientmemberclass, clientmembercode, clientsubsystemcode, clientxroadinstance, messageid,
        messageprotocolversion, producerdurationproducerview, representedpartyclass, representedpartycode,
       requestattachmentcount, requestindate, requestints, requestmimesize, requestsize, responseattachmentcount,
       responsemimesize, responsesize, securityservertype, servicecode, servicememberclass, servicemembercode,
        servicesubsystemcode, servicetype, serviceversion, servicexroadinstance, succeeded, totalduration
        )
        VALUES(
        :id,
        :requestints,
        :clientmemberclass,
        :clientmembercode,
        :clientsubsystemcode,
        :clientxroadinstance,
        :messageid,
        :messageprotocolversion,
        :producerdurationproducerview,
        :representedpartyclass,
        :representedpartycode,
        :requestattachmentcount,
        :requestindate,
        :requestints,
        :requestmimesize,
        :requestsize,
        :responseattachmentcount,
       :responsemimesize,
       :responsesize,
       :securityservertype,
       :servicecode,
       :servicememberclass,
       :servicemembercode,
       :servicesubsystemcode,
       :servicetype,
       :serviceversion,
       :servicexroadinstance,
       :succeeded,
       :totalduration
        )""",
        defaults
    )


class MockPsyContextManager:
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
    mocker.patch('metrics_statistics.postgresql_manager.PostgreSQL_StatisticsManager._ensure_table')
    mocker.patch('metrics_statistics.postgresql_manager.PostgreSQL_StatisticsManager._ensure_privileges')
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
        member_count json,
        service_count integer,
        service_request_count json,
        update_time timestamp);
    """)
    db_session.execute("""CREATE TABLE logs (
        id integer NOT NULL,
        clientmemberclass character varying(255),
        clientmembercode character varying(255),
        clientsubsystemcode character varying(255),
        clientxroadinstance character varying(255),
        messageid character varying(255),
        messageprotocolversion character varying(255),
        producerdurationproducerview integer,
        representedpartyclass character varying(255),
        representedpartycode character varying(255),
        requestattachmentcount integer,
        requestindate date,
        requestints bigint,
        requestmimesize bigint,
        requestsize bigint,
        responseattachmentcount integer,
        responsemimesize bigint,
        responsesize bigint,
        securityservertype character varying(255),
        servicecode character varying(255),
        servicememberclass character varying(255),
        servicemembercode character varying(255),
        servicesubsystemcode character varying(255),
        servicetype character varying(255),
        serviceversion character varying(255),
        servicexroadinstance character varying(255),
        succeeded boolean,
        totalduration integer
    );""")
    mocker.patch(
        'psycopg2.connect',
        return_value=MockPsyContextManager(MockSQLiteCursor(db_session))
    )
    yield db_session
    connection.close()


@freeze_time('2022-12-10')
def test_statistics_collector(pg, mocker):
    mocker.patch(
        'metrics_statistics.central_server_client.CentralServerClient.get_members_in_config',
        return_value=MOCK_CONFIG_MEMBERS
    )
    mocker.patch(
        'metrics_statistics.central_server_client.CentralServerClient.get_members',
        return_value=MOCK_MEMBERS
    )
    make_log(pg, servicesubsystemcode='TestSerive1')
    make_log(pg, servicesubsystemcode='TestSerive1')
    make_log(pg, servicesubsystemcode='TestSerive2')
    make_log(pg, servicesubsystemcode='TestSerive3')
    make_log(pg, servicesubsystemcode='TestSerive4')
    make_log(pg, servicesubsystemcode='TestSerive5')

    mock_time_range_requests_counts = {
        'current_month_request_count': 100,
        'current_year_request_count': 2000,
        'previous_month_request_count': 1111,
        'previous_year_request_count': 4000,
        'today_request_count': 10,
        'total_request_count': 100000,
    }
    mocker.patch(
        'metrics_statistics.mongodb_manager.DatabaseManager.get_requests_counts',
        return_value=mock_time_range_requests_counts
    )
    mock_services_requests_counts = [{
        'service_testservice1': [{'count': 10}],
        'service_testservice2': [{'count': 8}],
        'service_testservice3': [{'count': 25}],
        'service_testservice4': [{'count': 3}],
        'service_testservice5': [{'count': 1}],
    }]
    mocker.patch(
        'metrics_statistics.mongodb_manager.DatabaseManager._get_db_service_request_counts',
        return_value=mock_services_requests_counts
    )
    TEST_SETTINGS['metrics-statistics']['num-max-services-requests'] = 3

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
        'member_count': json.dumps([
            {'class_name': 'COM', 'description': 'Test companies', 'count': 2},
            {'class_name': 'GOV', 'description': 'Test govermental entities', 'count': 1},
            {'class_name': 'ORG', 'description': 'Test organizations', 'count': 0},
            {'class_name': 'UNUSED', 'description': 'Just for test', 'count': 0}]),
        'service_count': 5,
        'service_request_count': '{"service_testservice3": 25, "service_testservice1": 10, "service_testservice2": 8}',
        'update_time': '2022-12-10 00:00:00'
    }
