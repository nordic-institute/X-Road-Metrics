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

from typing import Dict, List, Optional, Tuple

import psycopg2 as pg
from dateutil import relativedelta


class BasePostgreSQL_Manager:
    def __init__(self, settings):
        self._settings = settings['postgres']
        self._connection_string = self._get_connection_string()
        self._connect_args = {
            'sslmode': settings['postgres'].get('ssl-mode'),
            'sslrootcert': settings['postgres'].get('ssl-root-cert')
        }

    def _get_connection_string(self):
        args = [
            f"host={self._settings['host']}",
            f"dbname={self._settings['database-name']}"
        ]

        optional_settings = {key: self._settings.get(key) for key in ['port', 'user', 'password']}
        optional_args = [f'{key}={value}' if value else '' for key, value in optional_settings.items()]
        return ' '.join(args + optional_args)


class PostgreSQL_LogManager(BasePostgreSQL_Manager):

    def __init__(self, settings):
        self._table_name = settings['postgres']['table-name']
        self._field_name_map = self._get_field_name_map(settings['opendata']['field-descriptions'].keys())
        self._logs_time_buffer = relativedelta.relativedelta(days=settings['opendata']['delay-days'])
        super().__init__(settings)

    def get_column_names_and_types(self):
        with pg.connect(self._connection_string, **self._connect_args) as connection:
            cursor = connection.cursor()
            cursor.execute('SELECT column_name,data_type FROM information_schema.columns WHERE table_name = %s;',
                           (self._table_name,))
            data = cursor.fetchall()

        return [(self._field_name_map[name], type_) for name, type_ in data]

    def get_rows_count(self, constraints: List[Dict[str, object]]) -> Tuple[int]:
        """
        Returns the number of rows in the specified table that satisfy the given constraints.

        :param constraints: A list of tuples containing the constraints to be applied to the query

        :return: tuple: A tuple containing a single element which is the number of rows that satisfy the constraints.
        """
        with pg.connect(self._connection_string, **self._connect_args) as connection:
            cursor = connection.cursor()

            subquery_name = 'T'
            request_in_date_constraint_str, other_constraints_str = self._get_constraints_string(cursor, constraints,
                                                                                                 subquery_name)
            cursor.execute(
                ('SELECT COUNT(*) FROM (SELECT * '
                 'FROM {table_name} {request_in_date_constraint}) as {subquery_name} {other_constraints}').format(
                    **{
                        'table_name': self._table_name,
                        'request_in_date_constraint': request_in_date_constraint_str,
                        'other_constraints': other_constraints_str,
                        'subquery_name': subquery_name,
                    }
                )
            )
            return cursor.fetchone()

    def get_data_cursor(
        self, constraints: Optional[List] = None, order_by: Optional[List] = None,
        columns: Optional[List] = None, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> pg.extensions.cursor:
        """
        Return a cursor object from a PostgreSQL database connection that executes a SQL SELECT statement
            with optional constraints, ordering, columns selection, and pagination.

        :param constraints: A list of tuples containing the constraints to be applied to the query. Default is None.
        :param order_by: A list of tuples containing the columns to order the query by. Default is None.
        :param columns: A list of column names to select in the query. Default is None (all columns selected).
        :param limit: An integer representing the maximum number of rows to be returned by the query. Default is None (no limit).
        :param offset: An integer representing the number of rows to skip before starting to return rows. Default is None.

        :return: A PostgreSQL cursor object that executes the SQL query.
        """
        with pg.connect(self._connection_string, **self._connect_args) as connection:
            # Using server side cursor to avoid fetching whole query result into memory.
            # A cursor created without HOLD would get automatically closed in the current programm before data is read from it.
            # PostgreSQL logs show COMMIT right after DECLARE CURSOR, probably because Python detects end of "with pg.connect" block.
            # A cursor created with HOLD is automatically closed when PostgreSQL session (connection) ends.
            # As programm creates a new connection for every operation a unique name for cursor is not required.
            cursor = connection.cursor('opendata', withhold=True)

            subquery_name = 'T'
            selected_columns_str = self._get_selected_columns_string(columns, subquery_name)
            request_in_date_constraint_str, other_constraints_str = self._get_constraints_string(cursor, constraints,
                                                                                                 subquery_name)
            order_by_str = self._get_order_by_string(order_by, subquery_name)
            limit_str = self._get_limit_string(cursor, limit)
            offset_str = self._get_offset_string(cursor, offset)

            cursor.execute(
                ('SELECT {selected_columns} FROM (SELECT * '
                 'FROM {table_name} {request_in_date_constraint}) as {subquery_name} {other_constraints}'
                 ' {order_by} {limit} {offset};').format(
                    **{
                        'selected_columns': selected_columns_str,
                        'table_name': self._table_name,
                        'request_in_date_constraint': request_in_date_constraint_str,
                        'other_constraints': other_constraints_str,
                        'order_by': order_by_str,
                        'limit': limit_str,
                        'subquery_name': subquery_name,
                        'offset': offset_str,
                    }
                )
            )
            return cursor

    def get_data(self, constraints=None, order_by=None, columns=None, limit=None):
        return self.get_data_cursor(constraints=constraints, order_by=order_by, columns=columns, limit=limit).fetchall()

    def get_min_and_max_dates(self):
        with pg.connect(self._connection_string, **self._connect_args) as connection:
            cursor = connection.cursor()
            cursor.execute('SELECT min(requestindate) as "min [date]", max(requestindate) as "max [date]" FROM ' + self._table_name)
            min_and_max = [date - self._logs_time_buffer for date in cursor.fetchone()]

        return min_and_max

    def _get_field_name_map(self, field_names):
        return {field_name.lower(): field_name for field_name in field_names}

    def _get_constraints_string(self, cursor, constraints, subquery_name):
        if not constraints:
            return ''

        request_in_date_constraint = None
        other_constraint_parts = []

        for constraint in constraints:
            if constraint['column'] != 'requestInDate':
                if constraint['value'] == 'None':
                    null_constraint = 'IS NULL' if constraint['operator'] == '=' else 'IS NOT NULL'
                    other_constraint_parts.append("{subquery_name}.{column} {null_constraint}".format(**{
                        'column': constraint['column'],
                        'null_constraint': null_constraint,
                        'subquery_name': subquery_name
                    }))
                else:
                    other_constraint_parts.append(cursor.mogrify("{subquery_name}.{column} {operator} %s".format(**{
                        'column': constraint['column'].lower(),
                        'operator': constraint['operator'],
                        'subquery_name': subquery_name
                    }), (constraint['value'],)).decode('utf8'))
            else:
                request_in_date_constraint = 'WHERE ' + cursor.mogrify("{column} {operator} %s".format(**{
                    'column': constraint['column'].lower(),
                    'operator': constraint['operator']
                }), (constraint['value'],)).decode('utf8')

        other_constraints = ('WHERE ' + ' AND '.join(other_constraint_parts)) if other_constraint_parts else ''

        return request_in_date_constraint, other_constraints

    def _get_selected_columns_string(self, columns, subquery_name):
        if not columns:
            return '*'
        else:
            return ', '.join('{0}.{1}'.format(subquery_name, column.lower()) for column in columns)

    def _get_order_by_string(self, order_by, subquery_name):
        if not order_by:
            return ''

        return 'ORDER BY ' + ', '.join('{subquery_name}.{column} {order}'.format(**{
            'subquery_name': subquery_name,
            'column': clause['column'],
            'order': clause['order']
        }) for clause in order_by)

    def _get_limit_string(self, cursor, limit):
        return cursor.mogrify('LIMIT %s', (limit,)).decode('utf8')

    def _get_offset_string(self, cursor: pg.extensions.cursor, offset: Optional[int] = None) -> str:
        """
        Return a SQL string to be used in a query to set the offset for pagination.

        :param cursor: A PostgreSQL cursor object.
        :param offset: An integer representing the number of rows to skip before starting to return rows.
        :return: A string containing the SQL command to set the offset for pagination.
        """
        return cursor.mogrify('OFFSET %s', (offset,)).decode('utf8')


class PostgreSQL_StatisticsManager(BasePostgreSQL_Manager):
    def __init__(self, settings):
        self._table_name = 'metrics_statistics'
        super().__init__(settings)

    def get_latest_metrics_statistics(self):
        """
            Retrieve the latest metrics statistics from the database.

            :return: A dictionary representing the latest metrics statistics if available, else None.
        """
        with pg.connect(self._connection_string, **self._connect_args) as connection:
            cursor = connection.cursor()
            cursor.execute(
                '''SELECT
                    current_month_request_count,
                    current_year_request_count,
                    previous_month_request_count,
                    previous_year_request_count,
                    today_request_count,
                    total_request_count,
                    update_time,
                    member_count,
                    service_count,
                    service_request_count
                    FROM {table_name}
                    WHERE update_time = (SELECT MAX(update_time)
                FROM {table_name})'''.format(**{'table_name': self._table_name})
            )
            row = cursor.fetchone()
        return {
            'current_month_request_count': row[0],
            'current_year_request_count': row[1],
            'previous_month_request_count': row[2],
            'previous_year_request_count': row[3],
            'today_request_count': row[4],
            'total_request_count': row[5],
            'update_time': row[6],
            'member_count': row[7],
            'service_count': row[8],
            'service_request_count': row[9]
        } if row else None
