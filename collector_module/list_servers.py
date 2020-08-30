import argparse

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

    parser = argparse.ArgumentParser()
    parser.add_argument("central_server",
                        help="The Name/IP of Central server can be found in configuration anchor")
    parser.add_argument("--timeout", type=int, default=10,
                        help="Time out value")

    args = parser.parse_args()
    central_server = args.central_server
    timeout = args.timeout

    server_list = server_m.get_list_from_central_server(central_server, timeout)
    for s in server_list:
        print(s)


if __name__ == '__main__':
    main()
