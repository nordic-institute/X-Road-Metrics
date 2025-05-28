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

import datetime
import json
import logging
import multiprocessing
import os
import re
import uuid
import xml.etree.ElementTree as ET
import zlib
from enum import Enum
from logging.handlers import RotatingFileHandler
from xml.etree.ElementTree import Element  # noqa: F401
from xml.etree.ElementTree import ParseError

import requests
from opmon_collector.security_server_client import SecurityServerClient

# Constants
MIN_REST_PATH_VERSION = '7.6.2'


class ServerProxyError(Exception):
    pass


class ServerClientProxyError(Exception):
    pass


class CollectorWorker:
    class Status(Enum):
        DATA_AVAILABLE = 0
        ALL_COLLECTED = 1
        TOO_SMALL_BATCH = 2

    def __init__(self, data):
        self.settings = data['settings']
        self.server_data = data['server_data']
        self.server_key = self.server_data['server']
        self.logger_m = data['logger_manager']
        self.server_m = data['server_manager']
        self.thread_name = multiprocessing.current_process().name

        self.batch_start, self.batch_end = self._get_record_limits()
        self.status = CollectorWorker.Status.DATA_AVAILABLE
        self.records = []

    def work(self):
        for _ in range(self.settings['collector']['repeat-limit']):
            try:
                response = self._request_opmon_data()
                records = self._parse_attachment(response)
                sanitized_records = self._sanitize_records(records)
                self.records = sanitized_records
                if self.settings['collector'].get('documents-log-directory', ''):
                    self._store_records_to_file()
                self._store_records_to_database()
                self.batch_start = self._parse_next_records_from_response(response) or self.batch_end
                self.server_m.set_next_records_timestamp(self.server_key, self.batch_start)
            except ServerClientProxyError as e:
                self.log_error('Collector caught exception.', repr(e))
                return False, e
            except Exception as e:
                self.log_exception('Collector caught exception.', repr(e))
                return False, e

            self.update_status()
            if self.status != CollectorWorker.Status.DATA_AVAILABLE:
                break

        self._log_status()
        return True, None

    def update_status(self):
        if self.batch_start >= self.batch_end:
            self.status = CollectorWorker.Status.ALL_COLLECTED
        elif len(self.records) < self.settings['collector']['repeat-min-records']:
            self.status = CollectorWorker.Status.TOO_SMALL_BATCH

    def log_warn(self, message, cause):
        self.logger_m.log_warning(
            'collector_worker',
            f'[{self.thread_name}] Message: {message} Server: {self.server_key} Cause: {cause} \n')

    def log_info(self, message):
        self.logger_m.log_info(
            'collector_worker',
            f'[{self.thread_name}] Message: {message} Server: {self.server_key} \n')

    def log_error(self, message, cause):
        self.logger_m.log_error(
            'collector_worker',
            f'[{self.thread_name}] Message: {message} Server: {self.server_key} Cause: {cause} \n')

    def log_exception(self, message: str, cause: str) -> None:
        self.logger_m.log_exception(
            'collector_worker',
            f'[{self.thread_name}] Message: {message} Server: {self.server_key} Cause: {cause} \n')

    def _log_status(self):
        if self.status == CollectorWorker.Status.ALL_COLLECTED:
            self.log_info(f'Records collected until {self.batch_end}.')
        elif self.status == CollectorWorker.Status.TOO_SMALL_BATCH:
            self.log_info('Not enough data received to repeat query.')
        else:
            self.log_warn('Maximum repeats reached.', '')

    def _get_record_limits(self):
        records_from_offset = self.settings['collector']['records-from-offset']
        records_to_offset = self.settings['collector']['records-to-offset']
        records_from = int(self.server_m.get_next_records_timestamp(self.server_key, records_from_offset))
        records_to = int(self.server_m.get_timestamp() - records_to_offset)

        return records_from, records_to

    def _request_opmon_data(self):
        self.log_info(f'Collecting from {self.batch_start} to {self.batch_end}')

        req_id = str(uuid.uuid4())
        headers = {'Content-type': 'text/xml;charset=UTF-8'}
        client_xml = SecurityServerClient.get_soap_monitoring_client(self.settings['xroad'])
        body = SecurityServerClient.get_soap_body(
            client_xml,
            self.server_data,
            req_id,
            self.batch_start,
            self.batch_end)

        try:
            sec_server_settings = self.settings['xroad']['security-server']
            url = sec_server_settings['protocol'] + sec_server_settings['host']
            timeout = sec_server_settings['timeout']
            client_cert = (
                sec_server_settings.get('tls-client-certificate'),
                sec_server_settings.get('tls-client-key')
            )
            server_cert = sec_server_settings.get('tls-server-certificate')
            response = requests.post(
                url, data=body, headers=headers, timeout=timeout,
                cert=client_cert, verify=server_cert
            )
            response.raise_for_status()
            self._process_soap_errors(response.content)
            return response
        except Exception as e:
            self.log_exception('Request for operational monitoring data failed.', str(e))
            raise e

    def _process_soap_errors(self, metrics_response: str) -> None:
        try:
            root = ET.fromstring(metrics_response)  # type: Element
            fault_code_element = root.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Fault/faultcode')
            fault_string_element = root.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Fault/faultstring')
            fault_detail_element = root.find('.//{http://schemas.xmlsoap.org/soap/envelope/}Fault/detail/faultDetail')
            fault_code = fault_code_element.text if fault_code_element is not None else None
            fault_string = fault_string_element.text if fault_string_element is not None else None
            fault_detail = fault_detail_element.text if fault_detail_element is not None else None
            if fault_code:
                error_message = f'Message: {fault_string}. Code: {fault_code}. Detail: {fault_detail}'
                if fault_code.startswith('Server.ClientProxy'):
                    raise ServerClientProxyError(error_message)
                raise ServerProxyError(error_message)
        except ParseError:
            pass

    def _parse_attachment(self, opmon_response):
        try:
            resp_search = re.search(b'content-id: <operational-monitoring-data.json.gz>\r\n\r\n(.+)\r\n--xroad',
                                    opmon_response.content, re.DOTALL)
            if resp_search is None:
                self.log_warn('No attachment present.', '')
                raise FileNotFoundError('Attachment not found in operational monitoring data response.')

            data_json = json.loads(zlib.decompress(resp_search.group(1), zlib.MAX_WBITS | 16).decode('utf-8'))
            return data_json['records']
        except Exception as e:
            self.log_exception('Cannot parse response attachment.', str(e))
            raise e

    """
    Check if the version is greater than or equal to the base version.
    :param version: Version to check
    :param base_version: Base version to compare with
    :return: True if version is greater than or equal to base_version, False otherwise"""    
    @staticmethod
    def _version_gte(version, base_version):
        if not isinstance(version, str) or not version.strip():
            return False
        try:
            return tuple(map(int, version.split('.'))) >= tuple(map(int, base_version.split('.')))
        except ValueError:
            return False

    @staticmethod
    def _sanitize_records(records):
        """
        Remove 'restPath' field from records if the xRoadVersion is not present or is less than 7.6.2.
        """
        sanitized_records = []
        for record in records:
            sanitized_record = record.copy()
            if 'xRoadVersion' not in record or not CollectorWorker._version_gte(record['xRoadVersion'], MIN_REST_PATH_VERSION):
                sanitized_record.pop('restPath', None)
            sanitized_records.append(sanitized_record)
        return sanitized_records

    def _get_records_logger(self) -> logging.Logger:
        host_name = re.sub('[^0-9a-zA-Z.-]+', '.', self.server_data['server'])
        records_logger = logging.getLogger(host_name)

        now = datetime.datetime.now()
        log_path = f"{self.settings['collector']['documents-log-directory']}" \
            f"/{self.settings['xroad']['instance']}/{now.year:04d}/{now.month:02d}/{now.day:02d}/"

        base_filename = log_path + host_name + '.log'
        rotating_host_handlers = [
            handler for handler in records_logger.handlers
            if isinstance(handler, RotatingFileHandler)
            and handler.baseFilename == base_filename
        ]
        if not rotating_host_handlers:
            if not os.path.exists(log_path):
                os.makedirs(log_path)

            handler = RotatingFileHandler(
                base_filename,
                maxBytes=self.settings['collector'].get('documents-log-file-size') or 0,
                backupCount=self.settings['collector'].get('documents-log-max-files') or 0
            )

            records_logger.setLevel(logging.INFO)
            records_logger.addHandler(handler)
        return records_logger

    def _store_records_to_file(self) -> None:
        if len(self.records):
            self.log_info(f'Appending {len(self.records)} documents to log file.')
            records_logger = self._get_records_logger()
            for record in self.records:
                records_logger.info(json.dumps(record, separators=(',', ':')))
        else:
            self.log_warn('No documents to append to log file!', '')

    def _store_records_to_database(self) -> None:
        if len(self.records):
            self.log_info(f'Adding {len(self.records)} documents.')
            try:
                self.server_m.insert_data_to_raw_messages(self.records)
            except Exception as e:
                self.log_exception('Failed to save records.', str(e))
                raise e
        else:
            self.log_warn('No documents to store!', '')

    @staticmethod
    def _parse_next_records_from_response(response):
        result = re.search(b'<om:nextRecordsFrom>(\\d+)</om:nextRecordsFrom>', response.content)
        return None if result is None else int(result.group(1))


def run_collector_thread(data):
    worker = CollectorWorker(data)
    return worker.work()
