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