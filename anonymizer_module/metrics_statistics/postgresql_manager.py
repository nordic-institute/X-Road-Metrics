#
# The MIT License 
# Copyright (c) 2021- Nordic Institute for Interoperability Solutions (NIIS)
# Copyright (c) 2017-2020 Estonian Information System Authority (RIA)
#  
# Permission is hereby granted, free of charge, to any person obtaining a copy 
# of this software and associated documentation files (the "Software"), to deal 
# in the Software without restriction, including without limitation the rights 
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions: 
#  
# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software. 
#  
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN 
# THE SOFTWARE.
#

from datetime import datetime
from logging import Logger
from typing import Dict, List, Optional, Tuple, TypedDict

import psycopg2 as pg

from metrics_statistics.mongodb_manager import RequestsCountData

METRICS_STATISTICS_TABLE = 'metrics_statistics'


class MetricsStatisticsField(TypedDict):
    type: str
    index: Optional[bool]


class StatisticalData(RequestsCountData):
    member_count: str
    service_count: int
    service_request_count: str


METRICS_STATISTICS_SCHEMA: Dict[str, MetricsStatisticsField] = {
    'update_time': {
        'type': 'timestamp',
        'index': True
    },
    'total_request_count': {
        'type': 'integer',
        'index': False
    },
    'previous_year_request_count': {
        'type': 'integer',
        'index': False
    },
    'current_year_request_count': {
        'type': 'integer',
        'index': False,
    },
    'previous_month_request_count': {
        'type': 'integer',
        'index': False,
    },
    'current_month_request_count': {
        'type': 'integer',
        'index': False,
    },
    'today_request_count': {
        'type': 'integer',
        'index': True
    },
    'member_count': {
        'type': 'json',
        'index': False,
    },
    'service_count': {
        'type': 'integer',
        'index': False,
    },
    'service_request_count': {
        'type': 'json',
        'index': False
    }
}


class BasePostgreSQL_Manager:
    def __init__(self, settings: dict):
        self._settings = settings
        self._connection_string = self._get_connection_string()
        self._connect_args = {
            'sslmode': settings.get('ssl-mode'),
            'sslrootcert': settings.get('ssl-root-cert')
        }

    def _get_connection_string(self) -> str:
        args = [
            f"host={self._settings['host']}",
            f"dbname={self._settings['database-name']}"
        ]

        optional_settings = {key: self._settings.get(key) for key in ['port', 'user', 'password']}
        optional_args = [f'{key}={value}' if value else '' for key, value in optional_settings.items()]
        return ' '.join(args + optional_args)


class PostgreSQL_StatisticsManager(BasePostgreSQL_Manager):

    def __init__(self, postgres_settings: dict, logger: Logger) -> None:
        self._logger = logger
        self._settings = postgres_settings
        self._table_name = METRICS_STATISTICS_TABLE
        self._readonly_users = postgres_settings['readonly-users']
        self._connection_string = self._get_connection_string()

        table_schema = PostgreSQL_StatisticsManager.get_schema()
        index_columns = PostgreSQL_StatisticsManager.get_indices()
        self._field_order = [field_name for field_name, _ in table_schema]
        super().__init__(self._settings)
        if table_schema:
            self._ensure_table(table_schema, index_columns)
            self._ensure_privileges()

    @staticmethod
    def get_schema() -> List[Tuple[str, str]]:
        schema = [
            (field_name, field_data['type'])
            for field_name, field_data in METRICS_STATISTICS_SCHEMA.items()
        ]
        schema.sort()
        return schema

    @staticmethod
    def get_indices() -> List[str]:
        return [
            field_name for field_name, field_data in METRICS_STATISTICS_SCHEMA.items()
            if field_data.get('index')
        ]

    def add_statistics(self, data: StatisticalData) -> None:
        try:
            data['update_time'] = datetime.now()
            with pg.connect(self._connection_string, **self._connect_args) as connection:
                cursor = connection.cursor()
                query = self._generate_insert_query(cursor, data)
                cursor.execute(query)
                self._logger.info('PostgreSqlManager.add_statistics. Added successfully')
        except Exception as e:
            self._logger.exception(f'statistics_insertion_failed. Failed to insert statistics to postgres. ERROR: {str(e)}')
            raise

    def _generate_insert_query(self, cursor: pg.extensions.cursor, data: StatisticalData) -> str:
        column_names = ','.join(self._field_order)
        template = '({})'.format(','.join(['%s'] * len(self._field_order)))

        rows = []

        record_values = [data.get(field_name) for field_name in self._field_order]
        rows.append(cursor.mogrify(template, record_values).decode('utf-8'))

        query_rows = ','.join(rows)
        return f'INSERT INTO {self._table_name} ({column_names}) VALUES {query_rows}'

    def is_alive(self) -> bool:
        try:
            with pg.connect(self._connection_string, **self._connect_args):
                pass
            return True

        except Exception as e:
            error = f'Failed to connect to postgres with connection string {self._connection_string}. {str(e)}'
            self._logger.exception(f'postgres_connection_failed. Error: {error}')
            return False

    def _ensure_table(self, schema: List[Tuple[str, str]], index_columns: List[str]) -> None:
        try:
            with pg.connect(self._connection_string, **self._connect_args) as connection:
                cursor = connection.cursor()
                if not self._table_exists(cursor):
                    self._create_table(cursor, schema, index_columns)

        except Exception as e:
            error = f'Failed to ensure postgres table {self._table_name} ' \
                    + f'existence with connection {self._connection_string}. ERROR: {str(e)}'
            self._logger.exception(f'failed_ensuring_postgres_table. Error: {str(error)}')
            raise

    def _table_exists(self, cursor: pg.extensions.cursor) -> bool:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE  table_schema = 'public'
                AND table_name = %s
            );
        """, (self._table_name,))
        result = cursor.fetchone()
        return bool(result[0]) if result else False

    def _create_table(self, cursor: pg.extensions.cursor,
                      schema: List[Tuple[str, str]], index_columns: List[str]) -> None:
        column_schema = ', '.join(' '.join(column_name_and_type) for column_name_and_type in schema + [])
        if column_schema:
            column_schema = ', ' + column_schema

            cursor.execute(f'CREATE TABLE {self._table_name} (id SERIAL PRIMARY KEY{column_schema});')

            for column_name in index_columns:
                cursor.execute(f'CREATE INDEX {column_name}_idx ON {self._table_name} ({column_name});')

    def _ensure_privileges(self) -> None:
        try:
            with pg.connect(self._connection_string, **self._connect_args) as connection:
                cursor = connection.cursor()

                for readonly_user in self._readonly_users:
                    cursor.execute(
                        'GRANT USAGE ON SCHEMA public TO {readonly_user};'.format(
                            **{
                                'readonly_user': readonly_user
                            })
                    )
                    cursor.execute(
                        'GRANT SELECT ON {table_name} TO {readonly_user};'.format(
                            **{
                                'table_name': self._table_name,
                                'readonly_user': readonly_user
                            })
                    )

        except Exception as e:
            self._logger.exception(f'Failed to ensure readonly users permissions for postgres table {self._table_name}'
                                   + f' existence with connection {self._connection_string}. ERROR: {str(e)}')
            raise


class PostgreSQL_LogManager(BasePostgreSQL_Manager):
    def __init__(self, postgres_settings: dict, logger: Logger):
        self._logger = logger
        self._table_name = postgres_settings['table-name']
        super().__init__(postgres_settings)

    def get_services(self) -> List[str]:
        with pg.connect(self._connection_string, **self._connect_args) as connection:
            cursor = connection.cursor()
            cursor.execute('SELECT servicesubsystemcode FROM {table_name} GROUP BY servicesubsystemcode;'.format(**{'table_name': self._table_name}))
            data = cursor.fetchall()
            return [service[0] for service in data if service[0]]
