from django.shortcuts import render
from django.http import HttpResponse
import json
import traceback
from psycopg2 import OperationalError

from api.postgresql_manager import PostgreSQL_Manager
from api.input_validator import load_and_validate_columns
from interface.settings import DISCLAIMER, POSTGRES_CONFIG, FIELD_DESCRIPTIONS, HEARTBEAT, BASE_DIR,\
    HEADER, FOOTER, X_ROAD_INSTANCE, LOG, LOGS_TIME_BUFFER, IN_MAINTENANCE

import time
import threading

from logger_manager import LoggerManager, setup_logger

raw_type_to_type = {'integer': 'numeric', 'character varying': 'categorical', 'date': 'numeric', 'bigint': 'numeric', 'boolean': 'categorical'}
PGM = PostgreSQL_Manager(POSTGRES_CONFIG, FIELD_DESCRIPTIONS.keys(), LOGS_TIME_BUFFER)

LOGGER = LoggerManager(logger_name='opendata-interface', module_name='opendata',
                       heartbeat_dir=HEARTBEAT['dir'])


def heartbeat():
    while True:
        try:
            PGM.get_min_and_max_dates()
            LOGGER.log_heartbeat('Scheduled heartbeat', HEARTBEAT['gui_file'], 'SUCCEEDED')
        except OperationalError as operational_error:
            LOGGER.log_heartbeat('PostgreSQL error: {0}'.format(str(operational_error).replace('\n', ' ')),
                                 HEARTBEAT['gui_file'], 'FAILED')
        except Exception as exception:
            LOGGER.log_heartbeat('Error: {0}'.format(str(exception).replace('\n', ' ')),
                                 HEARTBEAT['gui_file'], 'FAILED')

        time.sleep(HEARTBEAT['interval'])

heartbeat_thread = threading.Thread(target=heartbeat)
heartbeat_thread.daemon = True
heartbeat_thread.start()


def index(request):
    try:
        if IN_MAINTENANCE:
            return render(request, 'gui/maintenance.html', {'x_road_instance': X_ROAD_INSTANCE})
        else:
            column_data = get_column_data()
            min_date, max_date = PGM.get_min_and_max_dates()

            return render(request, 'gui/index.html', {
                'column_data': column_data, 'column_count': len(column_data), 'min_date': min_date,
                'max_date': max_date, 'disclaimer': DISCLAIMER, 'header': HEADER, 'footer': FOOTER,
                'x_road_instance': X_ROAD_INSTANCE
            })
    except:
        LOGGER.log_error('gui_index_page_loading_failed', 'Failed loading index page. ERROR: {0}'.format(
            traceback.format_exc().replace('\n', '')
        ))
        return HttpResponse('Server encountered an error while rendering the HTML page.', status=500)


def get_datatable_frame(request):
    try:
        columns = load_and_validate_columns(request.GET.get('columns', '[]'))
    except Exception as exception:
        return HttpResponse(json.dumps({'error': str(exception)}), status=400)

    try:
        if not columns:
            column_data = get_column_data()
            columns = [column_datum['name'] for column_datum in column_data]

        return render(
            request,
            'gui/datatable.html',
            {
                'columns': [
                    {
                        'name': column_name,
                        'desc': FIELD_DESCRIPTIONS[column_name]['description']
                    }
                    for column_name in columns
                ]
            }
        )
    except:
        LOGGER.log_error('gui_datatable_frame_loading_failed', 'Failed loading datatable frame. ERROR: {0}'.format(
            traceback.format_exc().replace('\n', '')
        ))
        return HttpResponse('Server encountered an error while rendering the datatable frame.', status=500)


def get_column_data():
    return [{'name': column_name, 'type': raw_type_to_type[column_type]}
            for column_name, column_type in PGM.get_column_names_and_types()]
