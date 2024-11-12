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
from gzip import GzipFile
from io import BytesIO
import json
from typing import Dict, Generator, List, Optional, Tuple, TypedDict

from dateutil import relativedelta
from django.core.handlers.wsgi import WSGIRequest
import psycopg2

from opmon_opendata.api.input_validator import OpenDataInputValidator
from opmon_opendata.api.postgresql_manager import PostgreSQL_LogManager

DEFAULT_STREAM_BUFFER_LINES = 1000


class OrderByType(TypedDict):
    column: str
    order: str


class ConstraintMetaType(TypedDict):
    name: str
    description: str
    type: str
    valid_operators: List[str]


def generate_ndjson_stream(postgres: PostgreSQL_LogManager, date: datetime,
                           columns: List[str], constraints: List[dict],
                           order_clauses: List[dict], settings: dict) -> Generator[bytes, None, None]:
    """Creates a gzipped ndjson file iterator suitable for StreamingHttpResponse."""

    data_cursor, column_names, date_columns = _get_content_cursor(postgres, date, columns, constraints, order_clauses)

    gzip_buffer = BytesIO()
    with GzipFile(fileobj=gzip_buffer, mode='wb') as gzip_file:
        count = 0
        buffer_size = settings['opendata'].get('stream-buffer-lines', DEFAULT_STREAM_BUFFER_LINES)
        for row in data_cursor:
            json_obj = {column_name: row[column_idx] for column_idx, column_name in enumerate(column_names)}
            # Must manually convert Postgres dates to string to be compatible with JSON format
            for date_column in date_columns:
                json_obj[date_column] = datetime.strftime(json_obj[date_column], '%Y-%m-%d')
            gzip_file.write(bytes(json.dumps(json_obj), 'utf-8'))
            gzip_file.write(b'\n')
            count += 1
            if count == buffer_size:
                count = 0
                data = gzip_buffer.getvalue()
                data_len = len(data)
                if data_len:
                    # Yield current buffer
                    yield data
                    # Empty buffer to free memory
                    gzip_buffer.truncate(0)
                    gzip_buffer.seek(0)
    # Final data gets written when GzipFile is closed
    yield gzip_buffer.getvalue()


def get_content(postgres: PostgreSQL_LogManager, date: datetime, columns: List[str],
                constraints: List[dict], order_clauses: List[dict],
                limit: Optional[int] = None) -> Tuple[List[Tuple], List[str], List[str]]:
    data_cursor, columns, date_columns = _get_content_cursor(
        postgres, date, columns, constraints, order_clauses, limit=limit)
    return data_cursor.fetchall(), columns, date_columns


def _get_content_cursor(postgres: PostgreSQL_LogManager, date: datetime, columns: List[str],
                        constraints: List[dict], order_clauses: List[dict],
                        limit: Optional[int] = None) -> Tuple[psycopg2.extensions.cursor, List[str], List[str]]:
    constraints.append({'column': 'requestInDate', 'operator': '=', 'value': date.strftime('%Y-%m-%d')})

    column_names_and_types = postgres.get_column_names_and_types()

    if not columns:  # If no columns are specified, all must be returned
        columns = [column_name for column_name, _ in column_names_and_types]

    date_columns = [column_name for column_name, column_type in column_names_and_types
                    if column_type == 'date' and column_name in columns]
    data_cursor = postgres.get_data_cursor(
        constraints=constraints, columns=columns, order_by=order_clauses, limit=limit)

    return data_cursor, columns, date_columns


def generate_meta_file(postgres: PostgreSQL_LogManager, columns: List[str],
                       constraints: List[dict], order_clauses: List[dict], field_descriptions: dict) -> bytes:
    column_names_and_types = postgres.get_column_names_and_types()

    if not columns:  # If no columns are specified, all must be returned
        columns = [column_name for column_name, _ in column_names_and_types]

    meta_dict = {}
    meta_dict['descriptions'] = {field: field_descriptions[field]['description'] for field in field_descriptions}
    meta_dict['query'] = {'fields': columns, 'constraints': constraints,
                          'order_by': [' '.join(order_clause) for order_clause in order_clauses]}

    content = json.dumps(meta_dict).encode('utf8')

    return content


def validate_query(request: WSGIRequest, postgres: PostgreSQL_LogManager,
                   settings: dict) -> Tuple[datetime, List[str], List[dict], List[dict]]:
    if request.method == 'GET':
        request_data = request.GET
    else:
        request_data = json.loads(request.body.decode('utf8'))

    date_str = request_data.get('date', '')
    logs_time_buffer = relativedelta.relativedelta(days=settings['opendata']['delay-days'])

    validator = OpenDataInputValidator(postgres, settings)

    return (
        validator.load_and_validate_date(date_str, logs_time_buffer),
        validator.load_and_validate_columns(request_data.get('columns', '[]')),
        validator.load_and_validate_constraints(request_data.get('constraints', '[]')),
        validator.load_and_validate_order_clauses(request_data.get('order-clauses', '[]'))
    )


def get_harvest_row_range(total_rows: int, offset: int) -> Tuple[int, int]:
    """
    Get the range of rows to be harvested based on the total rows and offset.
    Args:
        total_rows (int): The total number of rows returned by the query.
        offset (int): The number of rows to skip before starting to harvest.

    Returns:
        Tuple[int, int]: A tuple of two integers representing the range of rows to harvest.
        The first integer is the starting row index (inclusive), and the second integer is the ending row index (exclusive).

    Raises:
        None.
    Example:
        >>> get_harvest_row_range(10, 2)
        (3, 12)
    """  # noqa
    if total_rows:
        if offset:
            range_from = offset + 1
        else:
            range_from = 1
    else:
        range_from = 0

    range_to = total_rows
    if offset:
        range_to = total_rows + offset + 1
    return range_from, range_to


def get_harvest_rows(
    postgres: PostgreSQL_LogManager,
    from_dt: datetime,
    until_dt: Optional[datetime] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    from_row_id: Optional[int] = None,
    order_by: Optional[List[OrderByType]] = None
) -> Tuple[List[Tuple], List[str], Tuple[int]]:
    """
    Retrieve harvested data from a PostgreSQL database based on the provided parameters.

    :param postgres: A PostgreSQL_LogManager object representing the connection to the PostgreSQL database.
    :param from_dt: A datetime object representing the start date/time for the harvest.
    :param until_dt: A datetime object representing the end date/time for the harvest. Default is None.
    :param limit: An integer representing the maximum number of rows to return. Default is None.
    :param offset: An integer representing the offset for the returned rows. Default is None.
    :param from_row_id: A integer representing the start row id for the harvest. Default is None.
    :param order_by: A list of dictionaries representing the column and order to use for sorting the results. Default is None.

    :return: A tuple of list of tuples representing the harvested data from the PostgreSQL database.
    If an error occurs, an empty list is returned.
    """
    if not order_by:
        order_by = [
            {'column': 'requestints', 'order': 'ASC'},
            {'column': 'id', 'order': 'ASC'}
        ]
    constraints = [
        {
            'column': 'requestints',
            'operator': '>=',
            # Convert the datetime object to a Unix timestamp in milliseconds
            'value': int(from_dt.timestamp() * 1000)
        }
    ]
    if until_dt:
        constraints.append(
            {
                'column': 'requestints',
                'operator': '<',
                # Convert the datetime object to a Unix timestamp in milliseconds
                'value': int(until_dt.timestamp() * 1000)
            }
        )

    if from_row_id:
        constraints.append(
            {
                'column': 'id',
                'operator': '>',
                'value': int(from_row_id)
            }
        )

    column_names_and_types = postgres.get_column_names_and_types()

    columns = [column_name for column_name, _ in column_names_and_types]

    total_query_count = postgres.get_rows_count(constraints)

    data_cursor = postgres.get_data_cursor(
        constraints=constraints, columns=columns, order_by=order_by, limit=limit, offset=offset)

    return data_cursor.fetchall(), columns, total_query_count


def prepare_data_columns(field_descriptions: Dict[str, Dict[str, str]]) -> List[ConstraintMetaType]:
    """
    Prepares data columns based on the field descriptions.

    :param field_descriptions: A dictionary containing field descriptions.
    :return: A list of ConstraintMetaType objects representing the prepared data columns.
    """
    postgres_to_python_type = {'varchar(255)': 'string', 'bigint': 'integer', 'integer': 'integer',
                               'date': 'date (YYYY-MM-DD)', 'boolean': 'boolean'}
    type_to_operators = {
        'string': ['=', '!='],
        'boolean': ['=', '!='],
        'integer': ['=', '!=', '<', '<=', '>', '>='],
        'date (YYYY-MM-DD)': ['=', '!=', '<', '<=', '>', '>='],
    }

    data = []
    for column_name in field_descriptions:
        column_type = postgres_to_python_type[field_descriptions[column_name]['type']]
        datum: ConstraintMetaType = {
            'name': column_name,
            'description': field_descriptions[column_name]['description'],
            'type': column_type,
            'valid_operators': type_to_operators[column_type]
        }
        data.append(datum)
    return data
