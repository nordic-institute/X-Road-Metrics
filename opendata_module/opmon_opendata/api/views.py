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

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from gzip import GzipFile
import tarfile
from io import BytesIO
from datetime import datetime
import json
import traceback
from psycopg2 import OperationalError
from dateutil import relativedelta
import time

from .input_validator import OpenDataInputValidator

from .postgresql_manager import PostgreSQL_Manager
from ..logger_manager import LoggerManager
from ..opendata_settings_parser import OpenDataSettingsParser
from .. import __version__


def heartbeat(request, profile=None):
    settings = OpenDataSettingsParser(profile).settings
    logger = LoggerManager(settings['logger'], settings['xroad']['instance'], __version__)

    heartbeat_status = 'FAILED'
    heartbeat_message = 'Opendata heartbeat'

    try:
        PostgreSQL_Manager(settings).get_min_and_max_dates()
        heartbeat_status = 'SUCCEEDED'
    except OperationalError as operational_error:
        heartbeat_message += ' PostgreSQL error: {0}'.format(str(operational_error).replace('\n', ' '))
    except Exception as exception:
        heartbeat_message += 'Error: {0}'.format(str(exception).replace('\n', ' '))

    logger.log_heartbeat(heartbeat_message, heartbeat_status)

    http_status = 200 if heartbeat_status == 'SUCCEEDED' else 500
    return HttpResponse(json.dumps({'heartbeat': heartbeat_status}), status=http_status)


@csrf_exempt
def get_daily_logs(request, profile=None):
    settings = OpenDataSettingsParser(profile).settings
    logger = LoggerManager(settings['logger'], settings['xroad']['instance'], __version__)

    try:
        postgres = PostgreSQL_Manager(settings)
        date, columns, constraints, order_clauses = _validate_query(request, postgres, settings)
    except Exception as exception:
        logger.log_error('api_daily_logs_query_validation_failed',
                         'Failed to validate daily logs query. {0} ERROR: {1}'.format(
                             str(exception), traceback.format_exc().replace('\n', '')
                         ))
        return HttpResponse(json.dumps({'error': str(exception)}), status=400)

    try:
        gzipped_file = _generate_gzipped_file(
            postgres,
            date,
            columns,
            constraints,
            order_clauses,
            settings['opendata']['field-descriptions']
        )

        response = HttpResponse(gzipped_file, content_type='application/gzip')
        response['Content-Disposition'] = 'attachment; filename="{0:04d}-{1:02d}-{2:02d}@{3}.tar.gz"'.format(
            date.year, date.month, date.day, int(datetime.now().timestamp())
        )

        return response
    except Exception as exception:
        logger.log_error('api_daily_logs_query_failed', 'Failed retrieving daily logs. ERROR: {0}'.format(
            traceback.format_exc().replace('\n', '')
        ))
        return HttpResponse(
            json.dumps({'error': 'Server encountered error when generating gzipped tarball.'}),
            status=500
        )


@csrf_exempt
def get_preview_data(request, profile=None):
    settings = OpenDataSettingsParser(profile).settings
    logger = LoggerManager(settings['logger'], settings['xroad']['instance'], __version__)

    try:
        postgres = PostgreSQL_Manager(settings)
        date, columns, constraints, order_clauses = _validate_query(request, postgres, settings)
    except Exception as exception:
        logger.log_error('api_preview_data_query_validation_failed',
                         'Failed to validate daily preview data query. {0} ERROR: {1}'.format(
                             str(exception), traceback.format_exc().replace('\n', '')
                         ))
        return HttpResponse(json.dumps({'error': str(exception)}), status=400)

    try:
        rows, _, _ = _get_content(
            postgres,
            date,
            columns,
            constraints,
            order_clauses,
            settings['opendata']['preview-limit']
        )

        return_value = {'data': [[str(element) for element in row] for row in rows]}

        return HttpResponse(json.dumps(return_value))
    except Exception as exception:
        logger.log_error('api_preview_data_query_failed', 'Failed retrieving daily preview data. {0} ERROR: {1}'.format(
            str(exception), traceback.format_exc().replace('\n', '')
        ))
        return HttpResponse(
            json.dumps({'error': 'Server encountered error when delivering dataset sample.'}),
            status=500
        )

@csrf_exempt
def get_date_range(request, profile=None):
    settings = OpenDataSettingsParser(profile).settings
    logger = LoggerManager(settings['logger'], settings['xroad']['instance'], __version__)

    try:
        min_date, max_date = PostgreSQL_Manager(settings).get_min_and_max_dates()
        return HttpResponse(json.dumps({'date': {'min': str(min_date), 'max': str(max_date)}}))
    except Exception as exception:
        logger.log_error('api_date_range_query_failed', 'Failed retrieving date range for logs. ERROR: {0}'.format(
            traceback.format_exc().replace('\n', '')
        ))
        return HttpResponse(
            json.dumps({'error': 'Server encountered error when calculating min and max dates.'}),
            status=500
        )


@csrf_exempt
def get_column_data(request, profile=None):
    settings = OpenDataSettingsParser(profile).settings
    logger = LoggerManager(settings['logger'], settings['xroad']['instance'], __version__)

    postgres_to_python_type = {'varchar(255)': 'string', 'bigint': 'integer', 'integer': 'integer',
                               'date': 'date (YYYY-MM-DD)', 'boolean': 'boolean'}
    type_to_operators = {
        'string': ['=', '!='],
        'boolean': ['=', '!='],
        'integer': ['=', '!=', '<', '<=', '>', '>='],
        'date (YYYY-MM-DD)': ['=', '!=', '<', '<=', '>', '>='],
    }

    try:
        data = []
        field_descriptions = settings['opendata']['field-descriptions']
        for column_name in field_descriptions:
            datum = {'name': column_name}

            datum['description'] = field_descriptions[column_name]['description']
            datum['type'] = postgres_to_python_type[field_descriptions[column_name]['type']]
            datum['valid_operators'] = type_to_operators[datum['type']]
            data.append(datum)

        return HttpResponse(json.dumps({'columns': data}))
    except Exception as exception:
        logger.log_error('api_column_data_query_failed', 'Failed retrieving column data. ERROR: {0}'.format(
            traceback.format_exc().replace('\n', '')
        ))
        return HttpResponse(
            json.dumps({'error': 'Server encountered error when listing column data.'}),
            status=500
        )


def _generate_gzipped_file(postgres, date, columns, constraints, order_clauses, field_descriptions):
    rows, columns, date_columns = _get_content(postgres, date, columns, constraints, order_clauses)

    tarball_bytes = BytesIO()
    with tarfile.open(fileobj=tarball_bytes, mode='w:gz') as tarball:
        data_file, data_info = _generate_json_file(columns, rows, date_columns, date)
        meta_file, meta_info = _generate_meta_file(columns, constraints, order_clauses, date_columns,
                                                   field_descriptions)

        tarball.addfile(data_info, data_file)
        tarball.addfile(meta_info, meta_file)

    return tarball_bytes.getvalue()


def _get_content(postgres, date, columns, constraints, order_clauses, limit=None):
    constraints.append({'column': 'requestInDate', 'operator': '=', 'value': date.strftime('%Y-%m-%d')})

    column_names_and_types = postgres.get_column_names_and_types()

    if not columns:  # If no columns are specified, all must be returned
        columns = [column_name for column_name, _ in column_names_and_types]

    date_columns = [column_name for column_name, column_type in column_names_and_types
                    if column_type == 'date' and column_name in columns]
    rows = postgres.get_data(constraints=constraints, columns=columns, order_by=order_clauses, limit=limit)

    return rows, columns, date_columns


def _generate_json_file(column_names, rows, date_columns, date):
    json_content = []

    for row in rows:
        json_obj = {column_name: row[column_idx] for column_idx, column_name in enumerate(column_names)}
        for date_column in date_columns:  # Must manually convert Postgres dates to string to be compatible with JSON format
            json_obj[date_column] = datetime.strftime(json_obj[date_column], '%Y-%m-%d')

        json_content.append(json.dumps(json_obj))

    json_content.append('')  # Hack to get \n after the last JSON object
    json_file_content = ('\n'.join(json_content)).encode('utf8')

    info = tarfile.TarInfo(date.strftime('%Y-%m-%d') + '.json')
    info.size = len(json_file_content)
    info.mtime = time.time()

    return BytesIO(json_file_content), info


def _generate_meta_file(columns, constraints, order_clauses, date_columns, field_descriptions):
    if 'requestInDate' not in date_columns:
        date_columns += ['requestInDate']

    meta_dict = {}
    meta_dict['descriptions'] = {field: field_descriptions[field]['description'] for field in field_descriptions}
    meta_dict['query'] = {'fields': columns, 'constraints': constraints,
                          'order_by': [' '.join(order_clause) for order_clause in order_clauses]}

    content = json.dumps(meta_dict).encode('utf8')

    info = tarfile.TarInfo('meta.json')
    info.size = len(content)
    info.mtime = time.time()

    return BytesIO(content), info


def _gzip_content(content):
    output_bytes = BytesIO()

    with GzipFile(fileobj=output_bytes, mode='wb') as gzip_file:
        input_bytes = BytesIO(content.encode('utf8'))
        gzip_file.writelines(input_bytes)

    return output_bytes.getvalue()


def _validate_query(request, postgres, settings):
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
