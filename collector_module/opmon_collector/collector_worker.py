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

import json
import multiprocessing
import re
import uuid
import zlib
import requests
from enum import Enum

from opmon_collector.security_server_client import SecurityServerClient


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
                self.records = self._parse_attachment(response)
                self._store_records_to_database()
                self.batch_start = self._parse_next_records_from_response(response) or self.batch_end
                self.server_m.set_next_records_timestamp(self.server_key, self.batch_start)
            except Exception as e:
                self.log_warn("Collector caught exception.", repr(e))
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
            f"[{self.thread_name}] Message: {message} Server: {self.server_key} Cause: {cause} \n")

    def log_info(self, message):
        self.logger_m.log_info(
            'collector_worker',
            f"[{self.thread_name}] Message: {message} Server: {self.server_key} \n")

    def _log_status(self):
        if self.status == CollectorWorker.Status.ALL_COLLECTED:
            self.log_info(f'Records collected until {self.batch_end}.')
        elif self.status == CollectorWorker.Status.TOO_SMALL_BATCH:
            self.log_info(f'Not enough data received to repeat query.')
        else:
            self.log_warn("Maximum repeats reached.", "")

    def _get_record_limits(self):
        records_from_offset = self.settings['collector']['records-from-offset']
        records_to_offset = self.settings['collector']['records-to-offset']
        records_from = int(self.server_m.get_next_records_timestamp(self.server_key, records_from_offset))
        records_to = int(self.server_m.get_timestamp() - records_to_offset)

        return records_from, records_to

    def _request_opmon_data(self):
        self.log_info(f'Collecting from {self.batch_start} to {self.batch_end}')

        req_id = str(uuid.uuid4())
        headers = {"Content-type": "text/xml;charset=UTF-8"}
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
            return response
        except Exception as e:
            self.log_warn("Request for operational monitoring data failed.", '')
            raise e

    def _parse_attachment(self, opmon_response):
        try:
            resp_search = re.search(b"content-id: <operational-monitoring-data.json.gz>\r\n\r\n(.+)\r\n--xroad",
                                    opmon_response.content, re.DOTALL)
            if resp_search is None:
                self.log_warn('No attachment present.', '')
                raise FileNotFoundError('Attachment not found in operational monitoring data response.')

            data_json = json.loads(zlib.decompress(resp_search.group(1), zlib.MAX_WBITS | 16).decode('utf-8'))
            return data_json["records"]
        except Exception as e:
            self.log_warn("Cannot parse response attachment.", '')
            raise e

    def _store_records_to_database(self):
        if len(self.records):
            self.log_info(f"Adding {len(self.records)} documents.")
            try:
                self.server_m.insert_data_to_raw_messages(self.records)
            except Exception as e:
                self.log_warn("Failed to save records.", '')
                raise e
        else:
            self.log_warn("No documents to store!", "")

    @staticmethod
    def _parse_next_records_from_response(response):
        result = re.search(b"<om:nextRecordsFrom>(\\d+)</om:nextRecordsFrom>", response.content)
        return None if result is None else int(result.group(1))


def run_collector_thread(data):
    worker = CollectorWorker(data)
    return worker.work()
