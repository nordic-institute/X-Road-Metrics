""" Gets list of server information from CENTRALSERVER
    Stores updated list into collector_state.server_list
"""

from .collectorlib.database_manager import DatabaseManager
from .collectorlib.logger_manager import LoggerManager
from . import settings


def main():
    logger_m = LoggerManager(settings.LOGGER_NAME, settings.MODULE)
    server_m = DatabaseManager(settings.MONGODB_SUFFIX,
                               settings.MONGODB_SERVER,
                               settings.MONGODB_USER,
                               settings.MONGODB_PWD,
                               logger_m)

    central_server = settings.CENTRAL_SERVER
    timeout = settings.CENTRAL_SERVER_TIMEOUT
    server_list = server_m.get_list_from_central_server(central_server, timeout)

    if len(server_list):
        server_m.stores_server_list_database(server_list)
        print('- Total of {0} inserted into server_list collection.'.format(len(server_list)))
    else:
        print('- No servers found')


if __name__ == '__main__':
    main()
