""" Gets list of server information from CENTRALSERVER
    Stores updated list into collector_state.server_list
"""

from collectorlib.database_manager import DatabaseManager
from collectorlib.logger_manager import LoggerManager


def _get_server_list(settings):
    logger_m = LoggerManager(settings['logger'], settings['xroad']['instance'])
    server_m = DatabaseManager(
        settings['mongodb'],
        settings['xroad']['instance'],
        logger_m
    )

    central_server = settings['xroad']['central-server']
    return server_m.get_list_from_central_server(
        central_server['url'],
        central_server['timeout']
    )


def update_database_server_list(settings):
    server_list = _get_server_list(settings)
    if len(server_list):
        server_m.stores_server_list_database(server_list)
        print('- Total of {0} inserted into server_list collection.'.format(len(server_list)))
    else:
        print('- No servers found')


def print_server_list(settings):
    server_list = _get_server_list(settings)
    for s in server_list:
        print(s)
