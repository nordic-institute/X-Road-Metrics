""" Gets list of server information from CENTRALSERVER
    Stores updated list into collector_state.server_list
"""

from opmon_collector.central_server_client import CentralServerClient
from opmon_collector.database_manager import DatabaseManager
from opmon_collector.logger_manager import LoggerManager


def _init_clients(settings):
    logger_m = LoggerManager(settings['logger'], settings['xroad']['instance'])
    cs_client = CentralServerClient(settings['xroad'], logger_m)
    db_client = DatabaseManager(settings['mongodb'], settings['xroad']['instance'], logger_m)
    return cs_client, db_client


def update_database_server_list(settings):
    cs_client, db_client = _init_clients(settings)
    server_list = cs_client.get_security_servers()
    if len(server_list):
        db_client.save_server_list_to_database(server_list)
        print('- Total of {0} inserted into server_list collection.'.format(len(server_list)))
    else:
        print('- No servers found')


def print_server_list(settings):
    cs_client, _ = _init_clients(settings)
    server_list = cs_client.get_security_servers()
    for s in server_list:
        print(s)
