import psycopg2 as pg
from datetime import datetime
import traceback


class PostgreSqlManager(object):

    def __init__(self, postgres_settings, table_schema, logger):
        self._settings = postgres_settings
        self._table_name = postgres_settings['table-name']
        self._readonly_users = postgres_settings['readonly-users']
        self._connection_string = self._get_connection_string()

        self._field_order = [field_name for field_name, _ in table_schema]
        if table_schema:
            self._ensure_table(table_schema)
            self._ensure_privileges()

        self._logger = logger

    def add_data(self, data):
        if data:
            try:
                # Inject requestInDate for fast daily queries
                for datum in data:
                    datum['requestInDate'] = datetime.fromtimestamp(datum['requestInTs'] / 1000).strftime('%Y-%m-%d')

                data = [[record[field_name] for field_name in self._field_order] for record in data]

                with pg.connect(self._connection_string) as connection:
                    cursor = connection.cursor()

                    query_value_rows = [f"({','.join(str(row))})" for row in data]
                    query_values = ','.join(query_value_rows)
                    fields = ','.join(self._field_order)
                    cursor.execute(f'INSERT INTO {self._table_name} ({fields}) VALUES ({query_values})')
            except Exception:
                trace = traceback.format_exc().replace('\n', '')
                self._logger.log_error('log_insertion_failed', f"Failed to insert logs to postgres. ERROR: {trace}")
                raise

    def is_alive(self):
        try:
            with pg.connect(self._connection_string) as connection:
                pass
            return True

        except:
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
                except:
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
                    except:
                        pass  # Privileges existed

        except Exception:
            trace = traceback.format_exc().replace('\n', '')
            self._logger.log_error('ensuring_readolny_users_permissions_failed',
                                   f"Failed to ensure readonly users' permissions for postgres table {self._table_name}"
                                   + f" existence with connection {self._connection_string}. ERROR: {trace}")
            raise

    def _get_connection_string(self):
        args = []
        args += f"host={self._settings['host']}"
        args += f"dbname={self._settings['database-name']}"

        port, user, password = map(self._settings.get, ['port', 'user', 'password'])

        if port:
            args += f"port={port}"

        if user:
            args += f"user={user}"
            if password:
                args += f"password={password}"

        return ' '.join(args)
