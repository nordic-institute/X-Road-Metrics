from datetime import datetime
import json

from interface.settings import POSTGRES_CONFIG, FIELD_DESCRIPTIONS, LOGS_TIME_BUFFER

from .postgresql_manager import PostgreSQL_Manager

AVAILABLE_COLUMNS, AVAILABLE_OPERATORS, COLUMN_TO_TYPE = None, None, None
AVAILABLE_ORDERS = {'asc', 'desc'}


def _load_column_data():
    PGM = PostgreSQL_Manager(POSTGRES_CONFIG, FIELD_DESCRIPTIONS.keys(), LOGS_TIME_BUFFER)
    postgres_to_statistical_type = {'integer': 'numeric', 'character varying': 'categorical', 'date': 'numeric',
                                    'bigint': 'numeric', 'boolean': 'categorical'}

    staticical_type_to_operators = {
        'numeric': {'=', '!=', '<', '<=', '>', '>='},
        'categorical': {'=', '!='}
    }

    column_names_and_types = PGM.get_column_names_and_types()

    available_columns = {column_name for column_name, type_ in column_names_and_types}
    column_to_type = {column_name: postgres_to_statistical_type[type_] for column_name, type_ in column_names_and_types}
    available_operators = {
        column_name: staticical_type_to_operators[postgres_to_statistical_type[type_]]
        for column_name, type_ in column_names_and_types
    }

    return available_columns, available_operators, column_to_type


def load_and_validate_date(date_str):
    if date_str:
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
        except:
            raise Exception('Date must be in the format "YYYY-MM-DD".')
    else:
        raise Exception('Missing "date" field.')

    if datetime.now() - LOGS_TIME_BUFFER < date:
        raise Exception('The latest available date is {0}, as {1} days may pass before all the logs for that day are processed.'.format(
            (datetime.now() - LOGS_TIME_BUFFER).strftime('%Y-%m-%d'), LOGS_TIME_BUFFER.days
        ))

    return date


def load_and_validate_columns(columns):
    global AVAILABLE_COLUMNS, AVAILABLE_OPERATORS, COLUMN_TO_TYPE
    if not AVAILABLE_COLUMNS:
        AVAILABLE_COLUMNS, AVAILABLE_OPERATORS, COLUMN_TO_TYPE = _load_column_data()

    if isinstance(columns, str):
        try:
            columns = json.loads(columns)
        except:
            raise Exception('Unable to parse columns as a list of field names.')
    elif not isinstance(columns, list):
        raise Exception('Unable to parse columns as a list of field names.')

    for column in columns:
        if column not in AVAILABLE_COLUMNS:
            raise Exception('Column "{column_name}" does not exist.'.format(**{
                'column_name': column
            }))

    return columns


def load_and_validate_constraints(constraints):
    global AVAILABLE_COLUMNS, AVAILABLE_OPERATORS, COLUMN_TO_TYPE
    if not AVAILABLE_COLUMNS:
        AVAILABLE_COLUMNS, AVAILABLE_OPERATORS, COLUMN_TO_TYPE = _load_column_data()

    if isinstance(constraints, str):
        try:
            constraints = json.loads(constraints)
        except:
            raise Exception('Unable to parse constraints as a list of objects with the schema {"column": null, "operator": null, "value": null}.')
    elif not isinstance(constraints, list):
        raise Exception('Unable to parse constraints as a list of objects with the schema {"column": null, "operator": null, "value": null}.')

    for constraint_idx, constraint in enumerate(constraints):
        if not isinstance(constraint, dict):
            raise Exception('Every constraint must be with the schema {"column": null, "operator": null, "value": null}.')
        for key in ['column', 'operator', 'value']:
            if key not in constraint:
                raise Exception('Constraint at index {constraint_idx} is missing "{key}" key.'.format(**{
                    'constraint_idx': constraint_idx,
                    'key': key
                }))
        if constraint['column'] not in AVAILABLE_COLUMNS:
            raise Exception('Column "{column_name}" in constraint at index {constraint_idx} does not exist.'.format(**{
                'column_name': constraint['column'],
                'constraint_idx': constraint_idx
            }))

        if constraint['operator'] not in AVAILABLE_OPERATORS[constraint['column']]:
            raise Exception('Invalid operator "{operator}" in constraint at index {constraint_idx} for {data_type} data.'.format(**{
                'operator': constraint['operator'],
                'constraint_idx': constraint_idx,
                'data_type': COLUMN_TO_TYPE[constraint['column']]
            }))

        # TODO check value?

    return constraints


def load_and_validate_order_clauses(order_clauses):
    global AVAILABLE_COLUMNS, AVAILABLE_OPERATORS, COLUMN_TO_TYPE
    if not AVAILABLE_COLUMNS:
        AVAILABLE_COLUMNS, AVAILABLE_OPERATORS, COLUMN_TO_TYPE = _load_column_data()

    if isinstance(order_clauses, str):
        try:
            order_clauses = json.loads(order_clauses)
        except:
            raise Exception('Unable to parse order clauses as a list of objects with the schema {"column": null, "order": null}.')
    elif not isinstance(order_clauses, list):
        raise Exception('Unable to parse order clauses as a list of objects with the schema {"column": null, "order": null}.')

    for order_clause_idx, order_clause in enumerate(order_clauses):
        if not isinstance(order_clause, dict):
            raise Exception('Every constraint must be with the schema {"column": null, "order": null}.')
        for key in ['column', 'order']:
            if key not in order_clause:
                raise Exception('Order clause at index {order_clause_idx} is missing "{key}" key.'.format(**{
                    'order_clause_idx': order_clause_idx,
                    'key': key
                }))
        if order_clause['column'] not in AVAILABLE_COLUMNS:
            raise Exception('Column "{column_name}" in order clause at index {order_clause_idx} does not exist.'.format(**{
                'column_name': order_clause['column'],
                'order_clause_idx': order_clause_idx
            }))
        if order_clause['order'] not in AVAILABLE_ORDERS:
            raise Exception('Can not order data in {order} order in order clause at index {order_clause_idx}.'.format(**{
                'order': order_clause['order'],
                'order_clause_idx': order_clause_idx
            }))

    return order_clauses
