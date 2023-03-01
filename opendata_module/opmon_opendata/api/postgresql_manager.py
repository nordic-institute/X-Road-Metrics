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
from dateutil import relativedelta
from typing import Optional, List


class PostgreSQL_Manager(object):

    def __init__(self, settings):

        self._settings = settings['postgres']
        self._table_name = settings['postgres']['table-name']
        self._connection_string = self._get_connection_string()
        self._field_name_map = self._get_field_name_map(settings['opendata']['field-descriptions'].keys())
        self._logs_time_buffer = relativedelta.relativedelta(days=settings['opendata']['delay-days'])
        self._connect_args = {
            'sslmode': settings['postgres'].get('ssl-mode'),
            'sslrootcert': settings['postgres'].get('ssl-root-cert')
        }

    def get_column_names_and_types(self):
        with pg.connect(self._connection_string, **self._connect_args) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT column_name,data_type FROM information_schema.columns WHERE table_name = %s;",
                (self._table_name,))
            data = cursor.fetchall()

        return [(self._field_name_map[name], type_) for name, type_ in data]

    def get_data_cursor(
        self, constraints: Optional[List] = None, order_by: Optional[List] = None,
        columns: Optional[List] = None, limit: Optional[int] = None
    ) -> pg.extensions.cursor:
        with pg.connect(self._connection_string, **self._connect_args) as connection:
            cursor = connection.cursor()

            subquery_name = 'T'
            selected_columns_str = self._get_selected_columns_string(columns, subquery_name)
            request_in_date_constraint_str, other_constraints_str = self._get_constraints_string(cursor, constraints,
                                                                                                 subquery_name)
            order_by_str = self._get_order_by_string(order_by, subquery_name)
            limit_str = self._get_limit_string(cursor, limit)

            query = """SELECT %(selected_columns)s
            FROM (
                SELECT * FROM %s(table_name)s %(request_in_data_constraint)s
                )
                as %(subquery_name)s %(other_constraints)s %(order_by)s %(limit)s;
                """
            params = {
                'selected_columns': selected_columns_str,
                'table_name': self._table_name,
                'request_in_data_constraint': request_in_date_constraint_str,
                'subquery_name': subquery_name,
                'other_constraints': other_constraints_str,
                'order_by': order_by_str,
                'limit': limit_str,
            }
            cursor.execute(query, params)
            return cursor

    def get_data(self, constraints=None, order_by=None, columns=None, limit=None):
        return self.get_data_cursor(constraints=constraints, order_by=order_by, columns=columns, limit=limit).fetchall()

    def get_min_and_max_dates(self):
        with pg.connect(self._connection_string, **self._connect_args) as connection:
            cursor = connection.cursor()
            cursor.execute(
                "SELECT min(requestindate), max(requestindate) FROM %s;", (self._table_name,)
            )
            min_and_max = [date - self._logs_time_buffer for date in cursor.fetchone()]

        return min_and_max

    def _get_connection_string(self):
        args = [
            f"host={self._settings['host']}",
            f"dbname={self._settings['database-name']}"
        ]

        optional_settings = {key: self._settings.get(key) for key in ['port', 'user', 'password']}
        optional_args = [f"{key}={value}" if value else "" for key, value in optional_settings.items()]

        return ' '.join(args + optional_args)

    def _get_database_settings(self, config):
        settings = {'host_address': config['writer']['host_address'],
                    'port': config['writer']['port'],
                    'database_name': config['writer']['database_name'],
                    'user': config['writer']['user'],
                    'password': config['writer']['password']}

        return settings

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
                    other_constraint_parts.append(cursor.mogrify(
                        "%s.%s %s %s",
                        (
                            subquery_name,
                            constraint['column'].lower(),
                            constraint['operator'],
                            constraint['value'],
                        )
                    ).decode('utf8'))
            else:
                request_in_date_constraint = 'WHERE ' + cursor.mogrify(
                    "%s %s %s",
                    (
                        constraint['column'].lower(),
                        constraint['operator'],
                        constraint['value'],
                    )
                ).decode('utf8')

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
        return cursor.mogrify("LIMIT %s", (limit,)).decode('utf8')
