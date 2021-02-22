import psycopg2 as pg
from datetime import datetime
import traceback


class PostgreSqlManager(object):

    def __init__(self, postgres_settings, table_schema, logger):
        self._logger = logger
        self._settings = postgres_settings
        self._table_name = postgres_settings['table-name']
        self._readonly_users = postgres_settings['readonly-users']
        self._connection_string = self._get_connection_string()

        self._field_order = [field_name for field_name, _ in table_schema]
        if table_schema:
            self._ensure_table(table_schema)
            self._ensure_privileges()

    def add_data(self, data):
        if not data:
            return

        try:
            # Inject requestInDate for fast daily queries
            for datum in data:
                datum['requestInDate'] = datetime.fromtimestamp(datum['requestInTs'] / 1000).strftime('%Y-%m-%d')

            with pg.connect(self._connection_string) as connection:
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
            with pg.connect(self._connection_string) as connection:
                pass
            return True

        except Exception:
            trace = traceback.format_exc().replace('\n', '')
            error = f"Failed to connect to postgres with connection string {self._connection_string}. ERROR: {trace}"
            self._logger.log_error('postgres_connection_failed', error)

            return False

    def _ensure_table(self, schema):
        try:
            with pg.connect(self._connection_string) as connection:
                cursor = connection.cursor()
                column_schema = ', '.join(' '.join(column_name_and_type) for column_name_and_type in schema + [])
                if column_schema:
                    column_schema = ', ' + column_schema

                try:
                    cursor.execute(f"CREATE TABLE {self._table_name} (id SERIAL PRIMARY KEY{column_schema})")
                except Exception:
                    pass  # Table exists
        except Exception:
            trace = traceback.format_exc().replace('\n', '')
            error = f"Failed to ensure postgres table {self._table_name} " \
                    + f"existence with connection {self._connection_string}. ERROR: {trace}"
            self._logger.log_error('failed_ensuring_postgres_table', error)
            raise

    def _ensure_privileges(self):
        try:
            with pg.connect(self._connection_string) as connection:
                cursor = connection.cursor()

                for readonly_user in self._readonly_users:
                    try:
                        cursor.execute("GRANT USAGE ON SCHEMA public TO {readonly_user};".format(**{
                            'readonly_user': readonly_user
                        }))
                        cursor.execute("GRANT SELECT ON {table_name} TO {readonly_user};".format(**{
                            'table_name': self._table_name,
                            'readonly_user': readonly_user
                        }))
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
