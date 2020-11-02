""" Gets list of server information from CENTRALSERVER
    Stores updated list into collector_state.server_list
"""

from opmon_collector.database_manager import DatabaseManager
from opmon_collector.logger_manager import LoggerManager


def _init_server_manager(settings):
    logger_m = LoggerManager(settings['logger'], settings['xroad']['instance'])
    return DatabaseManager(
        settings['mongodb'],
        settings['xroad'],
        logger_m
    )


def update_database_server_list(settings):
    server_manager = _init_server_manager(settings)
    server_list = server_manager.get_list_from_central_server()
    if len(server_list):
        server_manager.save_server_list_to_database(server_list)
        print('- Total of {0} inserted into server_list collection.'.format(len(server_list)))
    else:
        print('- No servers found')


def print_server_list(settings):
    server_manager = _init_server_manager(settings)
    server_list = server_manager.get_list_from_central_server()
    for s in server_list:
        print(s)
