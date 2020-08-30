import json
import logging
import os
import time
from logging.handlers import RotatingFileHandler


def get_timestamp():
    return int(time.time())


def get_local_timestamp():
    return time.strftime('%Y-%m-%d %H:%M:%S %z', time.localtime())


class LoggerManager:
    __version__ = 'v1.5'

    def __init__(self, logger_name, module_name, heartbeat_dir=None):
        """
        Creates a LoggerManager object that keeps the logger_name and module_name inside.
        :param logger_name: Name of the logger.
        :param module_name: Name of the module.
        """
        self.logger_name = logger_name
        self.module_name = module_name
        self.heartbeat_dir = heartbeat_dir

    def log_info(self, activity, msg):
        logger = logging.getLogger(self.logger_name)
        # Build Message
        data = dict()
        data['level'] = 'INFO'
        data['timestamp'] = get_timestamp()
        data['local_timestamp'] = get_local_timestamp()
        data['module'] = self.module_name
        data['activity'] = activity
        data['msg'] = msg
        data['version'] = self.__version__
        # Log to file
        logger.info(json.dumps(data))

    def log_warning(self, activity, msg):
        logger = logging.getLogger(self.logger_name)
        # Build Message
        data = dict()
        data['level'] = 'WARNING'
        data['timestamp'] = get_timestamp()
        data['local_timestamp'] = get_local_timestamp()
        data['module'] = self.module_name
        data['activity'] = activity
        data['msg'] = msg
        data['version'] = self.__version__
        # Log to file
        logger.warning(json.dumps(data))

    def log_error(self, activity, msg):
        logger = logging.getLogger(self.logger_name)
        # Build Message
        data = dict()
        data['level'] = 'ERROR'
        data['timestamp'] = get_timestamp()
        data['local_timestamp'] = get_local_timestamp()
        data['module'] = self.module_name
        data['activity'] = activity
        data['msg'] = msg
        data['version'] = self.__version__
        # Log to file
        logger.error(json.dumps(data))

    def log_heartbeat(self, msg, heartbeat_name, status):
        # Build Message
        data = dict()
        data['timestamp'] = get_timestamp()
        data['local_timestamp'] = get_local_timestamp()
        data['module'] = self.module_name
        data['msg'] = msg
        data['version'] = self.__version__
        data['status'] = status
        # Log to file
        with open(os.path.join(self.heartbeat_dir, "{0}.json".format(heartbeat_name)), 'w') as out_file:
            json.dump(data, out_file)


def setup_logger(logger_name, log_level, log_path, max_file_size, backup_count):
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    formatter = logging.Formatter("%(message)s")
    rotate_handler = RotatingFileHandler(log_path, maxBytes=max_file_size,
                                         backupCount=backup_count)
    rotate_handler.setFormatter(formatter)
    logger.addHandler(rotate_handler)
