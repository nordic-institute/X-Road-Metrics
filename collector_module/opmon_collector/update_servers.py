""" Gets list of server information from CENTRALSERVER
    Stores updated list into collector_state.server_list
"""

from .central_server_client import CentralServerClient
from .database_manager import DatabaseManager
from .logger_manager import LoggerManager
from .pid_file_handler import OpmonPidFileHandler
from . import __version__


def _init_clients(settings, logger_m):
    cs_client = CentralServerClient(settings['xroad'], logger_m)
    db_client = DatabaseManager(settings['mongodb'], settings['xroad']['instance'], logger_m)
    return cs_client, db_client


def update_database_server_list(settings):
    logger_m = LoggerManager(settings['logger'], settings['xroad']['instance'], __version__)

    try:
        OpmonPidFileHandler(settings).create_pid_file()
    except RuntimeError as e:
        logger_m.log_error('update_database_server_list', str(e))
        raise e

    cs_client, db_client = _init_clients(settings, logger_m)
    server_list = cs_client.get_security_servers()
    if len(server_list):
        db_client.save_server_list_to_database(server_list)
        logger_m.log_info(
            'update_database_server_list',
            '- Total of {0} inserted into server_list collection.'.format(len(server_list))
        )
    else:
        logger_m.log_info('update_database_server_list', '- No servers found')


def print_server_list(settings):
    logger_m = LoggerManager(settings['logger'], settings['xroad']['instance'], __version__)
    cs_client, _ = _init_clients(settings, logger_m)
    server_list = cs_client.get_security_servers()
    for s in server_list:
        print(s)
