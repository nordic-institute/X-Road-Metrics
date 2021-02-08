from django.shortcuts import render
from django.http import HttpResponse
import json
import traceback

from ..logger_manager import LoggerManager
from ..api.postgresql_manager import PostgreSQL_Manager
from ..api.input_validator import OpenDataInputValidator
from ..opendata_settings_parser import OpenDataSettingsParser


def index(request, profile=None):

    settings = OpenDataSettingsParser(profile).settings
    logger = LoggerManager(settings['logger'], settings['xroad']['instance'])

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
            postgres = PostgreSQL_Manager(settings)
            column_data = get_column_data(postgres)
            min_date, max_date = postgres.get_min_and_max_dates()

            return render(request, 'gui/index.html', {
                'column_data': column_data,
                'column_count': len(column_data),
                'min_date': min_date,
                'max_date': max_date,
                'disclaimer': settings['opendata']['disclaimer'],
                'header': settings['opendata']['header'],
                'footer': settings['opendata']['footer'],
                'x_road_instance': settings['xroad']['instance'],
            })
    except:
        logger.log_error('gui_index_page_loading_failed', 'Failed loading index page. ERROR: {0}'.format(
            traceback.format_exc().replace('\n', '')
        ))
        return HttpResponse('Server encountered an error while rendering the HTML page.', status=500)


def get_datatable_frame(request, profile=None):

    settings = OpenDataSettingsParser(profile).settings
    logger = LoggerManager(settings['logger'], settings['xroad']['instance'])

    try:
        postgres = PostgreSQL_Manager(settings)
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
    except Exception:
        logger.log_error('gui_datatable_frame_loading_failed', 'Failed loading datatable frame. ERROR: {0}'.format(
            traceback.format_exc().replace('\n', '')
        ))
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
