import psycopg2 as pg


class PostgreSQL_Manager(object):

    def __init__(self, config, field_names, logs_time_buffer):

        self._table_name = config['table_name']
        self._connection_string = self._get_connection_string(**config)
        self._field_name_map = self._get_field_name_map(field_names)
        self._logs_time_buffer = logs_time_buffer

    def get_column_names_and_types(self):
        with pg.connect(self._connection_string) as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT column_name,data_type FROM information_schema.columns WHERE table_name = %s;", (self._table_name, ))
            data = cursor.fetchall()

        return [(self._field_name_map[name], type_) for name, type_ in data]

    def get_data(self, constraints=None, order_by=None, columns=None, limit=None):
        with pg.connect(self._connection_string) as connection:
            cursor = connection.cursor()

            subquery_name = 'T'
            selected_columns_str = self._get_selected_columns_string(columns, subquery_name)
            request_in_date_constraint_str, other_constraints_str = self._get_constraints_string(cursor, constraints, subquery_name)
            order_by_str = self._get_order_by_string(order_by, subquery_name)
            limit_str = self._get_limit_string(cursor, limit)

            cursor.execute(("SELECT {selected_columns} FROM (SELECT * "
                            "FROM {table_name} {request_in_date_constraint}) as {subquery_name} {other_constraints}"
                            "{order_by} {limit};").format(**{
                                                            'selected_columns': selected_columns_str,
                                                            'table_name': self._table_name,
                                                            'request_in_date_constraint': request_in_date_constraint_str,
                                                            'other_constraints': other_constraints_str,
                                                            'order_by': order_by_str,
                                                            'limit': limit_str,
                                                            'subquery_name': subquery_name}
                                                         ))

            data = cursor.fetchall()

        return data

    def get_min_and_max_dates(self):
        with pg.connect(self._connection_string) as connection:
            cursor = connection.cursor()
            cursor.execute('SELECT min(requestindate), max(requestindate) FROM ' + self._table_name)
            min_and_max = [date - self._logs_time_buffer for date in cursor.fetchone()]

        return min_and_max

    def _get_connection_string(self, host_address=None, port=None, database_name=None, user=None, password=None, **irrelevant_settings):
        string_parts = ["host={host} dbname={dbname}".format(
            **{'host': host_address, 'dbname': database_name})]

        if port:
            string_parts.append("port=" + str(port))

        if user:
            string_parts.append("user=" + user)

        if password:
            string_parts.append("password=" + password)

        return ' '.join(string_parts)

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
                    other_constraint_parts.append(cursor.mogrify("{subquery_name}.{column} {operator} %s".format(**{
                        'column': constraint['column'].lower(),
                        'operator': constraint['operator'],
                        'subquery_name': subquery_name
                    }), (constraint['value'], )).decode('utf8'))
            else:
                request_in_date_constraint = 'WHERE ' + cursor.mogrify("{column} {operator} %s".format(**{
                        'column': constraint['column'].lower(),
                        'operator': constraint['operator']
                    }), (constraint['value'], )).decode('utf8')

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
        return cursor.mogrify("LIMIT %s", (limit, )).decode('utf8')
