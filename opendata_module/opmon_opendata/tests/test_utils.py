import datetime
import sqlite3
from logging import StreamHandler
from typing import Union

import pytest
from django.test import Client

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

FIELD_DESCRIPTIONS = {
    'field1': {
        'type': 'varchar(255)',
        'description': 'test description'
    }
}

TEST_SETTINGS = {
    'logger': {
        'name': 'test',
        'module': 'test',
        'level': 2,
        'log-path': 'test',
        'heartbeat-path': 'test',
    },
    'django': {
        'secret-key': 'sdsdsd',
        'allowed-hosts': []
    },
    'xroad': {
        'instance': 'TEST'
    },
    'postgres': {
        'table-name': 'logs',
        'host': 'test',
        'database-name': 'test',
        'user': 'test',
        'password': 'test'
    },
    'opendata': {
        'delay-days': 1,
        'maintenance-mode': False,
        'disclaimer': '<!--insert your custom HTML disclaimer here-->',
        'header': '<!--insert your custom HTML header here-->',
        'footer': '<!--insert your custom HTML footer here-->',
        'field-descriptions': FIELD_DESCRIPTIONS
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


class MockSettingsParser:
    def __init__(self) -> None:
        settings = TEST_SETTINGS.copy()
        self.settings = settings


@pytest.fixture(autouse=True)
def mock_settings(mocker):
    mocker.patch('opmon_opendata.settings_parser.OpmonSettingsManager')
    mocker.patch(
        'opmon_opendata.opendata_settings_parser.OpenDataSettingsParser',
        return_value=MockSettingsParser()
    )


class MockPsyContextManager(object):
    def __init__(self, mock_cursor):
        self._mock_cursor = mock_cursor

    def __enter__(self):
        return self

    def cursor(self, name=None, withhold=None):
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

    def fetchone(self, *args, **kwargs):
        return self._sql_session.fetchone(*args, **kwargs)


@pytest.fixture(autouse=True)
def mock_logger_manager(mocker):
    mocker.patch(
        'opmon_opendata.logger_manager.LoggerManager._create_file_handler',
        return_value=StreamHandler()
    )
    yield mocker.Mock()


@pytest.fixture
def http_client():
    yield Client()


@pytest.fixture
def db(mocker):
    mocker.patch(
        'opmon_opendata.api.postgresql_manager.PostgreSQL_LogManager.get_column_names_and_types',
        return_value=COLUMNS_AND_TYPES
    )
    connection = sqlite3.connect(':memory:',
                                 detect_types=sqlite3.PARSE_COLNAMES | sqlite3.PARSE_DECLTYPES)
    db_session = connection.cursor()
    # mimic PG and return result as rows, not as tuple
    db_session.row_factory = sqlite3.Row
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
        member_gov_count integer,
        member_com_count integer,
        member_org_count integer,
        service_count integer,
        services_request_counts json,
        update_time timestamp);
    """)
    connection.commit()
    mocker.patch(
        'psycopg2.connect',
        return_value=MockPsyContextManager(MockSQLiteCursor(db_session))
    )
    yield db_session
    connection.close()


def log_factory(db_session: sqlite3.Cursor,
                request_in_dt: Union[str, datetime.datetime, None] = None, **kwargs) -> None:
    overrides: dict = {}
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


def make_m_statistics(db_session, **kwargs):
    defaults = {
        'id': 0,
        'current_month_request_count': 101,
        'current_year_request_count': 12345,
        'previous_month_request_count': 753,
        'previous_year_request_count': 10234,
        'today_request_count': 12,
        'total_request_count': 999999,
        'update_time': datetime.datetime.now(),
    }
    defaults.update(kwargs)
    db_session.execute("""
                    INSERT INTO metrics_statistics(
                        id,
                        current_month_request_count,
                        current_year_request_count,
                        previous_month_request_count,
                        previous_year_request_count,
                        today_request_count,
                        total_request_count,
                        member_gov_count,
                        member_com_count,
                        member_org_count,
                        service_count,
                        services_request_counts,
                        update_time
                    )
                    VALUES(
                        :id,
                        :current_month_request_count,
                        :current_year_request_count,
                        :previous_month_request_count,
                        :previous_year_request_count,
                        :today_request_count,
                        :total_request_count,
                        :member_gov_count,
                        :member_com_count,
                        :member_org_count,
                        :service_count,
                        :services_request_counts,
                        :update_time
                    )
                    """,
                       defaults)


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
