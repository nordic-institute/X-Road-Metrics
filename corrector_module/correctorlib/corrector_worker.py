
import queue

from . import database_manager


class CorrectorWorker:

    def __init__(self, settings, name):
        self.settings = settings
        self.db_m = None
        self.worker_name = name

    def run(self, to_process, duplicates):
        """ Process run entry point
        :param to_process: Queue of documents to be processed
        :param duplicates: Variable to hold the number of duplicates
        :return: None
        """
        self.db_m = database_manager.DatabaseManager(self.settings)
        try:
            # Process queue while is not empty
            while True:
                data = to_process.get(True, 1)
                duplicate_count = self.consume_data(data)
                with duplicates.get_lock():
                    duplicates.value += duplicate_count
        except queue.Empty:
            pass

    def consume_data(self, data):
        """
        The Corrector worker. Processes a batch of documents with the same message_id.
        :param data: Contains LoggerManager, DatabaseManager, DocumentManager, message_id and documents to be processed.
        :return: Returns number of duplicates found.
        """
        # Get parameters
        logger_manager = data['logger_manager']
        doc_m = data['document_manager']
        message_id = data['message_id']
        documents = data['documents']
        to_remove_queue = data['to_remove_queue']
        duplicates = no_requestInTs = 0
        hash_set = set()

        for current_document in documents:

            # Mark to removal documents without requestInTs immediately (as of bug in xRoad software ver 6.22.0)
            if current_document['requestInTs'] is None and current_document['securityServerType'] is None:
                to_remove_queue.put(current_document['_id'])
                no_requestInTs += 1
                self.db_m.mark_as_corrected(current_document)
                """
                :logger_manager.log_warning('no_requestInTs',
                :'_id : ObjectId(\'' + str(current_document['_id']) + '\'),
                :messageId : ' + str(current_document['messageId']))
                """
                continue

            # Check if is batch duplicated
            current_document_hash = doc_m.calculate_hash(current_document)
            if current_document_hash in hash_set:
                # If yes, mark to removal
                to_remove_queue.put(current_document['_id'])
                duplicates += 1
                self.db_m.mark_as_corrected(current_document)
                """
                :logger_manager.log_warning('batch_duplicated',
                :'_id : ObjectId(\'' + str(current_document['_id']) + '\'),
                :messageId : ' + str(current_document['messageId']))
                """
                continue

            # Check if is database duplicated
            if self.db_m.check_if_hash_exists(current_document_hash):
                # If here, add to batch duplicate cache
                hash_set.add(current_document_hash)
                duplicates += 1
                self.db_m.mark_as_corrected(current_document)
                """
                :logger_manager.log_warning('database_duplicated',
                :'_id : ObjectId(\'' + str(current_document['_id']) + '\'),
                :messageId : ' + str(current_document['messageId']))
                """
                continue

            # Mark hash as seen
            hash_set.add(current_document_hash)
            # Find possible matching documents
            matching_documents = self.db_m.find_by_message_id(current_document)
            # Try to match the current document with possible pairs (regular)
            merged_document = doc_m.find_match(current_document, matching_documents)
            matching_type = ''

            if merged_document is None:
                # Try to match the current document with orphan-matching
                merged_document = doc_m.find_orphan_match(current_document, matching_documents)
                if merged_document is not None:
                    matching_type = 'orphan_pair'
            else:
                matching_type = 'regular_pair'

            if merged_document is None:
                matching_type = 'orphan'
                if current_document['securityServerType'] == 'Producer':
                    new_document = doc_m.create_json(None, current_document, None, current_document_hash, message_id)
                else:
                    if current_document['securityServerType'] != 'Client':
                        current_document['securityServerType'] = 'Client'
                    new_document = doc_m.create_json(current_document, None, current_document_hash, None, message_id)

                new_document = doc_m.apply_calculations(new_document)
                new_document['correctorTime'] = database_manager.get_timestamp()
                new_document['correctorStatus'] = 'processing'
                new_document['matchingType'] = matching_type

                # Mark non-xRoad queries as 'done' instantly. No reason to wait matching pair
                if 'client' in new_document and new_document['client'] is not None and 'clientXRoadInstance' in new_document['client'] \
                        and new_document['client']['clientXRoadInstance'] is None:
                    new_document['correctorStatus'] = 'done'
                    new_document['matchingType'] = 'orphan'

                self.db_m.add_to_clean_data(new_document)

            else:

                if current_document['securityServerType'] == 'Client':

                    if merged_document['client'] is None:
                        merged_document['client'] = current_document
                        merged_document = doc_m.apply_calculations(merged_document)
                        merged_document['clientHash'] = current_document_hash
                        merged_document['correctorTime'] = database_manager.get_timestamp()
                        merged_document['correctorStatus'] = 'done'
                        merged_document['matchingType'] = matching_type
                        self.db_m.update_document_clean_data(merged_document)
                    else:
                        # This should never-ever happen in >= v0.4.
                        msg = '[{0}] 2 matching clients for 1 producer: {1}'.format(self.worker_name, current_document)
                        logger_manager.log_warning('corrector_merging', msg)

                else:

                    if merged_document['producer'] is None:
                        merged_document['producer'] = current_document
                        merged_document = doc_m.apply_calculations(merged_document)
                        merged_document['producerHash'] = current_document_hash
                        merged_document['correctorTime'] = database_manager.get_timestamp()
                        merged_document['correctorStatus'] = 'done'
                        merged_document['matchingType'] = matching_type
                        self.db_m.update_document_clean_data(merged_document)
                    else:
                        # This should never-ever happen in >= v0.4.
                        msg = '[{0}] 2 matching producers for 1 client: {1}'.format(self.worker_name, current_document)
                        logger_manager.log_error('corrector_merging', msg)

            self.db_m.mark_as_corrected(current_document)

        if no_requestInTs:
            msg = '[{0}] {1} document(s) without requestInTs present'.format(self.worker_name, no_requestInTs)
            logger_manager.log_warning('corrector_no_requestInTs', msg)

        return duplicates
