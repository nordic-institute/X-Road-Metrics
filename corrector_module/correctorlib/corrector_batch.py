import multiprocessing
import queue
import time
import traceback

from . import database_manager
from . import document_manager
from .corrector_worker import CorrectorWorker
from .logger_manager import LoggerManager


class CorrectorBatch:
    def __init__(self, settings):
        self.settings = settings

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
            logger_m = LoggerManager(self.settings.LOGGER_NAME, self.settings.MODULE)
            msg = "Error: {0} {1}".format(repr(e), traceback.format_exc()).replace("\n", "")
            logger_m.log_error('corrector_batch_run', msg)
            # Raise exception again
            raise e

    def _batch_run(self, process_dict):
        """
        Gets raw documents, groups by "messageId", corrects documents' structure, initializes workers,
        updates timeout documents to "done", removes duplicates from raw_messages.
        :param process_dict:
        :return: Returns the amount of documents still to process.
        """

        doc_len = 0
        start_processing_time = time.time()
        logger_m = LoggerManager(self.settings.LOGGER_NAME, self.settings.MODULE)
        logger_m.log_heartbeat(
            "processing", self.settings.HEARTBEAT_LOGGER_PATH, self.settings.HEARTBEAT_FILE, "SUCCEEDED")
        logger_m.log_info('corrector_batch_start', 'Starting corrector - Version {0}'.format(LoggerManager.__version__))

        # Start Database Manager
        db_m = database_manager.DatabaseManager(self.settings)
        # Start Document Manager
        doc_m = document_manager.DocumentManager(self.settings)

        # Get documents from raw collection
        cursor = db_m.get_raw_documents(limit=self.settings.CORRECTOR_DOCUMENTS_LIMIT)
        logger_m.log_info('corrector_batch_raw', 'Processing {0} raw documents'.format(len(cursor)))

        # Aggregate documents by message id
        # Correct missing fields
        doc_map = {}
        for _doc in cursor:
            message_id = _doc.get('messageId', '')
            if message_id not in doc_map:
                doc_map[message_id] = []
            fix_doc = doc_m.correct_structure(_doc)
            doc_map[message_id].append(fix_doc)

        # Build queue to be processed
        list_to_process = multiprocessing.Queue()
        duplicates = multiprocessing.Value('i', 0, lock=True)

        m = multiprocessing.Manager()
        to_remove_queue = m.Queue()

        for message_id in doc_map:
            documents = doc_map[message_id]
            data = dict()
            data['logger_manager'] = logger_m
            data['document_manager'] = doc_m
            data['message_id'] = message_id
            data['documents'] = documents
            data['to_remove_queue'] = to_remove_queue
            list_to_process.put(data)
            doc_len += len(documents)

        # Sync
        # time.sleep(5)

        # Create pool of workers
        pool = []
        for i in range(self.settings.THREAD_COUNT):
            # Configure worker
            worker = CorrectorWorker(self.settings, 'worker_{0}'.format(i))
            p = multiprocessing.Process(target=worker.run, args=(list_to_process, duplicates))
            pool.append(p)

        # Starts all pool process
        for p in pool:
            p.start()
        # Wait all processes to finish their jobs
        for p in pool:
            p.join()

        logger_m.log_info('corrector_batch_update_timeout',
                          "Updating timed out [{0} days] orphans to done.".format(self.settings.CORRECTOR_TIMEOUT_DAYS))

        # Update Status of older documents according to client.requestInTs
        cursor = db_m.get_timeout_documents_client(self.settings.CORRECTOR_TIMEOUT_DAYS,
                                            limit=self.settings.CORRECTOR_DOCUMENTS_LIMIT)
        list_of_docs = list(cursor)
        number_of_updated_docs = db_m.update_old_to_done(list_of_docs)

        if number_of_updated_docs > 0:
            logger_m.log_info('corrector_batch_update_client_old_to_done',
                              "Total of {0} orphans from Client updated to status 'done'.".format(number_of_updated_docs))
        else:
            logger_m.log_info('corrector_batch_update_client_old_to_done',
                              "No orphans updated to done.")

        doc_len += number_of_updated_docs

        # Update Status of older documents according to producer.requestInTs
        cursor = db_m.get_timeout_documents_producer(self.settings.CORRECTOR_TIMEOUT_DAYS,
                                            limit=self.settings.CORRECTOR_DOCUMENTS_LIMIT)
        list_of_docs = list(cursor)
        number_of_updated_docs = db_m.update_old_to_done(list_of_docs)

        if number_of_updated_docs > 0:
            logger_m.log_info('corrector_batch_update_producer_old_to_done',
                              "Total of {0} orphans from Producer updated to status 'done'.".format(number_of_updated_docs))
        else:
            logger_m.log_info('corrector_batch_update_producer_old_to_done',
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
            logger_m.log_info('corrector_batch_remove_duplicates_from_raw',
                              "Total of {0} duplicate documents removed from raw messages.".format(total_raw_removed))
        else:
            logger_m.log_info('corrector_batch_remove_duplicates_from_raw',
                              "No raw documents marked to removal.")

        doc_len += total_raw_removed

        end_processing_time = time.time()
        total_time = time.strftime("%H:%M:%S", time.gmtime(end_processing_time - start_processing_time))
        msg = ["Number of duplicates: {0}".format(duplicates.value),
               "Documents processed: " + str(doc_len),
               "Processing time: {0}".format(total_time)]

        logger_m.log_info('corrector_batch_end', ' | '.join(msg))
        logger_m.log_heartbeat(
            "finished", self.settings.HEARTBEAT_LOGGER_PATH, self.settings.HEARTBEAT_FILE, "SUCCEEDED")
        process_dict['doc_len'] = doc_len
