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
from typing import Sequence, TypedDict

from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render

from opmon_opendata import __version__
from opmon_opendata.api.input_validator import OpenDataInputValidator
from opmon_opendata.api.postgresql_manager import PostgreSQL_LogManager
from opmon_opendata.logger_manager import LoggerManager
from opmon_opendata.opendata_settings_parser import OpenDataSettingsParser


class OperatorChoice(TypedDict):
    name: str
    value: str


def get_settings(profile):
    profile_suffix = f'-{profile}' if profile else ''
    cache_key = f'xroad-metrics-opendata-settings{profile_suffix}'
    if cache_key not in cache:
        settings = OpenDataSettingsParser(profile).settings
        cache.add(cache_key, settings)

    return cache.get(cache_key)


def index(request, profile=None):
    settings = get_settings(profile)
    logger = LoggerManager(settings['logger'], settings['xroad']['instance'], __version__)

    try:
        if settings['opendata']['maintenance-mode']:
            return render(
                request,
                'gui/maintenance.html',
                {
                    'x_road_instance': settings['xroad']['instance'],
                    'settings_profile': profile or ''
                }
            )
        else:
            postgres = PostgreSQL_LogManager(settings)
            column_data = get_column_data(postgres)
            min_date, max_date = postgres.get_min_and_max_dates()

            return render(request, 'gui/index.html', {
                'column_data': column_data,
                'column_count': len(column_data),
                'initial_constraint_operators': get_constraint_operators_choices(column_data[0]['type']) if column_data else [],
                'min_date': min_date,
                'max_date': max_date,
                'disclaimer': settings['opendata']['disclaimer'],
                'header': settings['opendata']['header'],
                'footer': settings['opendata']['footer'],
                'x_road_instance': settings['xroad']['instance'],
            })
    except Exception as e:
        logger.log_exception('gui_index_page_loading_failed', f'Failed loading index page. ERROR: {str(e)}')
        return HttpResponse('Server encountered an error while rendering the HTML page.', status=500)


def get_datatable_frame(request, profile=None):
    settings = get_settings(profile)
    logger = LoggerManager(settings['logger'], settings['xroad']['instance'], __version__)

    try:
        postgres = PostgreSQL_LogManager(settings)
        validator = OpenDataInputValidator(postgres, settings)
        columns = validator.load_and_validate_columns(request.GET.get('columns', '[]'))
    except Exception as exception:
        return HttpResponse(json.dumps({'error': str(exception)}), status=400)

    try:
        if not columns:
            column_data = get_column_data(postgres)
            columns = [column_datum['name'] for column_datum in column_data]

        return render(
            request,
            'gui/datatable.html',
            {
                'columns': [
                    {
                        'name': column_name,
                        'desc': settings['opendata']['field-descriptions'][column_name]['description']
                    }
                    for column_name in columns
                ]
            }
        )
    except Exception as e:
        logger.log_exception('gui_datatable_frame_loading_failed', f'Failed loading datatable frame. ERROR: {str(e)}')
        return HttpResponse('Server encountered an error while rendering the datatable frame.', status=500)


def get_column_data(postgres):
    raw_type_to_type = {
        'integer': 'numeric',
        'character varying': 'categorical',
        'date': 'numeric',
        'bigint': 'numeric',
        'boolean': 'categorical'
    }

    return [{'name': column_name, 'type': raw_type_to_type[column_type]}
            for column_name, column_type in postgres.get_column_names_and_types()]


def get_constraint_operators_choices(operator_type: str) -> Sequence[OperatorChoice]:
    operators = [{'name': 'equal', 'value': '='}, {'name': 'not equal', 'value': '!='}]
    numerical_operators = [
        {'name': 'less than', 'value': '<'},
        {'name': 'greater than', 'value': '>'},
        {'name': 'less than or equal to', 'value': '<='},
        {'name': 'greater than or equal to', 'value': '>='},
    ]
    if operator_type == 'numeric':
        operators.extend(numerical_operators)
    return operators
