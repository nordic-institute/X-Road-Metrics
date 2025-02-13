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
""" Gets list of server information from CENTRALSERVER
    Stores updated list into collector_state.server_list
"""

from .central_server_client import CentralServerClient
from .database_manager import DatabaseManager
from .logger_manager import LoggerManager
from .pid_file_handler import OpmonPidFileHandler
from . import __version__


def _init_clients(settings, logger_m):
    cs_client = CentralServerClient(settings['xroad'], logger_m)
    db_client = DatabaseManager(settings['mongodb'], settings['xroad']['instance'], logger_m)
    return cs_client, db_client


def update_database_server_list(settings):
    logger_m = LoggerManager(settings['logger'], settings['xroad']['instance'], __version__)

    try:
        OpmonPidFileHandler(settings).create_pid_file()
    except RuntimeError as e:
        logger_m.log_error('update_database_server_list', str(e))
        raise e

    cs_client, db_client = _init_clients(settings, logger_m)
    server_list = cs_client.get_security_servers()
    if len(server_list):
        db_client.save_server_list_to_database(server_list)
        logger_m.log_info(
            'update_database_server_list',
            '- Total of {0} inserted into server_list collection.'.format(len(server_list))
        )
    else:
        logger_m.log_info('update_database_server_list', '- No servers found')


def print_server_list(settings):
    logger_m = LoggerManager(settings['logger'], settings['xroad']['instance'], __version__)
    cs_client, _ = _init_clients(settings, logger_m)
    server_list = cs_client.get_security_servers()
    for s in server_list:
        print(s)
