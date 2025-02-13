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

import queue

from . import database_manager

from opmon_corrector import SECURITY_SERVER_TYPE_CLIENT
from opmon_corrector import SECURITY_SERVER_TYPE_PRODUCER


class CorrectorWorker:

    def __init__(self, settings, name):
        self.settings = settings
        self.db_m = None
        self.worker_name = name

    def run(self, to_process, duplicates, job_type='consume'):
        """ Process run entry point
        :param to_process: Queue of documents to be processed
        :param duplicates: Variable to hold the number of duplicates
        :param job_type: Job type (consume / timeout)
        :return: None
        """
        self.db_m = database_manager.DatabaseManager(self.settings)
        try:
            # Process queue while is not empty
            while True:
                data = to_process.get(True, 1)
                if job_type == 'consume':
                    duplicate_count = self.consume_data(data)
                    with duplicates.get_lock():
                        duplicates.value += duplicate_count
                elif job_type == 'faulty':
                    self.consume_faulty_data(data)
                elif job_type == 'timeout':
                    self.db_m.update_old_doc_to_done(data)
        except queue.Empty:
            pass

    def consume_data(self, data):
        """
        The Corrector worker. Processes a batch of documents with the same xRequestId
        :param data: Contains LoggerManager, DocumentManager, x_request_id and documents to be
        processed.
        :return: Returns number of duplicates found.
        """
        # Get parameters
        # logger_manager = data['logger_manager']
        doc_m = data['document_manager']
        x_request_id = data['x_request_id']
        documents = []
        for _doc in data['documents']:
            sanitized_doc = doc_m.sanitize_document(_doc)
            fix_doc = doc_m.correct_structure(sanitized_doc)
            documents.append(fix_doc)
        duplicates = 0

        matched_pair = {}
        clients = [
            doc for doc in documents
            if doc.get('securityServerType', '').lower() == SECURITY_SERVER_TYPE_CLIENT
        ]
        producers = [
            doc for doc in documents
            if doc.get('securityServerType', '').lower() == SECURITY_SERVER_TYPE_PRODUCER
        ]

        if clients:
            if not self.db_m.check_clean_document_exists(x_request_id, clients[0]):
                matched_pair['client'] = clients[0]

        if producers:
            if not self.db_m.check_clean_document_exists(x_request_id, producers[0]):
                matched_pair['producer'] = producers[0]

        docs_to_remove = [
            doc for doc in documents
            if (
                doc != matched_pair.get('client')
                and doc != matched_pair.get('producer')
            )
        ]
        for current_document in docs_to_remove:
            self.db_m.remove_duplicate_from_raw(current_document['_id'])
            duplicates += 1
            """
            :logger_manager.log_warning('batch_duplicated',
            :'_id : ObjectId(\'' + str(current_document['_id']) + '\'),
            :messageId : ' + str(current_document['messageId']))
            """

        if not matched_pair:
            return duplicates

        message_id = (
            matched_pair.get('client', {}).get('messageId')
            or matched_pair.get('producer', {}).get('messageId') or ''
        )

        # Let's find processing party in processing clean_data
        if len(matched_pair) == 1:
            doc = matched_pair.get('client') or matched_pair.get('producer')
            clean_document = self.db_m.get_clean_document(doc)

            if clean_document:
                if doc['securityServerType'].lower() == SECURITY_SERVER_TYPE_CLIENT:
                    clean_document['client'] = doc
                    clean_document = doc_m.apply_calculations(clean_document)
                else:
                    clean_document['producer'] = doc
                    clean_document = doc_m.apply_calculations(clean_document)

                if clean_document['correctorStatus'] == 'processing':
                    # Updating correctorTime value only when document is in 'processing' status
                    # Updating correctorTime value when document is in 'done' status
                    # may trigger anonymizer to insert duplicate value to opendata
                    clean_document['correctorTime'] = database_manager.get_timestamp()
                clean_document['correctorStatus'] = 'done'
                clean_document['matchingType'] = 'regular_pair'
                clean_document['xRequestId'] = x_request_id
                doc_m.correct_client_rest_path(clean_document['client'], clean_document['producer'])
                self.db_m.update_document_clean_data(clean_document)
                self._post_consume_raw_document(matched_pair.get('client'), matched_pair.get('producer'))
                return duplicates

        corrected_document = doc_m.create_json(
            matched_pair.get('client'), matched_pair.get('producer'), x_request_id
        )
        corrected_document = doc_m.apply_calculations(corrected_document)
        corrected_document['correctorTime'] = database_manager.get_timestamp()
        corrected_document['correctorStatus'] = 'done' if len(matched_pair) > 1 else 'processing'
        corrected_document['matchingType'] = 'regular_pair' if len(matched_pair) > 1 else 'orphan'
        corrected_document['messageId'] = message_id
        doc_m.correct_client_rest_path(corrected_document['client'], corrected_document['producer'])
        self.db_m.add_to_clean_data(corrected_document)
        self._post_consume_raw_document(matched_pair.get('client'), matched_pair.get('producer'))

        return duplicates

    def consume_faulty_data(self, data):
        """
        The Corrector worker for faulty documents without xRequestId.
        :param data: Contains LoggerManager, DocumentManager and document to be processed.
        :return: None.
        """
        # Get parameters
        # logger_manager = data['logger_manager']
        doc_m = data['document_manager']
        sanitized_doc = doc_m.sanitize_document(data['document'])
        fixed_doc = doc_m.correct_structure(sanitized_doc)
        producer = fixed_doc if (
            fixed_doc['securityServerType'].lower() == SECURITY_SERVER_TYPE_PRODUCER) else None
        client = fixed_doc if (
            fixed_doc['securityServerType'].lower() == SECURITY_SERVER_TYPE_CLIENT) else None
        cleaned_document = doc_m.create_json(
            client, producer, ''
        )
        cleaned_document = doc_m.apply_calculations(cleaned_document)
        cleaned_document['correctorTime'] = database_manager.get_timestamp()
        cleaned_document['correctorStatus'] = 'done'
        cleaned_document['xRequestId'] = ''
        cleaned_document['matchingType'] = 'orphan'
        cleaned_document['messageId'] = fixed_doc.get('message_id') or ''
        doc_m.correct_client_rest_path(client, producer)
        self.db_m.add_to_clean_data(cleaned_document)
        self._post_consume_raw_document(client, producer)

    def _post_consume_raw_document(self, client: dict, producer: dict):
        """
        Post consume raw document. If client has a restPath, correct it and mark client and producer as corrected.
        Otherwise, just mark client and producer as corrected.
        :param client: Client document.
        :param producer: Producer document.
        :return: None.
        """
        if client:
            if client and client.get('restPath'):
                rest_path = producer.get('restPath') if producer and producer.get('restPath') else "/*"
                self.db_m.mark_as_corrected_and_correct_rest_path(client, rest_path)
            else:
                self.db_m.mark_as_corrected(client)
        if producer:
            self.db_m.mark_as_corrected(producer)
