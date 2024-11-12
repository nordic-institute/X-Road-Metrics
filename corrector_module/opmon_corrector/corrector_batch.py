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

import multiprocessing
import time
from collections import defaultdict

from opmon_corrector import database_manager, document_manager
from opmon_corrector.corrector_worker import CorrectorWorker
from opmon_corrector.logger_manager import LoggerManager

PROCESSING_TIME_FORMAT = '%H:%M:%S'


class CorrectorBatch:
    def __init__(self, settings, logger_m: LoggerManager):
        self.settings = settings
        self.logger_m = logger_m

    def run(self, process_dict):
        """
        The run method fetches data and initializes corrector workers.
        :param process_dict:
        :return:
        """
        try:
            self._batch_run(process_dict)
        except Exception as e:
            # Catch internal exceptions to log
            self.logger_m.log_exception('corrector_batch_run', f'Error: {str(e)}')
            # Raise exception again
            raise e

    def _process_workers(self, list_to_process, duplicates, job_type='consume'):
        """
        Processes the workers in a thread pool.
        :param list_to_process: queue of items to be processed by the worker processes
        :param duplicates: a shared Value object to store the number of duplicates encountered
        during processing
        : return: None
        """
        # Configure worker
        pool = []
        for i in range(self.settings['corrector']['thread-count']):
            # Configure worker
            worker = CorrectorWorker(self.settings, f'worker_{i}')
            p = multiprocessing.Process(
                target=worker.run, args=(list_to_process, duplicates, job_type)
            )
            pool.append(p)

        # Starts all pool process
        for p in pool:
            p.start()
        # Wait all processes to finish their jobs
        for p in pool:
            p.join()

    def _batch_run(self, process_dict):
        """
        Gets unique xRequestId's, gets documents by xRequestId, corrects documents, initializes
        workers, gets raw documents, groups by "messageId", corrects documents' structure,
        initializes workers, updates timeout documents to "done", removes duplicates from
        raw_messages.
        :param process_dict:
        :return: Returns the amount of documents still to process.
        """
        doc_len = 0
        start_processing_time = time.time()
        self.logger_m.log_heartbeat('processing', 'SUCCEEDED')
        self.logger_m.log_info(
            'corrector_batch_start',
            'Starting corrector'
        )
        db_m = database_manager.DatabaseManager(self.settings)
        doc_m = document_manager.DocumentManager(self.settings)

        limit = self.settings['corrector']['documents-max']
        cursor = db_m.get_raw_documents(limit)
        self.logger_m.log_info('corrector_batch_raw', f'Processing {len(cursor)} raw documents.')

        # Process documents with xRequestId
        doc_map = defaultdict(list)
        for _doc in cursor:
            x_request_id = _doc.get('xRequestId')
            if not x_request_id:
                continue
            doc_map[x_request_id].append(_doc)

        # Build queue to be processed
        list_to_process = multiprocessing.Queue()
        duplicates = multiprocessing.Value('i', 0, lock=True)

        for x_request_id in doc_map:
            documents = doc_map[x_request_id]
            data = dict()
            data['logger_manager'] = self.logger_m
            data['document_manager'] = doc_m
            data['x_request_id'] = x_request_id
            data['documents'] = documents
            list_to_process.put(data)
            doc_len += len(documents)

        self._process_workers(list_to_process, duplicates)

        if duplicates.value > 0:
            self.logger_m.log_info(
                'corrector_batch_remove_duplicates_from_raw',
                f'Total of {duplicates.value} duplicate documents removed from raw messages.')
        else:
            self.logger_m.log_info(
                'corrector_batch_remove_duplicates_from_raw',
                'No raw documents marked to removal.')

        # Process documents without xRequestId
        cursor = db_m.get_faulty_raw_documents(limit)
        self.logger_m.log_info(
            'corrector_batch_raw', f'Processing {len(cursor)} faulty raw documents')
        if len(cursor) > 0:
            doc_len += len(cursor)
            list_to_process = multiprocessing.Queue()
            for _doc in cursor:
                data = dict()
                data['logger_manager'] = self.logger_m
                data['document_manager'] = doc_m
                data['document'] = _doc
                list_to_process.put(data)
            self._process_workers(list_to_process, None, 'faulty')

        # Updating Status of older documents from processing to done
        timeout = self.settings['corrector']['timeout-days']
        self.logger_m.log_info(
            'corrector_batch_update_timeout',
            f'Updating timed out [{timeout} days] orphans to done.')

        list_of_doc_ids_client = db_m.get_timeout_document_ids_client(timeout, limit=limit)
        list_of_doc_ids_producer = db_m.get_timeout_document_ids_producer(timeout, limit=limit)
        list_of_doc_ids = list_of_doc_ids_client + list_of_doc_ids_producer
        if len(list_of_doc_ids) > 0:
            doc_len += len(list_of_doc_ids)
            list_to_process = multiprocessing.Queue()
            for _doc in list_of_doc_ids:
                list_to_process.put(_doc['_id'])
            self._process_workers(list_to_process, None, 'timeout')

        if len(list_of_doc_ids_client) > 0:
            self.logger_m.log_info(
                'corrector_batch_update_client_old_to_done',
                f'Total of {len(list_of_doc_ids_client)} orphans from Client '
                "updated to status 'done'.")
        else:
            self.logger_m.log_info(
                'corrector_batch_update_client_old_to_done', 'No orphans updated to done.')

        if len(list_of_doc_ids_producer) > 0:
            self.logger_m.log_info(
                'corrector_batch_update_producer_old_to_done',
                f'Total of {len(list_of_doc_ids_producer)} orphans from Producer '
                "updated to status 'done'.")
        else:
            self.logger_m.log_info(
                'corrector_batch_update_producer_old_to_done', 'No orphans updated to done.')

        end_processing_time = time.time()
        total_time = time.strftime(
            PROCESSING_TIME_FORMAT,
            time.gmtime(end_processing_time - start_processing_time)
        )
        msg = [f'Number of duplicates: {duplicates.value}',
               f'Documents processed: {str(doc_len)}',
               f'Processing time: {total_time}']

        self.logger_m.log_info('corrector_batch_end', ' | '.join(msg))
        self.logger_m.log_heartbeat('finished', 'SUCCEEDED')
        process_dict['doc_len'] = doc_len
