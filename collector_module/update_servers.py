""" Gets list of server information from CENTRALSERVER
    Stores updated list into collector_state.server_list
"""

from collectorlib.database_manager import DatabaseManager
from collectorlib.logger_manager import LoggerManager


def main(settings, args=None):

    logger_m = LoggerManager(settings['logger'], settings['xroad']['instance'])
    server_m = DatabaseManager(
        settings['mongodb'],
        settings['xroad']['instance'],
        logger_m
    )

    central_server = settings['xroad']['central-server']
    server_list = server_m.get_list_from_central_server(
        central_server['url'],
        central_server['timeout']
    )

    if len(server_list):
        server_m.stores_server_list_database(server_list)
        print('- Total of {0} inserted into server_list collection.'.format(len(server_list)))
    else:
        print('- No servers found')
