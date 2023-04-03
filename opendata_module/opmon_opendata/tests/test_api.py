import datetime
import json
import os
import pathlib
import random
import sqlite3
from logging import StreamHandler

import pytest
from django.test import Client
from freezegun import freeze_time


COLUMNS = [
    'clientmemberclass',
    'clientmembercode',
    'clientsubsystemcode',
    'clientxroadinstance',
    'messageid',
    'messageprotocolversion',
    'producerdurationproducerview',
    'representedpartyclass',
    'representedpartycode',
    'requestattachmentcount',
    'requestints',
    'requestindate',
    'requestmimesize',
    'responseattachmentcount',
    'requestsize',
    'responsemimesize',
    'responsesize',
    'securityservertype',
    'servicecode',
    'servicememberclass',
    'servicemembercode',
    'servicesubsystemcode',
    'servicetype',
    'serviceversion',
    'servicexroadinstance',
    'succeeded',
    'totalduration',
]
COLUMNS_AND_TYPES = [(column, '_') for column in COLUMNS]


class MockSQLiteCursor(object):
    def __init__(self, sql_session):
        self._sql_session = sql_session

    def execute(self, *args, **kwargs):
        return self._sql_session.execute(*args, **kwargs)

    def mogrify(self, sql, parameters):
        # SQlite does not support LIMIT NULL or OFFSET NULL
        if len(parameters) == 1 and parameters[0] is None:
            if 'LIMIT' in sql:
                # disable limiting, get all records
                parameters = ('10000000',)
            if 'OFFSET' in sql:
                # disable offset, get all range of records
                parameters = ('0',)
        return (sql % parameters).encode('utf-8')

    def fetchall(self, *args, **kwargs):
        return self._sql_session.fetchall(*args, **kwargs)


class MockPsyContextManager(object):
    def __init__(self, mock_cursor):
        self._mock_cursor = mock_cursor

    def __enter__(self):
        return self

    def cursor(self):
        return self._mock_cursor

    def __exit__(self, _, __, ___):
        pass


@pytest.fixture(autouse=True)
def settings(mocker):
    settings = {
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
        'opendata': {
            'field-descriptions': {
            },
            'delay-days': 1
        }
    }
    mocker.patch('opmon_opendata.api.views.get_settings', return_value=settings)


@pytest.fixture
def set_dir():
    os.chdir(pathlib.Path(__file__).parent.absolute())


@pytest.fixture(autouse=True)
def mock_logger_manager(mocker):
    mocker.patch('opmon_opendata.logger_manager.LoggerManager._create_file_handler', return_value=StreamHandler())
    yield mocker.Mock()


@pytest.fixture
def http_client():
    yield Client()


@pytest.fixture
def db(mocker):
    mocker.patch(
        'opmon_opendata.api.postgresql_manager.PostgreSQL_Manager.get_column_names_and_types',
        return_value=COLUMNS_AND_TYPES
    )
    connection = sqlite3.connect(':memory:')
    db_session = connection.cursor()
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
    connection.commit()
    mocker.patch(
        'psycopg2.connect',
        return_value=MockPsyContextManager(MockSQLiteCursor(db_session))
    )
    yield db_session
    connection.close()


def test_get_harvest_from(db, http_client, caplog):
    now = datetime.datetime.now()

    log_factory(db, request_in_dt='2022-11-07T07:50:00')

    # happy logs
    log_factory(db, request_in_dt='2022-11-07T08:00:00')
    log_factory(db, request_in_dt=now)

    data = {
        'from_dt': '2022-11-07T08:00:00',
    }
    response = http_client.get('/api/harvest', data)
    assert response.status_code == 200
    response_data = response.json()
    data = response_data.get('data')
    assert len(data) == 2
    assert 'api_get_harvest_response_success' in caplog.text
    assert 'returning 2 rows' in caplog.text


@pytest.mark.parametrize('from_dt,expected_columns, has_data', [
    ('2011-11-07T08:00:00', COLUMNS, True),
    ('2023-01-07T08:00:00', [], False)
])
def test_get_harvest_columns(db, http_client, from_dt, expected_columns, has_data):
    # Do not return columns for empty data
    log_factory(db, request_in_dt='2022-11-07T08:00:00')
    data = {
        'from_dt': from_dt,
    }
    response = http_client.get('/api/harvest', data)
    assert response.status_code == 200
    response_data = response.json()
    assert bool(response_data['data']) == has_data
    assert response_data['columns'] == expected_columns


def test_get_harvest_from_until(db, http_client):
    log_factory(db, request_in_dt='2022-11-07T07:50:00')

    # happy logs
    log_factory(db, request_in_dt='2022-11-07T08:00:00')
    log_factory(db, request_in_dt='2022-11-07T08:20:00')
    log_factory(db, request_in_dt='2022-11-07T08:47:00')

    log_factory(db, request_in_dt='2022-11-07T09:00:00')
    log_factory(db, request_in_dt='2022-11-07T09:15:00')

    query = {
        'from_dt': '2022-11-07T08:00:00',
        'until_dt': '2022-11-07T09:00:00',
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 200
    response_data = response.json()
    data = response_data.get('data')
    assert len(data) == 3


def test_get_harvest_from_with_limit(db, http_client):
    log_factory(db, request_in_dt='2022-11-10T08:00:00')
    log_factory(db, request_in_dt='2022-11-08T08:20:00')
    log_factory(db, request_in_dt='2022-11-05T08:47:00')
    log_factory(db, request_in_dt='2022-11-09T09:30:00')
    log_factory(db, request_in_dt='2022-11-07T10:34:00')

    query = {
        'from_dt': '2022-11-05T08:00:00',
        'limit': 4
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 200
    response_data = response.json()
    data = response_data.get('data')
    assert len(data) == 4
    actual_request_in_dates = [row[11] for row in data]
    assert actual_request_in_dates == [
        '2022-11-05',
        '2022-11-07',
        '2022-11-08',
        '2022-11-09'
    ]


def test_get_harvest_from_with_limit_offset(db, http_client):
    log_factory(db, request_in_dt='2022-11-10T08:00:00')
    log_factory(db, request_in_dt='2022-11-08T08:20:00')
    log_factory(db, request_in_dt='2022-11-05T08:47:00')
    log_factory(db, request_in_dt='2022-11-09T09:30:00')
    log_factory(db, request_in_dt='2022-11-07T10:34:00')

    query = {
        'from_dt': '2022-11-05T07:00:00',
        'limit': 4,
        'offset': 2
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 200
    response_data = response.json()
    data = response_data.get('data')
    assert len(data) == 3
    actual_request_in_dates = [row[11] for row in data]
    assert actual_request_in_dates == [
        '2022-11-08',
        '2022-11-09',
        '2022-11-10'
    ]


def test_get_harvest_default_ordering(db, http_client):
    log_factory(db, request_in_dt='2022-11-15T10:34:00')
    log_factory(db, request_in_dt='2022-11-12T08:00:00')
    log_factory(db, request_in_dt='2022-11-07T09:30:00')
    log_factory(db, request_in_dt='2022-11-14T08:47:00')
    log_factory(db, request_in_dt='2022-11-13T08:20:00')

    query = {
        'from_dt': '2022-11-07T07:00:00',
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 200
    response_data = response.json()
    data = response_data.get('data')
    assert len(data) == 5
    actual_request_in_dates = [row[11] for row in data]
    assert actual_request_in_dates == [
        '2022-11-07',
        '2022-11-12',
        '2022-11-13',
        '2022-11-14',
        '2022-11-15'
    ]


@pytest.mark.parametrize('ordering,expected_rows', [
    ('ASC', [
        ('2022-11-15', '5'),
        ('2022-11-12', '25'),
        ('2022-11-07', '60'),
        ('2022-11-14', '100'),
        ('2022-11-13', '300')
    ]),
    ('DESC', [
        ('2022-11-13', '300'),
        ('2022-11-14', '100'),
        ('2022-11-07', '60'),
        ('2022-11-12', '25'),
        ('2022-11-15', '5'),
    ])
])
def test_get_harvest_ordering_requestinsize(db, http_client, ordering, expected_rows):
    log_factory(db, request_in_dt='2022-11-14T08:47:00', requestsize=100)
    log_factory(db, request_in_dt='2022-11-15T10:34:00', requestsize=5)
    log_factory(db, request_in_dt='2022-11-07T09:30:00', requestsize=60)
    log_factory(db, request_in_dt='2022-11-13T08:20:00', requestsize=300)
    log_factory(db, request_in_dt='2022-11-12T08:00:00', requestsize=25)

    query = {
        'from_dt': '2022-11-07T07:00:00',
        'order': json.dumps({
            'column': 'requestsize',
            'order': ordering,
        })
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 200
    response_data = response.json()
    data = response_data.get('data')
    assert len(data) == 5
    actual_dates_request_sizes = [(row[11], row[14]) for row in data]
    assert actual_dates_request_sizes == expected_rows


def test_get_harvest_error_missing_from_dt(http_client, caplog):
    query = {}
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 400
    response_data = response.json()
    assert response_data['errors'] == {
        'from_dt': ['This field is required.']
    }
    assert 'api_get_harvest_input_validation_failed' in caplog.text
    assert 'from_dt: This field is required' in caplog.text


@freeze_time('2022-12-10')
def test_get_harvest_error_from_dt_later_now(http_client):
    query = {
        'from_dt': '2022-12-11T07:00:00',
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 400
    response_data = response.json()
    assert response_data['errors'] == {
        'from_dt': ['Ensure the value is not later than the current date and time']
    }


def test_get_harvest_error_from_dt_later_until_dt(http_client):
    query = {
        'from_dt': '2022-12-13T07:00:00',
        'until_dt': '2022-12-11T07:00:00',
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 400
    response_data = response.json()
    assert response_data['errors'] == {
        'from_dt': ['Ensure the value is not later than until_dt'],
        'until_dt': ['Ensure the value is not earlier than from_dt']
    }


def test_get_harvest_error_invalid_json(http_client):
    query = {
        'from_dt': '2022-12-13T07:00:00',
        'order': 'not valid'
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 400
    response_data = response.json()
    assert response_data['errors'] == {
        'order': ['Ensure "order" is valid json']
    }


def test_get_harvest_error_order_keys(http_client):
    query = {
        'from_dt': '2022-12-13T07:00:00',
        'order': json.dumps({
            'column': 'requestsize',
            'notvalid': 'ASC',
        })
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 400
    response_data = response.json()
    assert response_data['errors'] == {
        'order': ['Ensure only "column" and "order" are set as keys']
    }


def test_get_harvest_error_order_order_values(http_client):
    query = {
        'from_dt': '2022-12-13T07:00:00',
        'order': json.dumps({
            'column': 'requestsize',
            'order': 'asce',
        })
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 400
    response_data = response.json()
    assert response_data['errors'] == {
        'order': ['Ensure only "ASC" or "DESC" is set for order']
    }


def test_get_harvest_db_connection_error(http_client, caplog):
    # test failed connection to db handled successfully
    query = {
        'from_dt': '2022-12-13T07:00:00',
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 500
    response_data = response.json()
    assert response_data['error'] == 'Server encountered error when getting harvest data.'
    assert 'api_get_harvest_query_failed' in caplog.text


def test_get_harvest_error_unsupported_method(http_client):
    query = {
        'from_dt': '2022-12-13T07:00:00',
    }
    response = http_client.post('/api/harvest', query)
    assert response.status_code == 405
    response_data = response.json()
    assert response_data['error'] == 'The requested method is not allowed for the requested resource'


def log_factory(db_session, request_in_dt=None, **kwargs):
    overrides = {}
    overrides.update(**kwargs)
    if request_in_dt:
        if isinstance(request_in_dt, str):
            forma = '%Y-%m-%dT%H:%M:%S'
            request_in_dt = datetime.datetime.strptime(request_in_dt, forma)
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
        'id': random.randint(1000, 999000),
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
