import json
import logging
import multiprocessing
import os
import re
import time
import uuid
import zlib
from logging.handlers import WatchedFileHandler
from multiprocessing import Pool

import requests

from . import settings
from .collectorlib.database_manager import DatabaseManager
from .collectorlib.logger_manager import LoggerManager


def collector_worker(data):
    logger_m = data['logger_manager']
    server_m = data['server_manager']
    server_data = data['server_data']
    server = server_data['server']
    repeat = data['repeat']
    # Use time in integer seconds inside worker
    records_from = int(data['next_records_from'])
    records_to = int(data['next_records_to'])
    xRoadInstance = server_data['instance']
    memberClass = server_data['memberClass']
    memberCode = server_data['memberCode']
    serverCode = server_data['serverCode']
    req_id = str(uuid.uuid4())
    worker_name = multiprocessing.current_process().name

    # Log collection period
    msg = '[{0}] Collecting {1} from {2} to {3}'.format(worker_name, server, records_from, records_to)
    logger_m.log_info('collector_worker', msg)

    headers = {"Content-type": "text/xml;charset=UTF-8"}
    monitoring_client = settings.MONITORING_CLIENT
    body = server_m.get_soap_body(monitoring_client, xRoadInstance, memberClass, memberCode,
                                  serverCode, req_id, records_from, records_to)

    try:
        response = requests.post(settings.SECURITY_SERVER_URL, data=body, headers=headers, timeout=settings.SECURITY_SERVER_TIMEOUT)
        response.raise_for_status()
    except Exception as e:
        msg = "[{0}] Cannot get response for: {1} Cause: {2} \n".format(worker_name, server, repr(e))
        logger_m.log_warning('collector_worker', msg)
        return -1

    try:
        # Finding attachment
        resp_search = re.search(b"content-id: <operational-monitoring-data.json.gz>\r\n\r\n(.+)\r\n--xroad",
                                response.content, re.DOTALL)
        if resp_search is None:
            # No attachment present
            msg = "[{0}] No attachment present for: {1}\n".format(worker_name, server)
            logger_m.log_warning('collector_worker', msg)
            return -1

        data_json = json.loads(zlib.decompress(resp_search.group(1), zlib.MAX_WBITS | 16).decode('utf-8'))
        records = data_json["records"]
    except Exception as e:
        msg = "[{0}] Cannot parse response attachment of: {1} Cause: {2} \n".format(worker_name, server, repr(e))
        logger_m.log_warning('collector_worker', msg)
        return -1

    # Add data to database
    if len(records):
        msg = "[{0}] Adding {1} documents for server: {2}".format(worker_name, len(records), server)
        logger_m.log_info('collector_worker', msg)
        server_m.insert_data_to_raw_messages(records)
    else:
        msg = "[{0}] No documents for server: {1}".format(worker_name, server)
        logger_m.log_warning('collector_worker', msg)

    return_value = 0
    next_records_from = records_to

    # Update nextRecordsFrom value
    resp_search = re.search(b"<om:nextRecordsFrom>(\d+)</om:nextRecordsFrom>", response.content)
    if resp_search:
        next_records_from = int(resp_search.group(1))
        # Deciding if we should repeat query and fetch additional data
        if len(records) < settings.REPEAT_MIN_RECORDS:
            msg = "[{0}] Not enough data received ({1}) to repeat query to server {2}".format(worker_name, len(records),
                                                                                              server)
            logger_m.log_info('collector_worker', msg)
        elif repeat > 0:
            return_value = repeat - 1
            if return_value == 0:
                msg = "[{0}] Maximum repeats reached for server {1}".format(worker_name, server)
                logger_m.log_warning('collector_worker', msg)
        else:
            msg = "[{0}] Maximum repeats reached for server {1}".format(worker_name, server)
            logger_m.log_warning('collector_worker', msg)

    # Updates collector pointer
    server_m.set_next_records_timestamp(server, next_records_from)
    return return_value


def collector_main(logger_m):
    """
    :param logger_m:
    :return:
    """
    server_m = DatabaseManager(settings.MONGODB_SUFFIX,
                               settings.MONGODB_SERVER,
                               settings.MONGODB_USER,
                               settings.MONGODB_PWD,
                               logger_m)

    logger_m.log_info('collector_start', 'Starting collector - Version {0}'.format(LoggerManager.__version__))

    start_processing_time = time.time()
    pool = Pool(processes=settings.THREAD_COUNT)
    data = server_m.get_server_list_database()[0]
    server_list = data['server_list']
    print('- Using server list updated at: {0}'.format(data['timestamp']))

    list_to_process = []
    records_from_offset = settings.RECORDS_FROM_OFFSET

    for server in server_list:
        server_key = server['server']
        records_from = server_m.get_next_records_timestamp(server_key, records_from_offset)
        records_to = server_m.get_timestamp() - settings.RECORDS_TO_OFFSET
        data = dict()
        data['logger_manager'] = logger_m
        data['server_manager'] = server_m
        data['server_data'] = server
        data['repeat'] = settings.REPEAT_LIMIT
        data['next_records_from'] = records_from
        data['next_records_to'] = records_to
        list_to_process.append(data)

    total_error = 0
    total_done = 0

    while list_to_process:
        processed = pool.map(collector_worker, list_to_process)
        # Check servers that are not finished
        repeat_process = []
        for i, p in enumerate(processed):
            if p == -1:
                total_error += 1
            elif p == 0:
                total_done += 1
            else:
                data = list_to_process[i]
                server_key = data['server_data']['server']
                records_from = server_m.get_next_records_timestamp(server_key, records_from_offset)
                records_to = server_m.get_timestamp() - settings.RECORDS_TO_OFFSET
                data['repeat'] = p
                data['next_records_from'] = records_from
                data['next_records_to'] = records_to
                repeat_process.append(data)
        list_to_process = repeat_process

    end_processing_time = time.time()
    total_time = time.strftime("%H:%M:%S", time.gmtime(end_processing_time - start_processing_time))
    logger_m.log_info(
        'collector_end', 'Total collected: {0}, Total error: {1}, Total time: {2}'.format(
            total_done, total_error, total_time))
    logger_m.log_heartbeat('Total collected: {0}, Total error: {1}, Total time: {2}'.format(
        total_done, total_error, total_time), settings.HEARTBEAT_PATH, settings.HEARTBEAT_FILE, "SUCCEEDED")


if __name__ == '__main__':
    logger = logging.getLogger(settings.LOGGER_NAME)
    logger.setLevel(settings.LOGGER_LEVEL)
    log_file_name = settings.LOGGER_FILE

    formatter = logging.Formatter("%(message)s")
    log_file = os.path.join(settings.LOGGER_PATH, log_file_name)
    file_handler = WatchedFileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    logger_m = LoggerManager(settings.LOGGER_NAME, settings.MODULE)
    try:
        collector_main(logger_m)
    except Exception as e:
        logger_m.log_error('collector', '{0}'.format(repr(e)))
        logger_m.log_heartbeat("error", settings.HEARTBEAT_PATH, settings.HEARTBEAT_FILE, "FAILED")
        raise e
