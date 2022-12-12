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

import multiprocessing
import queue
import time
import traceback

from . import database_manager
from . import document_manager
from .hash_based_corrector_worker import CorrectorWorker as HashBasedCorrectorWorker
from .corrector_worker import CorrectorWorker
from .logger_manager import LoggerManager


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
            msg = "Error: {0} {1}".format(repr(e), traceback.format_exc()).replace("\n", "")
            self.logger_m.log_error('corrector_batch_run', msg)
            # Raise exception again
            raise e

    def _batch_run(self, process_dict):
        """
        Gets unique xRequestId's, gets documents by xRequestId, corrects documents, unitializes workers,
        gets raw documents, groups by "messageId", corrects documents' structure, initializes workers,
        updates timeout documents to "done", removes duplicates from raw_messages.
        :param process_dict:
        :return: Returns the amount of documents still to process.
        """

        doc_len = 0
        start_processing_time = time.time()
        self.logger_m.log_heartbeat("processing", "SUCCEEDED")
        self.logger_m.log_info(
            'corrector_batch_start',
            f'Starting corrector'
        )

        db_m = database_manager.DatabaseManager(self.settings)
        doc_m = document_manager.DocumentManager(self.settings)
        list_to_process = multiprocessing.Queue()
        duplicates = multiprocessing.Value('i', 0, lock=True)

        m = multiprocessing.Manager()
        to_remove_queue = m.Queue()

        # Process documents with xRequestId

        x_request_ids = db_m.get_raw_x_request_ids()

        doc_map = {}
        for x_request_id in x_request_ids:
            doc_map[x_request_id] = []
            cursor = db_m.get_raw_documents_by_x_request_id(x_request_id)
            for _doc in cursor:
                fix_doc = doc_m.correct_structure(_doc)
                doc_map[x_request_id].append(fix_doc)

        for x_request_id in doc_map:
            documents = doc_map[x_request_id]
            data = dict()
            data['logger_manager'] = self.logger_m
            data['document_manager'] = doc_m
            data['x_request_id'] = x_request_id
            data['documents'] = documents
            data['to_remove_queue'] = to_remove_queue
            list_to_process.put(data)
            doc_len += len(documents)

        pool = []
        for i in range(self.settings["corrector"]["thread-count"]):
            # Configure worker
            worker = CorrectorWorker(self.settings, f'worker_{i}')
            p = multiprocessing.Process(target=worker.run, args=(list_to_process, duplicates))
            pool.append(p)

        # Starts all pool process
        for p in pool:
            p.start()
        # Wait all processes to finish their jobs
        for p in pool:
            p.join()

        # Process documents without xRequestId

        limit = self.settings["corrector"]["documents-max"]
        cursor = db_m.get_raw_documents(limit=limit)
        self.logger_m.log_info('corrector_batch_raw', 'Processing {0} raw documents'.format(len(cursor)))

        # Aggregate documents by message id
        # Correct missing fields
        doc_map = {}
        for _doc in cursor:
            message_id = _doc.get('messageId', '')
            if message_id not in doc_map:
                doc_map[message_id] = []
            fix_doc = doc_m.correct_structure(_doc)
            doc_map[message_id].append(fix_doc)

        for message_id in doc_map:
            documents = doc_map[message_id]
            data = dict()
            data['logger_manager'] = self.logger_m
            data['document_manager'] = doc_m
            data['message_id'] = message_id
            data['documents'] = documents
            data['to_remove_queue'] = to_remove_queue
            list_to_process.put(data)
            doc_len += len(documents)

        # Create pool of workers
        pool = []
        for i in range(self.settings["corrector"]["thread-count"]):
            # Configure worker
            worker = HashBasedCorrectorWorker(self.settings, f'worker_{i}')
            p = multiprocessing.Process(target=worker.run, args=(list_to_process, duplicates))
            pool.append(p)

        # Starts all pool process
        for p in pool:
            p.start()
        # Wait all processes to finish their jobs
        for p in pool:
            p.join()

        # TODO
        timeout = self.settings['corrector']['timeout-days']
        self.logger_m.log_info('corrector_batch_update_timeout',
                               f"Updating timed out [{timeout} days] orphans to done.")

        # Update Status of older documents according to client.requestInTs
        cursor = db_m.get_timeout_documents_client(timeout, limit=limit)
        list_of_docs = list(cursor)
        number_of_updated_docs = db_m.update_old_to_done(list_of_docs)

        if number_of_updated_docs > 0:
            self.logger_m.log_info('corrector_batch_update_client_old_to_done',
                                   "Total of {0} orphans from Client updated to status 'done'.".format(
                                       number_of_updated_docs))
        else:
            self.logger_m.log_info('corrector_batch_update_client_old_to_done',
                                   "No orphans updated to done.")

        doc_len += number_of_updated_docs

        # Update Status of older documents according to producer.requestInTs
        cursor = db_m.get_timeout_documents_producer(timeout, limit=limit)
        list_of_docs = list(cursor)
        number_of_updated_docs = db_m.update_old_to_done(list_of_docs)

        if number_of_updated_docs > 0:
            self.logger_m.log_info('corrector_batch_update_producer_old_to_done',
                                   "Total of {0} orphans from Producer updated to status 'done'.".format(
                                       number_of_updated_docs))
        else:
            self.logger_m.log_info('corrector_batch_update_producer_old_to_done',
                                   "No orphans updated to done.")

        doc_len += number_of_updated_docs

        # Go through the to_remove list and remove the duplicates
        element_in_queue = True
        total_raw_removed = 0
        while element_in_queue:
            try:
                element = to_remove_queue.get(False)
                db_m.remove_duplicate_from_raw(element)
                total_raw_removed += 1
            except queue.Empty:
                element_in_queue = False

        if total_raw_removed > 0:
            self.logger_m.log_info('corrector_batch_remove_duplicates_from_raw',
                                   "Total of {0} duplicate documents removed from raw messages.".format(
                                       total_raw_removed))
        else:
            self.logger_m.log_info('corrector_batch_remove_duplicates_from_raw',
                                   "No raw documents marked to removal.")

        doc_len += total_raw_removed

        end_processing_time = time.time()
        total_time = time.strftime("%H:%M:%S", time.gmtime(end_processing_time - start_processing_time))
        msg = ["Number of duplicates: {0}".format(duplicates.value),
               "Documents processed: " + str(doc_len),
               "Processing time: {0}".format(total_time)]

        self.logger_m.log_info('corrector_batch_end', ' | '.join(msg))
        self.logger_m.log_heartbeat(
            "finished", "SUCCEEDED")
        process_dict['doc_len'] = doc_len
