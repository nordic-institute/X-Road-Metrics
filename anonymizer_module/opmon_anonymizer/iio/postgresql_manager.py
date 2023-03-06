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

import psycopg2 as pg
from datetime import datetime
import traceback


class PostgreSqlManager(object):

    def __init__(self, postgres_settings, table_schema, index_columns, logger):
        self._logger = logger
        self._settings = postgres_settings
        self._table_name = postgres_settings['table-name']
        self._readonly_users = postgres_settings['readonly-users']
        self._connection_string = self._get_connection_string()
        self._connect_args = {
            'sslmode': postgres_settings.get('ssl-mode'),
            'sslrootcert': postgres_settings.get('ssl-root-cert')
        }

        self._field_order = [field_name for field_name, _ in table_schema]
        if table_schema:
            self._ensure_table(table_schema, index_columns)
            self._ensure_privileges()

    def add_data(self, data):
        if not data:
            return

        try:
            # Inject requestInDate for fast daily queries
            for datum in data:
                datum['requestInDate'] = datetime.fromtimestamp(datum['requestInTs'] / 1000).strftime('%Y-%m-%d')

            with pg.connect(self._connection_string, **self._connect_args) as connection:
                cursor = connection.cursor()
                query = self._generate_insert_query(cursor, data)
                cursor.execute(query)
                self._logger.log_info('PostgreSqlManager.add_data', f'Inserted {len(data)} rows to PostgreSQL.')
        except Exception:
            trace = traceback.format_exc().replace('\n', '')
            self._logger.log_error('log_insertion_failed', f"Failed to insert logs to postgres. ERROR: {trace}")
            raise

    def _generate_insert_query(self, cursor, data):
        column_names = ','.join(self._field_order)
        template = '({})'.format(','.join(['%s'] * len(self._field_order)))

        rows = []

        for record in data:
            record_values = [record[field_name] for field_name in self._field_order]
            rows.append(cursor.mogrify(template, record_values).decode('utf-8'))

        query_rows = ','.join(rows)
        return f'INSERT INTO {self._table_name} ({column_names}) VALUES {query_rows}'

    def is_alive(self):
        try:
            with pg.connect(self._connection_string, **self._connect_args) as connection:
                pass
            return True

        except Exception:
            trace = traceback.format_exc().replace('\n', '')
            error = f"Failed to connect to postgres with connection string {self._connection_string}. ERROR: {trace}"
            self._logger.log_error('postgres_connection_failed', error)

            return False

    def _ensure_table(self, schema, index_columns):
        try:
            with pg.connect(self._connection_string, **self._connect_args) as connection:
                cursor = connection.cursor()
                if not self._table_exists(cursor):
                    self._create_table(cursor, schema, index_columns)

        except Exception:
            trace = traceback.format_exc().replace('\n', '')
            error = f"Failed to ensure postgres table {self._table_name} " \
                    + f"existence with connection {self._connection_string}. ERROR: {trace}"
            self._logger.log_error('failed_ensuring_postgres_table', error)
            raise

    def _table_exists(self, cursor):
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE  table_schema = 'public'
                AND table_name = %s
            );
        """, (cursor._table_name,))

        return cursor.fetchone()[0]

    def _create_table(self, cursor, schema, index_columns):
        column_schema = ', '.join(' '.join(column_name_and_type) for column_name_and_type in schema + [])
        if column_schema:
            column_schema = ', ' + column_schema

            cursor.execute(f"CREATE TABLE {self._table_name} (id SERIAL PRIMARY KEY{column_schema});")

            for column_name in index_columns:
                cursor.execute(f"CREATE INDEX {column_name}_idx ON {self._table_name} ({column_name});")

    def _ensure_privileges(self):
        try:
            with pg.connect(self._connection_string, **self._connect_args) as connection:
                cursor = connection.cursor()

                for readonly_user in self._readonly_users:
                    try:
                        cursor.execute(
                            "GRANT USAGE ON SCHEMA public TO %s;", (readonly_user,)
                        )
                        cursor.execute(
                            "GRANT SELECT ON %s TO %s;", (self._table_name, readonly_user)
                        )
                    except Exception:
                        pass  # Privileges existed

        except Exception:
            trace = traceback.format_exc().replace('\n', '')
            self._logger.log_error('ensuring_readolny_users_permissions_failed',
                                   f"Failed to ensure readonly users' permissions for postgres table {self._table_name}"
                                   + f" existence with connection {self._connection_string}. ERROR: {trace}")
            raise

    def _get_connection_string(self):
        args = [
            f"host={self._settings['host']}",
            f"dbname={self._settings['database-name']}"
        ]

        optional_settings = {key: self._settings.get(key) for key in ['port', 'user', 'password']}
        optional_args = [f"{key}={value}" if value else "" for key, value in optional_settings.items()]

        return ' '.join(args + optional_args)
