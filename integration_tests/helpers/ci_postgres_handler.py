import psycopg2 as pg
import psycopg2.extras as pg_extras


class PostgreSQL_Manager(object):

    def __init__(self, user=None, password=None, host_address=None,
                 database_name=None, port=5432, table_name='logs'):
        self._connection_string = self._get_connection_string(host_address, port, database_name, user, password)
        self._table_name = table_name

    def get_all_logs(self):
        with pg.connect(self._connection_string) as connection:
            cursor = connection.cursor(cursor_factory=pg_extras.RealDictCursor)
            cursor.execute('SELECT * FROM {table_name};'.format(**{'table_name': self._table_name}))

            logs = []
            for log in cursor.fetchall():
                log['requestindate'] = log['requestindate'].strftime('%Y-%m-%d')
                del log['id']
                logs.append(log)

            return logs

    def remove_all(self):
        with pg.connect(self._connection_string) as connection:
            cursor = connection.cursor()
            cursor.execute('DROP TABLE IF EXISTS {table_name};'.format(**{'table_name': self._table_name}))

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