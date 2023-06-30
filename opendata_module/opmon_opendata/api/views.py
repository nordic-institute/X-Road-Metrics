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
import json
from datetime import datetime
from typing import Optional

from django.core.cache import cache
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, StreamingHttpResponse
from django.utils.html import escape
from django.views.decorators.csrf import csrf_exempt
from psycopg2 import OperationalError

from opmon_opendata import __version__
from opmon_opendata.api import helpers
from opmon_opendata.api.forms import HarvestForm
from opmon_opendata.api.postgresql_manager import PostgreSQL_Manager
from opmon_opendata.logger_manager import LoggerManager
from opmon_opendata.opendata_settings_parser import OpenDataSettingsParser


def get_settings(profile):
    profile_suffix = f'-{profile}' if profile else ''
    cache_key = f'xroad-metrics-opendata-settings{profile_suffix}'
    if cache_key not in cache:
        settings = OpenDataSettingsParser(profile).settings
        cache.add(cache_key, settings)

    return cache.get(cache_key)


def heartbeat(request, profile=None):
    settings = get_settings(profile)
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
    settings = get_settings(profile)
    logger = LoggerManager(settings['logger'], settings['xroad']['instance'], __version__)

    try:
        postgres = PostgreSQL_Manager(settings)
        date, columns, constraints, order_clauses = helpers.validate_query(request, postgres, settings)
    except Exception as e:
        logger.log_exception('api_daily_logs_query_validation_failed',
                             f'Failed to validate daily logs query. ERROR: {str(e)}'
                             )
        return HttpResponse(json.dumps({'error': escape(str(e))}), status=400)

    try:
        gzipped_file_stream = helpers.generate_ndjson_stream(
            postgres,
            date,
            columns,
            constraints,
            order_clauses,
            settings
        )

        response = StreamingHttpResponse(gzipped_file_stream, content_type='application/gzip')
        response['Content-Disposition'] = 'attachment; filename="{0:04d}-{1:02d}-{2:02d}@{3}.json.gz"'.format(
            date.year, date.month, date.day, int(datetime.now().timestamp())
        )
        return response
    except Exception as e:
        logger.log_exception('api_daily_logs_query_failed',
                             f'Failed retrieving daily logs. ERROR: {str(e)}')
        return HttpResponse(
            json.dumps({'error': 'Server encountered error when generating gzipped tarball.'}),
            status=500
        )


@csrf_exempt
def get_harvest_data(request: WSGIRequest, profile: Optional[str] = None) -> HttpResponse:
    """
    Return a JSON response containing harvested data from a PostgreSQL database.

    :param request: A Django request object representing the HTTP GET request.
    :param profile: A string representing the profile to use for harvesting. Default is None.

    :return: A JSON response. If an error occurs, an error message is returned in the response.
    """

    if request.method != 'GET':
        return HttpResponse(
            json.dumps({'error': 'The requested method is not allowed for the requested resource'}),
            status=405,
            content_type='application/json'
        )

    settings = get_settings(profile)
    logger = LoggerManager(settings['logger'], settings['xroad']['instance'], __version__)
    postgres = PostgreSQL_Manager(settings)
    form = HarvestForm(request.GET)

    if not form.is_valid():
        form_validation_failed_msg = 'api_get_harvest_input_validation_failed'
        for field, errors in form.errors.items():
            for error in errors:
                logger.log_error(form_validation_failed_msg, f'{field}: {error}')

        return HttpResponse(
            json.dumps({'errors': form.errors}),
            status=400,
            content_type='application/json'
        )

    cleaned_data = form.cleaned_data

    from_dt = cleaned_data['from_dt']
    until_dt = cleaned_data.get('until_dt')
    limit = cleaned_data.get('limit')
    offset = cleaned_data.get('offset')
    from_row_id = cleaned_data.get('from_row_id')

    order_by = None
    if cleaned_data.get('order'):
        order: helpers.OrderByType = cleaned_data['order']
        order_by = [order]
    try:
        rows, columns, total_query_count_data = (
            helpers.get_harvest_rows(
                postgres,
                from_dt,
                until_dt=until_dt,
                limit=limit,
                offset=offset,
                from_row_id=from_row_id,
                order_by=order_by
            )
        )
    except Exception as exec_info:
        logger.log_exception('api_get_harvest_query_failed', str(exec_info))
        return HttpResponse(
            json.dumps({'error': 'Server encountered error when getting harvest data.'}),
            content_type='application/json',
            status=500
        )

    data = [[escape(str(element)) for element in row] for row in rows]
    total_query_count = total_query_count_data[0] if rows else 0
    limit = limit or 0
    offset = offset or 0
    from_range, to_range = helpers.get_harvest_row_range(len(data), offset)
    return_value = {
        'data': data,
        'columns': columns if rows else [],
        'total_query_count': total_query_count,
        'timestamp_tz_offset': from_dt.strftime('%z'),
        'limit': limit,
        'row_range': f'{from_range}-{to_range}'
    }

    logger.log_info('api_get_harvest_response_success', f'returning {len(rows)} rows')
    return HttpResponse(json.dumps(return_value), content_type='application/json')


@csrf_exempt
def get_daily_logs_meta(request, profile=None):
    settings = get_settings(profile)
    logger = LoggerManager(settings['logger'], settings['xroad']['instance'], __version__)

    try:
        postgres = PostgreSQL_Manager(settings)
        date, columns, constraints, order_clauses = helpers.validate_query(request, postgres, settings)
    except Exception as e:
        logger.log_exception('api_daily_logs_meta_query_validation_failed',
                             f'Failed to validate daily logs meta query. ERROR: {str(e)}')
        return HttpResponse(json.dumps({'error': escape(str(e))}), status=400)

    try:
        meta_file = helpers.generate_meta_file(
            postgres,
            columns,
            constraints,
            order_clauses,
            settings['opendata']['field-descriptions']
        )

        response = HttpResponse(meta_file, content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="{0:04d}-{1:02d}-{2:02d}@{3}.meta.json"'.format(
            date.year, date.month, date.day, int(datetime.now().timestamp())
        )

        return response
    except Exception as e:
        logger.log_exception('api_daily_logs_meta_query_failed',
                             f'Failed retrieving daily logs meta. ERROR: {str(e)}')
        return HttpResponse(
            json.dumps({'error': 'Server encountered error when generating meta file.'}),
            status=500
        )


@csrf_exempt
def get_preview_data(request, profile=None):
    settings = get_settings(profile)
    logger = LoggerManager(settings['logger'], settings['xroad']['instance'], __version__)

    try:
        postgres = PostgreSQL_Manager(settings)
        date, columns, constraints, order_clauses = helpers.validate_query(request, postgres, settings)
    except Exception as e:
        logger.log_exception('api_preview_data_query_validation_failed',
                             f'Failed to validate daily preview data query. ERROR: {str(e)}')
        return HttpResponse(json.dumps({'error': escape(str(e))}), status=400)

    try:
        rows, _, _ = helpers.get_content(
            postgres,
            date,
            columns,
            constraints,
            order_clauses,
            settings['opendata']['preview-limit']
        )

        return_value = {'data': [[escape(str(element)) for element in row] for row in rows]}

        return HttpResponse(json.dumps(return_value))
    except Exception as e:
        logger.log_exception('api_preview_data_query_failed',
                             f'Failed retrieving daily preview data. ERROR: {str(e)}')
        return HttpResponse(
            json.dumps({'error': 'Server encountered error when delivering dataset sample.'}),
            status=500
        )


@csrf_exempt
def get_date_range(request, profile=None):
    settings = get_settings(profile)
    logger = LoggerManager(settings['logger'], settings['xroad']['instance'], __version__)

    try:
        min_date, max_date = PostgreSQL_Manager(settings).get_min_and_max_dates()
        return HttpResponse(json.dumps({'date': {'min': str(min_date), 'max': str(max_date)}}))
    except Exception as e:
        logger.log_exception('api_date_range_query_failed',
                             f'Failed retrieving date range for logs. ERROR: {str(e)}')
        return HttpResponse(
            json.dumps({'error': 'Server encountered error when calculating min and max dates.'}),
            status=500
        )


@csrf_exempt
def get_column_data(request, profile=None):
    settings = get_settings(profile)
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
    except Exception as e:
        logger.log_exception('api_column_data_query_failed',
                             f'Failed retrieving column data. ERROR: {str(e)}')
        return HttpResponse(
            json.dumps({'error': 'Server encountered error when listing column data.'}),
            status=500
        )
