import json
import logging
import os
import time
from logging.handlers import WatchedFileHandler


def get_timestamp():
    return int(time.time())


def get_local_timestamp():
    return time.strftime('%Y-%m-%d %H:%M:%S %z', time.localtime())


class LoggerManager:
    __version__ = 'v1.6'

    def __init__(self, logger_settings, xroad_instance):
        self.name = logger_settings['name']
        self.module = logger_settings['module']
        self.level = logger_settings['level']

        self.log_path = logger_settings['log-path']
        self.log_filename = f'log_{self.name}_{xroad_instance}.json'

        self.heartbeat_path = logger_settings['heartbeat-path']
        self.heartbeat_filename = f'heartbeat_{self.name}_{xroad_instance}.json'

        self._setup_logger()

    def _setup_logger(self):
        logger = logging.getLogger(self.name)
        logger.setLevel(self.level)

        if not logger.hasHandlers():
            formatter = logging.Formatter("%(message)s")
            log_file = os.path.join(self.log_path, self.log_filename)
            file_handler = WatchedFileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    def log_info(self, activity, msg):
        logger = logging.getLogger(self.name)
        # Build Message
        data = dict()
        data['level'] = 'INFO'
        data['timestamp'] = get_timestamp()
        data['local_timestamp'] = get_local_timestamp()
        data['module'] = self.module
        data['activity'] = activity
        data['msg'] = msg
        data['version'] = self.__version__
        # Log to file
        logger.info(json.dumps(data))

    def log_warning(self, activity, msg):
        logger = logging.getLogger(self.name)
        # Build Message
        data = dict()
        data['level'] = 'WARNING'
        data['timestamp'] = get_timestamp()
        data['local_timestamp'] = get_local_timestamp()
        data['module'] = self.module
        data['activity'] = activity
        data['msg'] = msg
        data['version'] = self.__version__
        # Log to file
        logger.warning(json.dumps(data))

    def log_error(self, activity, msg):
        logger = logging.getLogger(self.name)
        # Build Message
        data = dict()
        data['level'] = 'ERROR'
        data['timestamp'] = get_timestamp()
        data['local_timestamp'] = get_local_timestamp()
        data['module'] = self.module
        data['activity'] = activity
        data['msg'] = msg
        data['version'] = self.__version__
        # Log to file
        logger.error(json.dumps(data))

    def log_heartbeat(self, msg, status):
        # Build Message
        data = dict()
        data['status'] = status
        data['timestamp'] = get_timestamp()
        data['local_timestamp'] = get_local_timestamp()
        data['module'] = self.module
        data['msg'] = msg
        data['version'] = self.__version__
        # Log to file
        if not os.path.isdir(self.heartbeat_path):
            os.makedirs(self.heartbeat_path)
        with open(os.path.join(self.heartbeat_path, self.heartbeat_filename), 'w') as out_file:
            json.dump(data, out_file)
