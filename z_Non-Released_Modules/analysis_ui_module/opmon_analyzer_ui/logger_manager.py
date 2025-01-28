#
# The MIT License 
# Copyright (c) 2021- Nordic Institute for Interoperability Solutions (NIIS)
# Copyright (c) 2017-2020 Estonian Information System Authority (RIA)
#  
# Permission is hereby granted, free of charge, to any person obtaining a copy 
# of this software and associated documentation files (the "Software"), to deal 
# in the Software without restriction, including without limitation the rights 
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions: 
#  
# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software. 
#  
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN 
# THE SOFTWARE.
#

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
    def __init__(self, logger_settings, xroad_instance, version):
        self.name = logger_settings['name']
        self.module = logger_settings['module']
        self.level = logger_settings['level']
        self.log_path = os.path.join(logger_settings['log-path'], f'log_{self.name}_{xroad_instance}.json')

        self.heartbeat_path = logger_settings['heartbeat-path']
        self.heartbeat_filename = f'heartbeat_{self.name}_{xroad_instance}.json'

        self.version = version

        self._setup_logger()

    def _create_file_handler(self):
        formatter = logging.Formatter("%(message)s")

        file_handler = WatchedFileHandler(self.log_path)
        file_handler.setFormatter(formatter)
        return file_handler

    def _handler_is_set(self, handlers):
        for handler in handlers:
            if isinstance(handler, WatchedFileHandler) and os.path.abspath(self.log_path) == handler.baseFilename:
                return True
        return False

    def _setup_logger(self):
        logger = logging.getLogger(self.name)
        logger.setLevel(self.level)

        if not self._handler_is_set(logger.handlers):
            logger.addHandler(self._create_file_handler())

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
        data['version'] = self.version
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
        data['version'] = self.version
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
        data['version'] = self.version
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
        data['version'] = self.version
        # Log to file
        if not os.path.isdir(self.heartbeat_path):
            os.makedirs(self.heartbeat_path)
        with open(os.path.join(self.heartbeat_path, self.heartbeat_filename), 'w') as out_file:
            json.dump(data, out_file)
