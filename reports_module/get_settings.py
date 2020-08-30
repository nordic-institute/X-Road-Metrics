import sys

import settings
from reportslib.logger_manager import LoggerManager

if __name__ == '__main__':
    """
    Prints (returns) values from the settings file for the bash files.
    """
    args = sys.argv

    if args[1] == 'INSTANCE':
        print(settings.INSTANCE)
    elif args[1] == 'MONGODB_SUFFIX':
        print(settings.MONGODB_SUFFIX)
    elif args[1] == 'REPORTS_PATH':
        reports_path = settings.REPORTS_PATH
        if reports_path.endswith("/"):
            reports_path += settings.INSTANCE + "/"
        else:
            reports_path = reports_path + "/" + settings.INSTANCE + "/"
        print(reports_path)
    elif args[1] == 'REPORTS_TARGET':
        print(settings.REPORTS_TARGET)
    elif args[1] == 'FACTSHEET_PATH':
        factsheet_path = settings.FACTSHEET_PATH
        if factsheet_path.endswith("/"):
            print(settings.FACTSHEET_PATH)
        else:
            print(settings.FACTSHEET_PATH + "/")
    elif args[1] == 'FACTSHEET_TARGET':
        print(settings.FACTSHEET_TARGET)
    elif args[1] == 'BASE_FILE_LOCATION':
        interannual_factsheet_path = settings.BASE_FILE_LOCATION
        if interannual_factsheet_path.endswith("/"):
            print(settings.BASE_FILE_LOCATION)
        else:
            print(settings.BASE_FILE_LOCATION + "/")
    elif args[1] == 'BASE_FILE_NAME':
        print(settings.BASE_FILE_NAME)
    elif args[1] == 'INTERANNUAL_FACTSHEET_TARGET':
        print(settings.INTERANNUAL_FACTSHEET_TARGET)
    else:
        logger_m = LoggerManager(settings.LOGGER_NAME, 'reports_module')
        logger_m.log_error('getting_settings', "Invalid argument for get_settings")
        logger_m.log_heartbeat("Invalid argument for get_settings", settings.HEARTBEAT_LOGGER_PATH,
                               settings.REPORT_HEARTBEAT_NAME, "FAILED")
        raise ValueError("Invalid argument for get_settings")
