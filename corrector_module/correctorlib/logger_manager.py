""" Logger Manager - Corrector Module
"""

import json
import logging
import os
import time


def get_timestamp():
    return int(time.time())


def get_local_timestamp():
    return time.strftime('%Y-%m-%d %H:%M:%S %z', time.localtime())


class LoggerManager:
    __version__ = 'v1.5'

    def __init__(self, logger_name, module_name):
        self.logger_name = logger_name
        self.module_name = module_name

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

    def log_heartbeat(self, msg, heartbeat_path, heartbeat_name, status):
        # Build Message
        data = dict()
        data['status'] = status
        data['timestamp'] = get_timestamp()
        data['local_timestamp'] = get_local_timestamp()
        data['module'] = self.module_name
        data['msg'] = msg
        data['version'] = self.__version__
        # Log to file
        if not os.path.isdir(heartbeat_path):
            os.makedirs(heartbeat_path)
        with open(os.path.join(heartbeat_path, heartbeat_name), 'w') as out_file:
            json.dump(data, out_file)
