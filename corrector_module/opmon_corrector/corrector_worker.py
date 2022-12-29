
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
        The Corrector worker. Processes a batch of documents with the same xRequestId
        :param data: Contains LoggerManager, DatabaseManager, DocumentManager, x_request_id and documents to be processed.
        :return: Returns number of duplicates found.
        """
        # Get parameters
        logger_manager = data['logger_manager']
        doc_m = data['document_manager']
        x_request_id = data['x_request_id']
        documents = data['documents']
        to_remove_queue = data['to_remove_queue']
        duplicates = no_requestInTs = 0

        matched_pair = {}
        clients = [
            doc for doc in documents
            if doc.get('securityServerType') == 'Client'
        ]
        producers = [
            doc for doc in documents if doc.get('securityServerType') == 'Producer'
        ]

        if clients:
            matched_pair['client'] = clients[0]

        if producers:
            matched_pair['producer'] = producers[0]

        docs_to_remove = [
            doc for doc in documents
            if (
                doc != matched_pair.get('client')
                and doc != matched_pair.get('producer')
            )
        ]
        for current_document in docs_to_remove:

            # Mark to removal documents without requestInTs immediately (as of bug in xRoad software ver 6.22.0) # noqa
            if (
                current_document['requestInTs'] is None
                and current_document['securityServerType'] is None
            ):
                to_remove_queue.put(current_document['_id'])
                no_requestInTs += 1
                self.db_m.mark_as_corrected(current_document)
                """
                :logger_manager.log_warning('no_requestInTs',
                :'_id : ObjectId(\'' + str(current_document['_id']) + '\'),
                :messageId : ' + str(current_document['messageId']))
                """
                continue

            if self.db_m.check_clean_document_exists(
                    x_request_id, current_document
            ):
                to_remove_queue.put(current_document['_id'])
                duplicates += 1
                self.db_m.mark_as_corrected(current_document)
                continue

            # duplicates
            to_remove_queue.put(current_document['_id'])
            duplicates += 1
            self.db_m.mark_as_corrected(current_document)
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
            clean_document = self.db_m.get_processing_document(doc)

            if clean_document:
                if doc['securityServerType'] == 'Client':
                    clean_document['client'] = doc
                    clean_document = doc_m.apply_calculations(clean_document)
                else:
                    clean_document['producer'] = doc
                    clean_document = doc_m.apply_calculations(clean_document)

                clean_document['correctorTime'] = database_manager.get_timestamp()
                clean_document['correctorStatus'] = 'done'
                clean_document['matchingType'] = 'regular_pair'
                clean_document['xRequestId'] = x_request_id
                self.db_m.update_document_clean_data(clean_document)
                self.db_m.mark_as_corrected(doc)
                return duplicates

        corrected_document = doc_m.create_json(
            matched_pair.get('client'), matched_pair.get('producer'), x_request_id
        )
        corrected_document = doc_m.apply_calculations(corrected_document)
        corrected_document['correctorTime'] = database_manager.get_timestamp()
        corrected_document['correctorStatus'] = 'done' if len(matched_pair) > 1 else 'processing'
        corrected_document['matchingType'] = 'regular_pair' if len(matched_pair) > 1 else 'orphan'
        corrected_document['messageId'] = message_id
        self.db_m.add_to_clean_data(corrected_document)

        for party in matched_pair:
            self.db_m.mark_as_corrected(matched_pair[party])

        if no_requestInTs:
            msg = '[{0}] {1} document(s) without requestInTs present'.format(self.worker_name, no_requestInTs)
            logger_manager.log_warning('corrector_no_requestInTs', msg)

        return duplicates
