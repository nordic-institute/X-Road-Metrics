#  The MIT License
#  Copyright (c) 2021- Nordic Institute for Interoperability Solutions (NIIS)
#  Copyright (c) 2017-2020 Estonian Information System Authority (RIA)
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

import time
from multiprocessing import Pool

from .database_manager import DatabaseManager
from .logger_manager import LoggerManager
from .collector_worker import run_collector_thread
from .pid_file_handler import OpmonPidFileHandler
from . import __version__

def prepare_thread_inputs(settings, server_list, server_m, logger_m):
    inputs = []

    for server in server_list:
        data = dict()
        data['settings'] = settings
        data['logger_manager'] = logger_m
        data['server_manager'] = server_m
        data['server_data'] = server
        inputs.append(data)

    return inputs


def process_thread_pool(settings, inputs):
    pool = Pool(processes=settings['collector']['thread-count'])
    results = pool.map(run_collector_thread, inputs)
    done = len([result[0] for result in results if result[0]])
    error = len(results) - done
    return done, error


def run_threaded_collector(logger_m, settings):
    logger_m.log_info('collector_start', f'Starting collector')

    OpmonPidFileHandler(settings).create_pid_file()

    start_time_time = time.time()
    server_m = DatabaseManager(settings['mongodb'], settings['xroad']['instance'], logger_m)
    server_list, timestamp = server_m.get_server_list_from_database()
    print(f'- Using server list updated at: {timestamp}')

    inputs = prepare_thread_inputs(settings, server_list, server_m, logger_m)
    done, error = process_thread_pool(settings, inputs)

    total_time = time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time_time))
    logger_m.log_info('collector_end', f'Total collected: {done}, Total error: {error}, Total time: {total_time}')
    logger_m.log_heartbeat(f'Total collected: {done}, Total error: {error}, Total time: {total_time}', "SUCCEEDED")


def collector_main(settings):
    logger_m = LoggerManager(settings['logger'], settings['xroad']['instance'], __version__)

    try:
        run_threaded_collector(logger_m, settings)
    except Exception as e:
        logger_m.log_error('collector', '{0}'.format(repr(e)))
        logger_m.log_heartbeat("error", "FAILED")
        raise e
