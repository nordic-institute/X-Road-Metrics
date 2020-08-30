import sys

import settings
from collectorlib.logger_manager import LoggerManager

if __name__ == '__main__':
    """
    The error handler for handling bash script errors and to log into heartbeat & log.
    """
    args = sys.argv
    msg = ' '.join(args)

    logger_m = LoggerManager(settings.LOGGER_NAME, settings.MODULE)
    logger_m.log_error(args[0], msg)
    logger_m.log_heartbeat(msg, settings.HEARTBEAT_PATH, settings.HEARTBEAT_FILE, "FAILED")


