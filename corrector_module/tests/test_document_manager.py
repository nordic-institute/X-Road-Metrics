import unittest

from corrector_module.correctorlib.document_manager import DocumentManager
from corrector_module.tests import unit_helper
from corrector_module.tests.unit_settings import Settings


class TestDocumentManager(unittest.TestCase):
    def test_client_calculations(self):

        settings = Settings()
        # Get reference doc
        ref_doc = unit_helper.create_clean_document()

        # Get object to test
        doc_m = DocumentManager(settings)
        new_doc = dict()
        new_doc['client'] = ref_doc['client'].copy()
        new_doc['producer'] = ref_doc['producer'].copy()

        new_doc = doc_m._client_calculations(new_doc)
        new_keys = [k for k in new_doc if k not in ['client', 'producer']]

        # Check if new keys where added after calculation
        self.assertTrue(len(new_keys) > 0)
        # Check if keys match the reference values
        for k in new_keys:
            self.assertEqual(ref_doc[k], new_doc[k], 'Not match key: {0}'.format(k))

    def test_producer_calculations(self):

        settings = Settings()
        # Get reference doc
        ref_doc = unit_helper.create_clean_document()

        # Get object to test
        doc_m = DocumentManager(settings)
        new_doc = dict()
        new_doc['client'] = ref_doc['client'].copy()
        new_doc['producer'] = ref_doc['producer'].copy()

        new_doc = doc_m._producer_calculations(new_doc)
        new_keys = [k for k in new_doc if k not in ['client', 'producer']]

        # Check if new keys where added after calculation
        self.assertTrue(len(new_keys) > 0)
        # Check if keys match the reference values
        for k in new_keys:
            self.assertEqual(ref_doc[k], new_doc[k], 'Not match key: {0}'.format(k))

    def test_pair_calculations(self):

        settings = Settings()
        # Get reference doc
        ref_doc = unit_helper.create_clean_document()

        # Get object to test
        doc_m = DocumentManager(settings)
        new_doc = dict()
        new_doc['client'] = ref_doc['client'].copy()
        new_doc['producer'] = ref_doc['producer'].copy()

        new_doc = doc_m._pair_calculations(new_doc)
        new_keys = [k for k in new_doc if k not in ['client', 'producer']]

        # Check if new keys where added after calculation
        self.assertTrue(len(new_keys) > 0)
        # Check if keys match the reference values
        for k in new_keys:
            self.assertEqual(ref_doc[k], new_doc[k], 'Not match key: {0}'.format(k))

    def test_get_boundary_value(self):
        settings = Settings()

        # Get object to test
        doc_m = DocumentManager(settings)
        self.assertEqual(doc_m.get_boundary_value(5), 5)
        self.assertEqual(doc_m.get_boundary_value(0), 0)
        self.assertEqual(doc_m.get_boundary_value(-7), -7)
        self.assertEqual(doc_m.get_boundary_value(None), None)
        self.assertEqual(doc_m.get_boundary_value(5.0), 5.0)
        self.assertEqual(doc_m.get_boundary_value(-2 ** 31), -2 ** 31 + 1)
        self.assertEqual(doc_m.get_boundary_value(2 ** 31 + 2), 2 ** 31 - 1)

    def test_limit_calculation_values(self):
        settings = Settings()

        # Get object to test
        doc_m = DocumentManager(settings)
        document = unit_helper.create_clean_document()
        apply_check_doc = document.copy()
        apply_check_doc = doc_m._limit_calculation_values(apply_check_doc)
        self.assertEqual(document, apply_check_doc)

        document['clientSsResponseDuration'] = 2 ** 31 + 2
        document['producerSsResponseDuration'] = 2 ** 31 + 2
        document['requestNwDuration'] = 2 ** 31 + 2
        document['totalDuration'] = 2 ** 31 + 2
        document['producerDurationProducerView'] = 2 ** 31 + 2
        document['responseNwDuration'] = 2 ** 31 + 2
        document['producerResponseSize'] = 2 ** 31 + 2
        document['producerDurationClientView'] = 2 ** 31 + 2
        document['clientResponseSize'] = 2 ** 31 + 2
        document['producerSsRequestDuration'] = 2 ** 31 + 2
        document['clientRequestSize'] = 2 ** 31 + 2
        document['clientSsRequestDuration'] = 2 ** 31 + 2
        document['producerRequestSize'] = 2 ** 31 + 2
        document['producerIsDuration'] = 2 ** 31 + 2
        document = doc_m._limit_calculation_values(document)

        apply_check_doc['clientSsResponseDuration'] = 2 ** 31 - 1
        apply_check_doc['producerSsResponseDuration'] = 2 ** 31 - 1
        apply_check_doc['requestNwDuration'] = 2 ** 31 - 1
        apply_check_doc['totalDuration'] = 2 ** 31 - 1
        apply_check_doc['producerDurationProducerView'] = 2 ** 31 - 1
        apply_check_doc['responseNwDuration'] = 2 ** 31 - 1
        apply_check_doc['producerResponseSize'] = 2 ** 31 - 1
        apply_check_doc['producerDurationClientView'] = 2 ** 31 - 1
        apply_check_doc['clientResponseSize'] = 2 ** 31 - 1
        apply_check_doc['producerSsRequestDuration'] = 2 ** 31 - 1
        apply_check_doc['clientRequestSize'] = 2 ** 31 - 1
        apply_check_doc['clientSsRequestDuration'] = 2 ** 31 - 1
        apply_check_doc['producerRequestSize'] = 2 ** 31 - 1
        apply_check_doc['producerIsDuration'] = 2 ** 31 - 1

        self.maxDiff = None
        self.assertEqual(document, apply_check_doc)

        document['clientSsResponseDuration'] = -2 ** 31
        document['producerSsResponseDuration'] = -2 ** 31
        document['requestNwDuration'] = -2 ** 31
        document['totalDuration'] = -2 ** 31
        document['producerDurationProducerView'] = -2 ** 31
        document['responseNwDuration'] = -2 ** 31
        document['producerResponseSize'] = -2 ** 31
        document['producerDurationClientView'] = -2 ** 31
        document['clientResponseSize'] = -2 ** 31
        document['producerSsRequestDuration'] = -2 ** 31
        document['clientRequestSize'] = -2 ** 31
        document['clientSsRequestDuration'] = -2 ** 31
        document['producerRequestSize'] = -2 ** 31
        document['producerIsDuration'] = -2 ** 31
        document = doc_m._limit_calculation_values(document)

        apply_check_doc['clientSsResponseDuration'] = -2 ** 31 + 1
        apply_check_doc['producerSsResponseDuration'] = -2 ** 31 + 1
        apply_check_doc['requestNwDuration'] = -2 ** 31 + 1
        apply_check_doc['totalDuration'] = -2 ** 31 + 1
        apply_check_doc['producerDurationProducerView'] = -2 ** 31 + 1
        apply_check_doc['responseNwDuration'] = -2 ** 31 + 1
        apply_check_doc['producerResponseSize'] = -2 ** 31 + 1
        apply_check_doc['producerDurationClientView'] = -2 ** 31 + 1
        apply_check_doc['clientResponseSize'] = -2 ** 31 + 1
        apply_check_doc['producerSsRequestDuration'] = -2 ** 31 + 1
        apply_check_doc['clientRequestSize'] = -2 ** 31 + 1
        apply_check_doc['clientSsRequestDuration'] = -2 ** 31 + 1
        apply_check_doc['producerRequestSize'] = -2 ** 31 + 1
        apply_check_doc['producerIsDuration'] = -2 ** 31 + 1

        self.maxDiff = None
        self.assertEqual(document, apply_check_doc)

    def test_apply_calculations(self):

        settings = Settings()
        # Get reference doc
        ref_doc = unit_helper.create_clean_document()

        # Get object to test
        doc_m = DocumentManager(settings)
        new_doc = dict()
        new_doc['client'] = ref_doc['client'].copy()
        new_doc['producer'] = ref_doc['producer'].copy()

        new_doc = doc_m.apply_calculations(new_doc)
        new_keys = [k for k in new_doc if k not in ['client', 'producer']]

        # Check if new keys were added after calculation
        self.assertTrue(len(new_keys) > 0)
        # Check if keys match the reference values
        for k in new_keys:
            self.assertEqual(ref_doc[k], new_doc[k], 'Not match key: {0}'.format(k))

    def test_match_documents(self):

        settings = Settings()
        # Get object to test
        doc_m = DocumentManager(settings)

        # Test Regular Valid Pair Client
        ref_doc = unit_helper.create_clean_document()
        client = ref_doc['client']
        ref_doc['client'] = None
        resp = doc_m.match_documents(client, ref_doc)
        self.assertTrue(resp)
        resp = doc_m.match_orphan_documents(client, ref_doc)
        self.assertTrue(resp)

        # Test Regular Valid requestInTs
        # abs(client['requestInTs'] - producer['requestInTs']) < 30000
        client['requestInTs'] = 1
        ref_doc['producer']['requestInTs'] = 20000
        resp = doc_m.match_documents(client, ref_doc)
        self.assertEqual(resp, True)

        # Test Regular Wrong requestInTs
        # abs(client['requestInTs'] - producer['requestInTs']) > 1*60*1000
        client['requestInTs'] = 1
        ref_doc['producer']['requestInTs'] = 2 * 60 * 1000
        resp = doc_m.match_documents(client, ref_doc)
        self.assertEqual(resp, False)

        # Test Regular missing requestInTs
        # abs(client['requestInTs'] - producer['requestInTs']) > 30000
        client['requestInTs'] = None
        ref_doc['producer']['requestInTs'] = 50000
        resp = doc_m.match_documents(client, ref_doc)
        self.assertEqual(resp, False)

        # Test Orphan Valid Pair Client
        ref_doc = unit_helper.create_clean_document(orphan_match=True)
        client = ref_doc['client']
        ref_doc['client'] = None
        resp = doc_m.match_documents(client, ref_doc)
        self.assertFalse(resp)
        resp = doc_m.match_orphan_documents(client, ref_doc)
        self.assertTrue(resp)

        # Test Orphan Valid requestInTs
        # abs(client['requestInTs'] - producer['requestInTs']) < 30000
        client['requestInTs'] = 1
        ref_doc['producer']['requestInTs'] = 20000
        resp = doc_m.match_orphan_documents(client, ref_doc)
        self.assertEqual(resp, True)

        # Test Orphan Wrong requestInTs
        # abs(client['requestInTs'] - producer['requestInTs']) > 30000
        client['requestInTs'] = 1
        ref_doc['producer']['requestInTs'] = 50000
        resp = doc_m.match_orphan_documents(client, ref_doc)
        self.assertEqual(resp, True)

        # Test Orphan missing requestInTs
        # abs(client['requestInTs'] - producer['requestInTs']) > 30000
        client['requestInTs'] = None
        ref_doc['producer']['requestInTs'] = 50000
        resp = doc_m.match_orphan_documents(client, ref_doc)
        self.assertEqual(resp, False)

        # Test different pairs
        ref_doc_a = unit_helper.create_clean_document()
        ref_doc_b = unit_helper.create_clean_document()
        client_a = ref_doc_a['client']
        ref_doc_a['client'] = None
        client_b = ref_doc_b['client']
        ref_doc_b['client'] = None
        resp = doc_m.match_documents(client_a, ref_doc_a)
        self.assertEqual(resp, True)
        resp = doc_m.match_documents(client_b, ref_doc_b)
        self.assertEqual(resp, True)
        resp = doc_m.match_documents(client_b, ref_doc_a)
        self.assertEqual(resp, False)
        resp = doc_m.match_documents(client_a, ref_doc_b)
        self.assertEqual(resp, False)

        # Test invalid match pair client
        ref_doc = unit_helper.create_clean_document()
        client = ref_doc['client']
        ref_doc['producer'] = None
        resp = doc_m.match_documents(client, ref_doc)
        self.assertFalse(resp)
        resp = doc_m.match_orphan_documents(client, ref_doc)
        self.assertFalse(resp)

        # Test invalid match pair producer
        ref_doc = unit_helper.create_clean_document()
        producer = ref_doc['producer']
        ref_doc['client'] = None
        resp = doc_m.match_documents(producer, ref_doc)
        self.assertFalse(resp)
        resp = doc_m.match_orphan_documents(producer, ref_doc)
        self.assertFalse(resp)

    def test_calculate_hash(self):

        # Test without duplicates
        raw_docs = []
        for i in range(1000):
            client, producer = unit_helper.create_raw_document_pair()
            raw_docs.append(client)
            raw_docs.append(producer)

        total_docs = len(raw_docs)
        hash_set = set()
        for d in raw_docs:
            h = DocumentManager.calculate_hash(d)
            hash_set.add(h)

        total_hash = len(hash_set)
        self.assertTrue(total_docs > 0)
        self.assertEqual(total_docs, total_hash)

        # Test with duplicates
        raw_docs = []
        for i in range(1000):
            client, producer = unit_helper.create_raw_document_pair()
            raw_docs.append(client)
            raw_docs.append(producer)
            # Add extra docs
            raw_docs.append(client)
            raw_docs.append(producer)

        total_docs = len(raw_docs)
        hash_set = set()
        for d in raw_docs:
            h = DocumentManager.calculate_hash(d)
            hash_set.add(h)

        total_hash = len(hash_set)
        self.assertTrue(total_docs > 0)
        self.assertEqual(total_docs, 2 * total_hash)

    def test_calculate_hash_variation(self):

        # Test without duplicates
        client_base, _ = unit_helper.create_raw_document_pair()
        client_alter, _ = unit_helper.create_raw_document_pair()

        doc_a = client_base.copy()

        h_a = DocumentManager.calculate_hash(doc_a)
        h_b = DocumentManager.calculate_hash(doc_a)
        self.assertEqual(h_a, h_b)
        # Check if modification of a unique document key
        # producer a new hash
        for k in client_base.keys():
            doc_b = client_base.copy()
            # If client_base and client_alter are equal
            # continue without testing hash (would not change)
            if doc_b[k] == client_alter[k]:
                continue
            doc_b[k] = client_alter[k]
            h_a = DocumentManager.calculate_hash(doc_a)
            h_b = DocumentManager.calculate_hash(doc_b)
            self.assertNotEqual(h_a, h_b, 'Test key: {0}'.format(k))

    def test_find_match(self):

        settings = Settings()
        # Get object to test
        doc_m = DocumentManager(settings)

        # Use case 1 (regular client):

        # create 1 regular pair
        ref_doc = unit_helper.create_clean_document()

        # get client from clean doc & then remove it from the paired doc
        client = ref_doc['client']
        ref_doc['client'] = None

        # create 1000 orphans
        clean_orphans = []
        for i in range(0, 1000):
            orphan_doc = unit_helper.create_clean_document()
            orphan_doc['client'] = None
            clean_orphans.append(orphan_doc)

        # match the client (from pair) with the orphan producers in the orphan list
        paired = doc_m.find_match(client, clean_orphans)
        self.assertEqual(paired, None)

        paired = doc_m.find_orphan_match(client, clean_orphans)
        self.assertEqual(paired, None)

        # create a list with 1000 orphans and 1 matching producer (from pair)
        clean_orphans.append(ref_doc)

        # Find the matching doc and match
        paired = doc_m.find_match(client, clean_orphans)
        self.assertTrue(paired)

        paired = doc_m.find_orphan_match(client, clean_orphans)
        self.assertTrue(paired)

        # Use case 2 (regular producer):

        # create 1 regular pair
        ref_doc = unit_helper.create_clean_document()

        # get producer from clean doc & then remove it from the paired doc
        producer = ref_doc['producer']
        ref_doc['producer'] = None

        # create 1000 orphans
        clean_orphans = []
        for i in range(0, 1000):
            orphan_doc = unit_helper.create_clean_document()
            orphan_doc['producer'] = None
            clean_orphans.append(orphan_doc)

        # match the producer (from pair) with the clients in the orphan list
        paired = doc_m.find_match(producer, clean_orphans)
        self.assertEqual(paired, None)

        paired = doc_m.find_orphan_match(producer, clean_orphans)
        self.assertEqual(paired, None)

        # create a list with 1000 orphans and 1 matching client (from pair)
        clean_orphans.append(ref_doc)

        paired = doc_m.find_match(producer, clean_orphans)
        self.assertTrue(paired)

        paired = doc_m.find_orphan_match(producer, clean_orphans)
        self.assertTrue(paired)

        # Use case 3 (orphan client):

        # create 1 orphan pair
        ref_doc = unit_helper.create_clean_document(orphan_match=True)

        # get client from orphan doc & then remove it from the paired doc
        client = ref_doc['client']
        ref_doc['client'] = None

        # create 1000 orphans
        clean_orphans = []
        for i in range(0, 1000):
            orphan_doc = unit_helper.create_clean_document(orphan_match=True)
            orphan_doc['client'] = None
            clean_orphans.append(orphan_doc)

        # match the client (from pair) with the orphan producers in the orphan list
        paired = doc_m.find_match(client, clean_orphans)
        self.assertEqual(paired, None)

        paired = doc_m.find_orphan_match(client, clean_orphans)
        self.assertEqual(paired, None)

        # create a list with 1000 orphans and 1 matching producer (from pair)
        clean_orphans.append(ref_doc)

        # Find the matching doc and match
        paired = doc_m.find_match(client, clean_orphans)
        self.assertEqual(paired, None)

        paired = doc_m.find_orphan_match(client, clean_orphans)
        self.assertTrue(paired)

        # Use case 4 (orphan producer):

        # create 1 orphan pair
        ref_doc = unit_helper.create_clean_document(orphan_match=True)

        # get producer from orphan doc & then remove it from the paired doc
        producer = ref_doc['producer']
        ref_doc['producer'] = None

        # create 1000 orphans
        clean_orphans = []
        for i in range(0, 1000):
            orphan_doc = unit_helper.create_clean_document(orphan_match=True)
            orphan_doc['producer'] = None
            clean_orphans.append(orphan_doc)

        # match the producer (from pair) with the orphan clients in the orphan list
        paired = doc_m.find_match(producer, clean_orphans)
        self.assertEqual(paired, None)

        paired = doc_m.find_orphan_match(producer, clean_orphans)
        self.assertEqual(paired, None)

        # create a list with 1000 orphans and 1 matching client (from pair)
        clean_orphans.append(ref_doc)

        # Find the matching doc and match
        paired = doc_m.find_match(producer, clean_orphans)
        self.assertEqual(paired, None)

        paired = doc_m.find_orphan_match(producer, clean_orphans)
        self.assertTrue(paired)

    def test_create_json(self):

        settings = Settings()
        # Get object to test
        doc_m = DocumentManager(settings)

        for i in range(0, 1000):
            # Create raw docs (client & producer)
            client, producer = unit_helper.create_raw_document_pair()

            # Calculate hashes
            client_hash = unit_helper.calculate_hash(client)
            producer_hash = unit_helper.calculate_hash(producer)

            # Manually generate the document
            new_doc = dict()
            new_doc['client'] = client
            new_doc['producer'] = producer
            new_doc['clientHash'] = client_hash
            new_doc['producerHash'] = producer_hash
            new_doc['messageId'] = new_doc['client']['messageId']

            # Generate document with function
            default_doc = doc_m.create_json(client, producer, doc_m.calculate_hash(client),
                                            doc_m.calculate_hash(producer), client['messageId'])

            # Compare generated docs
            self.assertEqual(new_doc, default_doc)

    def test_correct_structure(self):

        settings = Settings()
        # Get object to test
        doc_m = DocumentManager(settings)

        # Use case 1: Complete documents

        # Create client & producer
        client, producer = unit_helper.create_raw_document_pair()
        c_client = client.copy()
        c_producer = producer.copy()

        # Try correcting fields
        c_client = doc_m.correct_structure(c_client)
        c_producer = doc_m.correct_structure(c_producer)

        self.assertEqual(c_client, client)
        self.assertEqual(c_producer, producer)

        # Create orphan client & orphan producer
        client, producer = unit_helper.create_raw_document_pair(orphan_match=True)
        c_client = client.copy()
        c_producer = producer.copy()

        # Try correcting fields
        c_client = doc_m.correct_structure(c_client)
        c_producer = doc_m.correct_structure(c_producer)

        self.assertEqual(c_client, client)
        self.assertEqual(c_producer, producer)

        # Use case 2: Totally incomplete documents

        # Create client & producer
        client, producer = unit_helper.create_raw_document_pair()

        # Set all the values of the fields to None
        for key in client:
            if key != "securityServerType":
                client[key] = None
                producer[key] = None

        # Create new client & producer
        new_client = {"securityServerType": "Client"}
        new_producer = {"securityServerType": "Producer"}

        # Fix the new documents
        new_client = doc_m.correct_structure(new_client)
        new_producer = doc_m.correct_structure(new_producer)

        # Change 1 field
        client['clientMemberClass'] = "Something"
        producer['clientMemberClass'] = "Nothing"

        # Compare the results
        self.assertNotEqual(new_client, client)
        self.assertNotEqual(new_producer, producer)

        # Fix the changed field
        client['clientMemberClass'] = None
        producer['clientMemberClass'] = None
        # Compare the results
        self.assertEqual(new_client, client)
        self.assertEqual(new_producer, producer)

        # Use case 3 (Some fields removed):

        # Create orphan client & orphan producer
        client, producer = unit_helper.create_raw_document_pair(orphan_match=True)
        c_client = client.copy()
        c_producer = producer.copy()

        # Remove some fields
        del client['clientMemberClass']
        del client['clientMemberCode']
        del client['messageProtocolVersion']

        del producer['clientMemberClass']
        del producer['clientMemberCode']
        del producer['messageProtocolVersion']

        # Fix the docs
        client = doc_m.correct_structure(client)
        producer = doc_m.correct_structure(producer)

        # Compare the docs
        self.assertNotEqual(c_client, client)
        self.assertNotEqual(c_producer, producer)

        # Fix c_client & c_producer
        c_client['clientMemberClass'] = None
        c_client['clientMemberCode'] = None
        c_client['messageProtocolVersion'] = None
        c_producer['clientMemberClass'] = None
        c_producer['clientMemberCode'] = None
        c_producer['messageProtocolVersion'] = None

        # Compare the docs again
        self.assertEqual(c_client, client)
        self.assertEqual(c_producer, producer)
