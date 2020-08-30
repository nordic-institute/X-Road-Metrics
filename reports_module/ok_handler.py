import sys

import settings
from reportslib.logger_manager import LoggerManager

if __name__ == '__main__':
    """
    The status handler for handling bash script status and to log into heartbeat & log.
    """
    args = sys.argv
    msg = ' '.join(args)

    # logger_m = LoggerManager(settings.LOGGER_NAME, settings.MODULE)
    logger_m = LoggerManager(settings.LOGGER_NAME, 'reports_module')
    logger_m.log_info(args[0], msg)
    # logger_m.log_heartbeat(msg, settings.HEARTBEAT_PATH, settings.HEARTBEAT_FILE, "SUCCEEDED")
    logger_m.log_heartbeat(msg, settings.HEARTBEAT_LOGGER_PATH, settings.REPORT_HEARTBEAT_NAME, "SUCCEEDED")

