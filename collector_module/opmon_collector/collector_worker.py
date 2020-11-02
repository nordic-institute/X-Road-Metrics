import json
import multiprocessing
import re
import uuid
import zlib
import requests


class CollectorWorker:
    def __init__(self, data):
        self.settings = data['settings']
        self.server_data = data['server_data']
        self.server_key = self.server_data['server']
        self.logger_m = data['logger_manager']
        self.server_m = data['server_manager']
        self.repeat = self.settings['collector']['repeat-limit']
        self.thread_name = multiprocessing.current_process().name

        self.records_from, self.records_to = self._get_record_limits()

    def work(self):
        while self.repeat:
            try:
                response = self._request_opmon_data()
                records = self._parse_attachment(response)
                self._store_records_to_database(records)
                next_records_from = self._parse_next_records_from_response(response) or self.records_to
                self.server_m.set_next_records_timestamp(self.server_key, next_records_from)
            except Exception as e:
                self.log_warn("Collector caught exception.", repr(e))
                return False

            self._update_repeat(next_records_from, len(records))

        return True

    def log_warn(self, message, cause):
        self.logger_m.log_warning(
            'collector_worker',
            f"[{self.thread_name}] Message: {message} Server: {self.server_key} Cause: {cause} \n")

    def log_info(self, message):
        self.logger_m.log_warning(
            'collector_worker',
            f"[{self.thread_name}] Message: {message} Server: {self.server_key} \n")

    def _get_record_limits(self):
        records_from_offset = self.settings['collector']['records-from-offset']
        records_to_offset = self.settings['collector']['records-to-offset']
        records_from = int(self.server_m.get_next_records_timestamp(self.server_key, records_from_offset))
        records_to = int(self.server_m.get_timestamp() - records_to_offset)

        return records_from, records_to

    def _request_opmon_data(self):
        self.log_info(f'Collecting from {self.records_from} to {self.records_to}')

        req_id = str(uuid.uuid4())
        headers = {"Content-type": "text/xml;charset=UTF-8"}
        client_xml = self.server_m.get_soap_monitoring_client(self.settings['xroad'])
        body = self.server_m.get_soap_body(
            client_xml,
            self.server_data,
            req_id,
            self.records_from,
            self.records_to)

        try:
            sec_server_settings = self.settings['xroad']['security-server']
            url = sec_server_settings['protocol'] + sec_server_settings['host']
            timeout = sec_server_settings['timeout']
            response = requests.post(url, data=body, headers=headers, timeout=timeout)
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

    def _store_records_to_database(self, records):
        if len(records):
            self.log_info(f"Adding {len(records)} documents.")
            try:
                self.server_m.insert_data_to_raw_messages(records)
            except Exception as e:
                self.log_warn("Failed to save records.", '')
                raise e
        else:
            self.log_warn("No documents to store!", "")

    @staticmethod
    def _parse_next_records_from_response(response):
        result = re.search(b"<om:nextRecordsFrom>(\d+)</om:nextRecordsFrom>", response.content)
        return None if result is None else int(result.group(1))

    def _update_repeat(self, next_records_from, record_size):
        if next_records_from >= self.records_to:
            self.log_info(f'Records collected until {self.records_to}.')
            self.repeat = 0

        if record_size < self.settings['collector']['repeat-min-records']:
            self.log_info(f'Not enough data received ({record_size}) to repeat query.')
            self.repeat = 0

        self.repeat -= 1
        if self.repeat <= 0:
            self.log_warn("Maximum repeats reached.", "")
            self.repeat = 0


def run_collector_thread(data):
    worker = CollectorWorker(data)
    return worker.work()

