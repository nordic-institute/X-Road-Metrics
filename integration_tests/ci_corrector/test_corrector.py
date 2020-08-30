
import unittest
import random

from integration_tests.helpers import ci_helper
from integration_tests.helpers import cl_db_handler
from integration_tests.ci_corrector.ci_corrector_settings import Settings
from corrector_module.correctorlib.corrector_batch import CorrectorBatch

random.seed(42)


class TestCorrectorCI(unittest.TestCase):

    def test_simple_pair_match(self):

        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_simple_pair_match')
        mongodb_h = cl_db_handler.MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()

        # Configure test scenario
        settings.CORRECTOR_DOCUMENTS_LIMIT = 10
        total_raw_documents = 2

        # Add pairs
        raw_documents = []
        for i in range(int(total_raw_documents / 2)):
            client, producer = ci_helper.create_raw_document_pair()
            raw_documents.append(client.copy())
            raw_documents.append(producer.copy())
        mongodb_h.add_raw_documents(raw_documents)

        # Run Corrector
        c_batch = CorrectorBatch(settings)
        process_dict = dict()
        process_dict['doc_len'] = -1
        c_batch.run(process_dict)

        # Total raw documents should be 2
        self.assertEqual(process_dict['doc_len'], 2)
        clean_docs = mongodb_h.get_clean_documents()

        # Documents are a pair
        self.assertEqual(len(clean_docs), 1)

        # It is a regular match
        doc = clean_docs[0]
        self.assertEqual(doc['matchingType'], 'regular_pair')

        # Clean before exit
        mongodb_h.remove_all()

    def test_multiple_pair_match(self):

        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_multiple_pair_match')
        mongodb_h = cl_db_handler.MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()

        # Configure test scenario
        settings.CORRECTOR_DOCUMENTS_LIMIT = 10000
        total_raw_documents = 500
        total_pairs = int(total_raw_documents / 2)

        # Add pairs
        raw_documents = []
        for i in range(total_pairs):
            client, producer = ci_helper.create_raw_document_pair()
            raw_documents.append(client.copy())
            raw_documents.append(producer.copy())
        mongodb_h.add_raw_documents(raw_documents)

        # Run Corrector
        c_batch = CorrectorBatch(settings)
        process_dict = dict()
        process_dict['doc_len'] = -1
        c_batch.run(process_dict)

        # Total raw documents
        self.assertEqual(process_dict['doc_len'], total_raw_documents)
        clean_docs = mongodb_h.get_clean_documents()

        # Documents are a pair
        self.assertEqual(len(clean_docs), total_pairs)

        # If all are regular_pair, set size is 1
        match_type_set = set([x['matchingType'] for x in clean_docs])
        self.assertEqual(len(match_type_set), 1)

        # Clean before exit
        mongodb_h.remove_all()

    def test_multiple_batch_pair_match(self):

        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_multiple_batch_pair_match')
        mongodb_h = cl_db_handler.MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()

        # Configure test scenario
        settings.CORRECTOR_DOCUMENTS_LIMIT = 100
        total_raw_documents = 500
        total_pairs = int(total_raw_documents / 2)
        total_steps = 5

        # Add pairs
        raw_documents = []
        for i in range(total_pairs):
            client, producer = ci_helper.create_raw_document_pair()
            raw_documents.append(client.copy())
            raw_documents.append(producer.copy())
        mongodb_h.add_raw_documents(raw_documents)

        # Run Corrector Multiple Steps
        c_batch = CorrectorBatch(settings)
        docs_processed = 0
        for i in range(total_steps):
            process_dict = dict()
            process_dict['doc_len'] = -1
            c_batch.run(process_dict)
            self.assertNotEqual(process_dict['doc_len'], -1)
            docs_processed += process_dict['doc_len']

        # Total raw documents
        self.assertEqual(docs_processed, total_raw_documents)
        clean_docs = mongodb_h.get_clean_documents()

        # Documents are a pair
        self.assertEqual(len(clean_docs), total_pairs)

        # If all are regular_pair, set size is 1
        match_type_set = set([x['matchingType'] for x in clean_docs])
        self.assertEqual(len(match_type_set), 1)

        # Clean before exit
        mongodb_h.remove_all()

    def test_simple_duplicates_match(self):

        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_simple_duplicates_match')
        mongodb_h = cl_db_handler.MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()

        # Configure test scenario
        settings.CORRECTOR_DOCUMENTS_LIMIT = 10000

        # 100 unique documents, duplicated 5 times
        total_unique_documents = 100
        total_duplicate_documents = 400
        total_raw_documents = total_unique_documents + total_duplicate_documents

        total_unique_pairs = int(total_unique_documents / 2)

        unique_raw_documents = []
        for i in range(total_unique_pairs):
            client, producer = ci_helper.create_raw_document_pair()
            unique_raw_documents.append(client.copy())
            unique_raw_documents.append(producer.copy())

        raw_documents = []
        for i in range(total_raw_documents):
            i_doc = i % total_unique_documents
            doc = unique_raw_documents[i_doc].copy()
            raw_documents.append(doc)

        mongodb_h.add_raw_documents(raw_documents)

        # Run Corrector
        c_batch = CorrectorBatch(settings)
        process_dict = dict()
        process_dict['doc_len'] = -1
        c_batch.run(process_dict)

        # Total raw documents
        self.assertEqual(process_dict['doc_len'], total_raw_documents)

        # Check total Pair documents
        clean_docs = mongodb_h.get_clean_documents()
        self.assertEqual(len(clean_docs), total_unique_pairs)

        # Check total raw documents after duplicate removal
        raw_docs = mongodb_h.get_raw_documents()
        self.assertEqual(len(raw_docs), total_unique_documents)

        # If all are regular_pair, set size is 1
        match_type_set = set([x['matchingType'] for x in clean_docs])
        self.assertEqual(len(match_type_set), 1)

        # Clean before exit
        mongodb_h.remove_all()

    def test_multiple_batch_duplicates_match(self):

        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_multiple_batch_duplicates_match')
        mongodb_h = cl_db_handler.MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()

        # Configure test scenario
        settings.CORRECTOR_DOCUMENTS_LIMIT = 100
        total_steps = 5

        # 100 unique documents, duplicated 5 times
        total_unique_documents = 100
        total_duplicate_documents = 400
        total_raw_documents = total_unique_documents + total_duplicate_documents

        total_unique_pairs = int(total_unique_documents / 2)

        unique_raw_documents = []
        for i in range(total_unique_pairs):
            client, producer = ci_helper.create_raw_document_pair()
            unique_raw_documents.append(client.copy())
            unique_raw_documents.append(producer.copy())

        raw_documents = []
        for i in range(total_raw_documents):
            i_doc = i % total_unique_documents
            doc = unique_raw_documents[i_doc].copy()
            raw_documents.append(doc)

        # Break the documents pair order before adding to MongoDB
        random.shuffle(raw_documents)
        mongodb_h.add_raw_documents(raw_documents)

        # Run Corrector Multiple Steps
        c_batch = CorrectorBatch(settings)
        docs_processed = 0
        for i in range(total_steps):
            process_dict = dict()
            process_dict['doc_len'] = -1
            c_batch.run(process_dict)
            self.assertNotEqual(process_dict['doc_len'], -1)
            docs_processed += process_dict['doc_len']

        # Total raw documents
        self.assertEqual(docs_processed, total_raw_documents)

        # Check total Pair documents
        clean_docs = mongodb_h.get_clean_documents()
        self.assertEqual(len(clean_docs), total_unique_pairs)

        # If all are regular_pair, set size is 1
        match_type_set = set([x['matchingType'] for x in clean_docs])
        self.assertEqual(len(match_type_set), 1)

        # Clean before exit
        mongodb_h.remove_all()

    def test_simple_all_producer_duplicates_match(self):

        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_simple_all_producer_duplicates_match')
        mongodb_h = cl_db_handler.MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()

        # Configure test scenario
        settings.CORRECTOR_DOCUMENTS_LIMIT = 100

        # 100 unique documents, duplicated 5 times
        total_unique_documents = 1
        total_duplicate_documents = 9
        total_raw_documents = total_unique_documents + total_duplicate_documents

        total_unique_pairs = 1

        unique_raw_documents = []
        for i in range(total_unique_pairs):
            client, producer = ci_helper.create_raw_document_pair()
            # Only producer
            unique_raw_documents.append(producer.copy())

        raw_documents = []
        for i in range(total_raw_documents):
            doc = unique_raw_documents[0].copy()
            raw_documents.append(doc)

        mongodb_h.add_raw_documents(raw_documents)

        # Run Corrector Multiple Steps
        c_batch = CorrectorBatch(settings)
        process_dict = dict()
        process_dict['doc_len'] = -1
        c_batch.run(process_dict)

        # Total raw documents
        self.assertEqual(process_dict['doc_len'], total_raw_documents)

        # Check total Pair documents
        clean_docs = mongodb_h.get_clean_documents()
        self.assertEqual(len(clean_docs), total_unique_pairs)

        # If all are orphan, set size is 1
        match_type_set = set([x['matchingType'] for x in clean_docs])
        self.assertEqual(len(match_type_set), 1)

        # The only document should be orphan
        self.assertEqual(clean_docs[0]['matchingType'], 'orphan')

        # Clean before exit
        mongodb_h.remove_all()

    def test_multiple_all_producer_duplicates_match(self):

        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_multiple_all_producer_duplicates_match')
        mongodb_h = cl_db_handler.MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()

        # Configure test scenario
        settings.CORRECTOR_DOCUMENTS_LIMIT = 10
        total_steps = 10

        # 100 unique documents, duplicated 5 times
        total_unique_documents = 1
        total_duplicate_documents = 99
        total_raw_documents = total_unique_documents + total_duplicate_documents

        total_unique_pairs = 1

        unique_raw_documents = []
        for i in range(total_unique_pairs):
            client, producer = ci_helper.create_raw_document_pair()
            # Only producer
            unique_raw_documents.append(producer.copy())

        raw_documents = []
        for i in range(total_raw_documents):
            doc = unique_raw_documents[0].copy()
            raw_documents.append(doc)

        mongodb_h.add_raw_documents(raw_documents)

        # Run Corrector Multiple Steps
        c_batch = CorrectorBatch(settings)
        docs_processed = 0
        for i in range(total_steps):
            process_dict = dict()
            process_dict['doc_len'] = -1
            c_batch.run(process_dict)
            self.assertNotEqual(process_dict['doc_len'], -1)
            docs_processed += process_dict['doc_len']

        # Total raw documents
        self.assertEqual(docs_processed, total_raw_documents)

        # Check total Pair documents
        clean_docs = mongodb_h.get_clean_documents()
        self.assertEqual(len(clean_docs), total_unique_pairs)

        # If all are orphan, set size is 1
        match_type_set = set([x['matchingType'] for x in clean_docs])
        self.assertEqual(len(match_type_set), 1)

        # The only document should be orphan
        self.assertEqual(clean_docs[0]['matchingType'], 'orphan')

        # Clean before exit
        mongodb_h.remove_all()

    def test_simple_orphan_pair_match(self):

        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_simple_orphan_pair_match')
        mongodb_h = cl_db_handler.MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()

        # Configure test scenario
        settings.CORRECTOR_DOCUMENTS_LIMIT = 10
        total_raw_documents = 2

        # Add pairs
        raw_documents = []
        for i in range(int(total_raw_documents / 2)):
            client, producer = ci_helper.create_raw_document_pair(orphan_match=True)
            raw_documents.append(client.copy())
            raw_documents.append(producer.copy())
        mongodb_h.add_raw_documents(raw_documents)

        # Run Corrector
        c_batch = CorrectorBatch(settings)
        process_dict = dict()
        process_dict['doc_len'] = -1
        c_batch.run(process_dict)

        # Total raw documents should be 2
        self.assertEqual(process_dict['doc_len'], 2)
        clean_docs = mongodb_h.get_clean_documents()

        # Documents are a pair
        self.assertEqual(len(clean_docs), 1)

        # It is a regular match
        doc = clean_docs[0]
        self.assertEqual(doc['matchingType'], 'orphan_pair')

        # Clean before exit
        mongodb_h.remove_all()

    def test_multiple_orphan_pair_match(self):

        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_multiple_orphan_pair_match')
        mongodb_h = cl_db_handler.MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()

        # Configure test scenario
        settings.CORRECTOR_DOCUMENTS_LIMIT = 20
        total_raw_documents = 100
        total_pairs = int(total_raw_documents / 2)
        total_steps = 5

        # Add pairs
        raw_documents = []
        for i in range(total_pairs):
            client, producer = ci_helper.create_raw_document_pair(orphan_match=True)
            raw_documents.append(client.copy())
            raw_documents.append(producer.copy())
        mongodb_h.add_raw_documents(raw_documents)

        # Run Corrector Multiple Steps
        c_batch = CorrectorBatch(settings)
        docs_processed = 0
        for i in range(total_steps):
            process_dict = dict()
            process_dict['doc_len'] = -1
            c_batch.run(process_dict)
            self.assertNotEqual(process_dict['doc_len'], -1)
            docs_processed += process_dict['doc_len']

        # Total raw documents
        self.assertEqual(docs_processed, total_raw_documents)
        clean_docs = mongodb_h.get_clean_documents()

        # Documents are a pair
        self.assertEqual(len(clean_docs), total_pairs)

        # If all are regular_pair, set size is 1
        match_type_set = set([x['matchingType'] for x in clean_docs])
        self.assertEqual(len(match_type_set), 1)

        # Clean before exit
        mongodb_h.remove_all()

    def test_multiple_many_matchingType_match(self):

        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_multiple_orphan_pair_match')
        mongodb_h = cl_db_handler.MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()
        # Scenario:
        # 5 orphan pairs (10 docs)
        # 5 regular pairs (10 docs)
        # 5 orphans (5 docs)

        # Configure test scenario
        settings.CORRECTOR_DOCUMENTS_LIMIT = 5
        total_raw_documents = 25
        total_pairs = 15
        total_steps = 5

        raw_documents = []
        # Add pairs multiple matchingType
        # Orphan pairs
        for i in range(5):
            client, producer = ci_helper.create_raw_document_pair(orphan_match=True)
            raw_documents.append(client.copy())
            raw_documents.append(producer.copy())
        # Regular pairs
        for i in range(5):
            client, producer = ci_helper.create_raw_document_pair()
            raw_documents.append(client.copy())
            raw_documents.append(producer.copy())
        # Orphans
        for i in range(5):
            client, producer = ci_helper.create_raw_document_pair()
            # Only client documents
            raw_documents.append(client.copy())

        random.shuffle(raw_documents)
        mongodb_h.add_raw_documents(raw_documents)

        # Run Corrector Multiple Steps
        c_batch = CorrectorBatch(settings)
        docs_processed = 0
        for i in range(total_steps):
            process_dict = dict()
            process_dict['doc_len'] = -1
            c_batch.run(process_dict)
            self.assertNotEqual(process_dict['doc_len'], -1)
            docs_processed += process_dict['doc_len']

        # Total raw documents
        self.assertEqual(docs_processed, total_raw_documents)
        clean_docs = mongodb_h.get_clean_documents()

        # Documents are a pair
        self.assertEqual(len(clean_docs), total_pairs)

        # If all are regular_pair, set size is 1
        matching_type_freq = {}
        for x in clean_docs:
            k = x['matchingType']
            if k not in matching_type_freq:
                matching_type_freq[k] = 0
            matching_type_freq[k] += 1

        self.assertEqual(matching_type_freq.get('orphan', None), 5)
        self.assertEqual(matching_type_freq.get('regular_pair', None), 5)
        self.assertEqual(matching_type_freq.get('orphan_pair', None), 5)

        # Clean before exit
        mongodb_h.remove_all()

    def test_producer_matching_with_orphan_client(self):

        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_producer_matching_with_orphan_client')
        mongodb_h = cl_db_handler.MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()

        # Configure test scenario
        settings.CORRECTOR_DOCUMENTS_LIMIT = 5
        total_clean_documents = 30
        total_steps = 6

        raw_documents = []
        clean_documents = []

        # Create pair documents, but make the client be none in the clean data
        for i in range(total_clean_documents):
            clean_doc = ci_helper.create_clean_document()
            producer = clean_doc['producer']
            clean_doc['producer'] = None
            clean_doc['producerHash'] = None
            clean_doc['matchingType'] = 'orphan'
            clean_documents.append(clean_doc)
            raw_documents.append(producer)

        mongodb_h.add_raw_documents(raw_documents)
        mongodb_h.add_clean_documents(clean_documents)

        # Run Corrector Multiple Steps
        c_batch = CorrectorBatch(settings)
        docs_processed = 0
        for i in range(total_steps):
            process_dict = dict()
            process_dict['doc_len'] = -1
            c_batch.run(process_dict)
            self.assertNotEqual(process_dict['doc_len'], -1)
            docs_processed += process_dict['doc_len']

        # Total raw documents
        self.assertEqual(docs_processed, len(raw_documents))
        clean_docs = mongodb_h.get_clean_documents()

        # Documents are a pair
        self.assertEqual(len(clean_docs), total_clean_documents)

        for d in clean_docs:
            self.assertNotEqual(d['client'], None)
            self.assertNotEqual(d['producer'], None)

        matching_type_freq = {}
        for x in clean_docs:
            k = x['matchingType']
            if k not in matching_type_freq:
                matching_type_freq[k] = 0
            matching_type_freq[k] += 1

        self.assertEqual(matching_type_freq.get('orphan', None), None)
        self.assertEqual(matching_type_freq.get('orphan_pair', None), None)
        self.assertEqual(matching_type_freq.get('regular_pair', None), total_clean_documents)

        # Clean before exit
        mongodb_h.remove_all()

    def test_client_matching_with_orphan_producer(self):

        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_client_matching_with_orphan_producer')
        mongodb_h = cl_db_handler.MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()

        # Configure test scenario
        settings.CORRECTOR_DOCUMENTS_LIMIT = 5
        total_clean_documents = 30
        total_steps = 6

        raw_documents = []
        clean_documents = []

        # Create pair documents, but make the client be none in the clean data
        for i in range(total_clean_documents):
            clean_doc = ci_helper.create_clean_document()
            client = clean_doc['client']
            clean_doc['client'] = None
            clean_doc['clientHash'] = None
            clean_doc['matchingType'] = 'orphan'
            clean_documents.append(clean_doc)
            raw_documents.append(client)

        mongodb_h.add_raw_documents(raw_documents)
        mongodb_h.add_clean_documents(clean_documents)

        # Run Corrector Multiple Steps
        c_batch = CorrectorBatch(settings)
        docs_processed = 0
        for i in range(total_steps):
            process_dict = dict()
            process_dict['doc_len'] = -1
            c_batch.run(process_dict)
            self.assertNotEqual(process_dict['doc_len'], -1)
            docs_processed += process_dict['doc_len']

        # Total raw documents
        self.assertEqual(docs_processed, len(raw_documents))
        clean_docs = mongodb_h.get_clean_documents()

        # Documents are a pair
        self.assertEqual(len(clean_docs), total_clean_documents)

        for d in clean_docs:
            self.assertNotEqual(d['client'], None)
            self.assertNotEqual(d['producer'], None)

        matching_type_freq = {}
        for x in clean_docs:
            k = x['matchingType']
            if k not in matching_type_freq:
                matching_type_freq[k] = 0
            matching_type_freq[k] += 1

        self.assertEqual(matching_type_freq.get('orphan', None), None)
        self.assertEqual(matching_type_freq.get('orphan_pair', None), None)
        self.assertEqual(matching_type_freq.get('regular_pair', None), total_clean_documents)

        # Clean before exit
        mongodb_h.remove_all()

    def test_producer_orphan_matching_with_orphan_client(self):

        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_producer_orphan_matching_with_orphan_client')
        mongodb_h = cl_db_handler.MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()

        # Configure test scenario
        settings.CORRECTOR_DOCUMENTS_LIMIT = 5
        total_clean_documents = 30
        total_steps = 6

        raw_documents = []
        clean_documents = []

        # Create pair documents, but make the client be none in the clean data
        for i in range(total_clean_documents):
            clean_doc = ci_helper.create_clean_document(orphan_match=True)
            producer = clean_doc['producer']
            clean_doc['producer'] = None
            clean_doc['producerHash'] = None
            clean_doc['matchingType'] = 'orphan'
            clean_documents.append(clean_doc)
            raw_documents.append(producer)

        mongodb_h.add_raw_documents(raw_documents)
        mongodb_h.add_clean_documents(clean_documents)

        # Run Corrector Multiple Steps
        c_batch = CorrectorBatch(settings)
        docs_processed = 0
        for i in range(total_steps):
            process_dict = dict()
            process_dict['doc_len'] = -1
            c_batch.run(process_dict)
            self.assertNotEqual(process_dict['doc_len'], -1)
            docs_processed += process_dict['doc_len']

        # Total raw documents
        self.assertEqual(docs_processed, len(raw_documents))
        clean_docs = mongodb_h.get_clean_documents()

        # Documents are a pair
        self.assertEqual(len(clean_docs), total_clean_documents)

        for d in clean_docs:
            self.assertNotEqual(d['client'], None)
            self.assertNotEqual(d['producer'], None)

        matching_type_freq = {}
        for x in clean_docs:
            k = x['matchingType']
            if k not in matching_type_freq:
                matching_type_freq[k] = 0
            matching_type_freq[k] += 1

        self.assertEqual(matching_type_freq.get('orphan', None), None)
        self.assertEqual(matching_type_freq.get('orphan_pair', None), total_clean_documents)
        self.assertEqual(matching_type_freq.get('regular_pair', None), None)

        # Clean before exit
        mongodb_h.remove_all()

    def test_client_orphan_matching_with_orphan_producer(self):

        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_client_orphan_matching_with_orphan_producer')
        mongodb_h = cl_db_handler.MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()

        # Configure test scenario
        settings.CORRECTOR_DOCUMENTS_LIMIT = 5
        total_clean_documents = 30
        total_steps = 6

        raw_documents = []
        clean_documents = []

        # Create pair documents, but make the client be none in the clean data
        for i in range(total_clean_documents):
            clean_doc = ci_helper.create_clean_document(orphan_match=True)
            client = clean_doc['client']
            clean_doc['client'] = None
            clean_doc['clientHash'] = None
            clean_doc['matchingType'] = 'orphan'
            clean_documents.append(clean_doc)
            raw_documents.append(client)

        mongodb_h.add_raw_documents(raw_documents)
        mongodb_h.add_clean_documents(clean_documents)

        # Run Corrector Multiple Steps
        c_batch = CorrectorBatch(settings)
        docs_processed = 0
        for i in range(total_steps):
            process_dict = dict()
            process_dict['doc_len'] = -1
            c_batch.run(process_dict)
            self.assertNotEqual(process_dict['doc_len'], -1)
            docs_processed += process_dict['doc_len']

        # Total raw documents
        self.assertEqual(docs_processed, len(raw_documents))
        clean_docs = mongodb_h.get_clean_documents()

        # Documents are a pair
        self.assertEqual(len(clean_docs), total_clean_documents)

        for d in clean_docs:
            self.assertNotEqual(d['client'], None)
            self.assertNotEqual(d['producer'], None)

        matching_type_freq = {}
        for x in clean_docs:
            k = x['matchingType']
            if k not in matching_type_freq:
                matching_type_freq[k] = 0
            matching_type_freq[k] += 1

        self.assertEqual(matching_type_freq.get('orphan', None), None)
        self.assertEqual(matching_type_freq.get('orphan_pair', None), total_clean_documents)
        self.assertEqual(matching_type_freq.get('regular_pair', None), None)

        # Clean before exit
        mongodb_h.remove_all()

    def test_pair_match_with_duplicate_messageId(self):

        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_pair_match_with_duplicate_messageId')
        mongodb_h = cl_db_handler.MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()

        # Configure test scenario
        settings.CORRECTOR_DOCUMENTS_LIMIT = 10000
        total_pairs_with_unique_message_id = 100
        total_pairs_with_same_message_id = 100

        total_pairs = total_pairs_with_unique_message_id + total_pairs_with_same_message_id
        total_raw_documents = 2 * total_pairs

        # Add pairs with unique MessageId
        raw_documents = []
        for i in range(total_pairs_with_unique_message_id):
            client, producer = ci_helper.create_raw_document_pair()
            raw_documents.append(client.copy())
            raw_documents.append(producer.copy())

        # Add pairs with duplicate MessageId
        same_message_id = "abcde"
        for i in range(total_pairs_with_same_message_id):
            client, producer = ci_helper.create_raw_document_pair()
            client['messageId'] = same_message_id
            producer['messageId'] = same_message_id
            raw_documents.append(client.copy())
            raw_documents.append(producer.copy())

        # Add all to mongodb
        mongodb_h.add_raw_documents(raw_documents)

        # Run Corrector
        c_batch = CorrectorBatch(settings)
        process_dict = dict()
        process_dict['doc_len'] = -1
        c_batch.run(process_dict)

        # Total raw documents
        self.assertEqual(process_dict['doc_len'], total_raw_documents)
        clean_docs = mongodb_h.get_clean_documents()

        # Documents are a pair
        self.assertEqual(len(clean_docs), total_pairs)

        # If all are regular_pair, set size is 1
        match_type_set = set([x['matchingType'] for x in clean_docs])
        self.assertEqual(len(match_type_set), 1)

        # Clean before exit
        mongodb_h.remove_all()
