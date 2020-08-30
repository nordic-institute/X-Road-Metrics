import sys

import settings
from collectorlib.logger_manager import LoggerManager

if __name__ == '__main__':
    """
    Prints (returns) values from the settings file for the bash files.
    """
    args = sys.argv

    if args[1] == 'MODULE':
        print(settings.MODULE)
    elif args[1] == 'APPDIR':
        print(settings.APPDIR)
    elif args[1] == 'INSTANCE':
        print(settings.INSTANCE)
    elif args[1] == 'MONGODB_USER':
        print(settings.MONGODB_USER)
    elif args[1] == 'MONGODB_PWD':
        print(settings.MONGODB_PWD)
    elif args[1] == 'MONGODB_SERVER':
        print(settings.MONGODB_SERVER)
    elif args[1] == 'MONGODB_SUFFIX':
        print(settings.MONGODB_SUFFIX)
    elif args[1] == 'CENTRAL_SERVER':
        print(settings.CENTRAL_SERVER)
    elif args[1] == 'CENTRAL_SERVER_TIMEOUT':
        print(settings.CENTRAL_SERVER_TIMEOUT)
    elif args[1] == 'SECURITY_SERVER_URL':
        print(settings.SECURITY_SERVER_URL)
    elif args[1] == 'SECURITY_SERVER_TIMEOUT':
        print(settings.SECURITY_SERVER_TIMEOUT)
    else:
        logger_m = LoggerManager(settings.LOGGER_NAME, settings.MODULE)
        logger_m.log_error('getting_settings', "Invalid argument for get_settings: " + str(args[1]))
        logger_m.log_heartbeat("Invalid argument for get_settings: " + str(args[1]), settings.HEARTBEAT_PATH,
                               settings.HEARTBEAT_FILE, "FAILED")
        raise ValueError("Invalid argument for get_settings")
