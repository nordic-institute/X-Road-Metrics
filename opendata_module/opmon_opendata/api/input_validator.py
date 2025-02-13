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
import json

AVAILABLE_ORDERS = {'asc', 'desc'}


class OpenDataInputValidator:
    def __init__(self, postgres, settings):
        postgres_to_statistical_type = {'integer': 'numeric', 'character varying': 'categorical', 'date': 'numeric',
                                        'bigint': 'numeric', 'boolean': 'categorical'}

        staticical_type_to_operators = {
            'numeric': {'=', '!=', '<', '<=', '>', '>='},
            'categorical': {'=', '!='}
        }

        column_names_and_types = postgres.get_column_names_and_types()

        self.available_columns = {column_name for column_name, type_ in column_names_and_types}

        self.column_to_type = {
            column_name: postgres_to_statistical_type[type_] for column_name, type_ in column_names_and_types
        }

        self.available_operators = {
            column_name: staticical_type_to_operators[postgres_to_statistical_type[type_]]
            for column_name, type_ in column_names_and_types
        }

        self.settings = settings

    def load_and_validate_date(self, date_str, logs_time_buffer):
        if date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d')
            except Exception:
                raise Exception(f'Date {date_str} is not in required format YYYY-MM-DD.')
        else:
            raise Exception('Missing "date" field.')

        if datetime.now() - logs_time_buffer < date:
            raise Exception(
                'The latest available date is {0}, as {1} days may pass before all the logs for that day are processed.'.format(
                    (datetime.now() - logs_time_buffer).strftime('%Y-%m-%d'), logs_time_buffer.days
                ))

        return date

    def load_and_validate_columns(self, columns):
        if isinstance(columns, str):
            try:
                columns = json.loads(columns)
            except Exception:
                raise Exception('Unable to parse columns as a list of field names.')
        elif not isinstance(columns, list):
            raise Exception('Unable to parse columns as a list of field names.')

        for column in columns:
            if column not in self.available_columns:
                raise Exception('Column "{column_name}" does not exist.'.format(**{
                    'column_name': column
                }))

        return columns

    def load_and_validate_constraints(self, constraints):
        if isinstance(constraints, str):
            try:
                constraints = json.loads(constraints)
            except Exception:
                raise Exception(
                    'Unable to parse constraints as a list of objects with the schema {"column": null, "operator": null, "value": null}.')
        elif not isinstance(constraints, list):
            raise Exception(
                'Unable to parse constraints as a list of objects with the schema {"column": null, "operator": null, "value": null}.')

        for constraint_idx, constraint in enumerate(constraints):
            if not isinstance(constraint, dict):
                raise Exception(
                    'Every constraint must be with the schema {"column": null, "operator": null, "value": null}.')
            for key in ['column', 'operator', 'value']:
                if key not in constraint:
                    raise Exception('Constraint at index {constraint_idx} is missing "{key}" key.'.format(**{
                        'constraint_idx': constraint_idx,
                        'key': key
                    }))
            if constraint['column'] not in self.available_columns:
                raise Exception(
                    'Column "{column_name}" in constraint at index {constraint_idx} does not exist.'.format(**{
                        'column_name': constraint['column'],
                        'constraint_idx': constraint_idx
                    }))

            if constraint['operator'] not in self.available_operators[constraint['column']]:
                raise Exception(
                    'Invalid operator "{operator}" in constraint at index {constraint_idx} for {data_type} data.'.format(
                        **{
                            'operator': constraint['operator'],
                            'constraint_idx': constraint_idx,
                            'data_type': self.column_to_type[constraint['column']]
                        }))

            # TODO check value?

        return constraints

    def load_and_validate_order_clauses(self, order_clauses):
        if isinstance(order_clauses, str):
            try:
                order_clauses = json.loads(order_clauses)
            except Exception:
                raise Exception(
                    'Unable to parse order clauses as a list of objects with the schema {"column": null, "order": null}.')
        elif not isinstance(order_clauses, list):
            raise Exception(
                'Unable to parse order clauses as a list of objects with the schema {"column": null, "order": null}.')

        for order_clause_idx, order_clause in enumerate(order_clauses):
            if not isinstance(order_clause, dict):
                raise Exception('Every constraint must be with the schema {"column": null, "order": null}.')
            for key in ['column', 'order']:
                if key not in order_clause:
                    raise Exception('Order clause at index {order_clause_idx} is missing "{key}" key.'.format(**{
                        'order_clause_idx': order_clause_idx,
                        'key': key
                    }))
            if order_clause['column'] not in self.available_columns:
                raise Exception(
                    'Column "{column_name}" in order clause at index {order_clause_idx} does not exist.'.format(**{
                        'column_name': order_clause['column'],
                        'order_clause_idx': order_clause_idx
                    }))
            if order_clause['order'] not in AVAILABLE_ORDERS:
                raise Exception(
                    'Can not order data in {order} order in order clause at index {order_clause_idx}.'.format(**{
                        'order': order_clause['order'],
                        'order_clause_idx': order_clause_idx
                    }))

        return order_clauses
