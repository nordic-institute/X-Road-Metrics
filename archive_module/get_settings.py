import sys

import settings

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
    elif args[1] == 'MONGODB_SERVER':
        print(settings.MONGODB_SERVER)
    elif args[1] == 'MONGODB_PORT':
        print(str(settings.MONGODB_PORT))
    elif args[1] == 'MONGODB_USER':
        print(settings.MONGODB_USER)
    elif args[1] == 'MONGODB_PWD':
        print(settings.MONGODB_PWD)
    elif args[1] == 'MONGODB_QUERY_DB':
        print(settings.MONGODB_QUERY_DB)
    elif args[1] == 'MONGODB_AUTH_DB':
        print(settings.MONGODB_AUTH_DB)
    # elif args[1] == 'MONGODB_SUFFIX':
    #     print(settings.MONGODB_SUFFIX)
    elif args[1] == 'MINIMUM_TO_ARCHIVE':
        print(str(settings.MINIMUM_TO_ARCHIVE))
    elif args[1] == 'TOTAL_TO_ARCHIVE':
        print(str(settings.TOTAL_TO_ARCHIVE))
    elif args[1] == 'RAW_MESSAGES_ARCHIVE_DIR':
        print(settings.RAW_MESSAGES_ARCHIVE_DIR)
    elif args[1] == 'CLEAN_DATA_ARCHIVE_DIR':
        print(settings.CLEAN_DATA_ARCHIVE_DIR)
    elif args[1] == 'LOGGER_PATH':
        print(settings.LOGGER_PATH)
    elif args[1] == 'LOGGER_FILE':
        print(settings.LOGGER_FILE)
    elif args[1] == 'HEARTBEAT_PATH':
        print(settings.HEARTBEAT_PATH)
    else:
        # logger_m = LoggerManager(settings.LOGGER_NAME, settings.MODULE)
        # logger_m.log_error('getting_settings', "Invalid argument for get_settings: " + str(args[1]))
        # logger_m.log_heartbeat("Invalid argument for get_settings: " + str(args[1]), settings.HEARTBEAT_PATH,
        #                        settings.HEARTBEAT_FILE, "FAILED")
        raise ValueError("Invalid argument " + str(args[1]) + " for get_settings")

