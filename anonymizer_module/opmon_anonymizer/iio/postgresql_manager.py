import psycopg2 as pg
from datetime import datetime
import logging
import traceback
from anonymizer.utils import logger_manager


class PostgreSQL_Manager(object):

    def __init__(self, host_address='localhost', port_number='5432', database_name='opendata', table_name='logs', user=None, password=None,
                 table_schema=None, readonly_users=None, threshold_ts=None):
        self._table_name = table_name
        self._readonly_users = readonly_users
        self._connection_string = self._get_connection_string(host_address, port_number, database_name, user, password)

        self._field_order = [field_name for field_name, field_type in table_schema]

        if table_schema:
            self._ensure_table(table_schema)
            self._ensure_privileges()

    def add_data(self, data):
        if data:
            try:
                # Inject requestInDate for fast daily queries
                for datum in data:
                    datum['requestInDate'] = datetime.fromtimestamp(datum['requestInTs'] / 1000).strftime('%Y-%m-%d')

                data = [[record[field_name] for field_name in self._field_order] for record in data]

                with pg.connect(self._connection_string) as connection:
                    cursor = connection.cursor()
                    insertion_str = ','.join(cursor.mogrify("({0})".format(','.join(['%s'] * len(row))), row).decode('utf8') for row in data)
                    cursor.execute('INSERT INTO {table_name} ({fields}) VALUES '.format(
                        **{'table_name': self._table_name, 'fields': ','.join(self._field_order)}) + insertion_str)
            except Exception:
                logger = logger_manager.LoggerManager(logger_name='opendata-anonymizer', module='opendata')
                logger.log_error('log_insertion_failed',
                                 "Failed to insert logs to postgres. ERROR: {0}".format(
                                     traceback.format_exc().replace('\n', '')
                                 ))
                raise

    def is_alive(self):
        try:
            with pg.connect(self._connection_string) as connection:
                pass
            return True

        except:
            logger = logger_manager.LoggerManager(logger_name='opendata-anonymizer', module='opendata')
            logger.log_error('postgres_connection_failed',
                             "Failed to connect to postgres with connection string {0}. ERROR: {1}".format(
                                 self._connection_string, traceback.format_exc().replace('\n', '')))
            return False

    def _ensure_table(self, schema):
        try:
            with pg.connect(self._connection_string) as connection:
                cursor = connection.cursor()
                column_schema = ', '.join(' '.join(column_name_and_type) for column_name_and_type in schema + [])
                if column_schema:
                    column_schema = ', ' + column_schema

                try:
                    cursor.execute("CREATE TABLE {table_name} (id SERIAL PRIMARY KEY{column_schema})".format(
                        **{'table_name': self._table_name, 'column_schema': column_schema}))
                except:
                    pass    # Table existed
        except Exception:
            logger = logger_manager.LoggerManager(logger_name='opendata-anonymizer', module='opendata')
            logger.log_error('failed_ensuring_postgres_table',
                             "Failed to ensure postgres table {0} existence with connection {1}. ERROR: {2}".format(
                                 self._table_name, self._connection_string, traceback.format_exc().replace('\n', '')
                             ))
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
                        pass    # Privileges existed

        except Exception:
            logger = logger_manager.LoggerManager(logger_name='opendata-anonymizer', module='opendata')
            logger.log_error('ensuring_readolny_users_permissions_failed',
                             "Failed to ensure readonly users' permissions for postgres table {0} existence with connection {1}".format(
                                 self._table_name, self._connection_string, traceback.format_exc().replace('\n', '')
                             ))
            raise

    def _get_connection_string(self, host, port, database_name, user, password):
        string_parts = ["host={host} dbname={dbname}".format(
            **{'host': host, 'dbname': database_name})]

        if port:
            string_parts.append("port=" + str(port))

        if user:
            string_parts.append("user=" + user)

        if password:
            string_parts.append("password=" + password)

        return ' '.join(string_parts)
