import os
import json
import unittest
from datetime import datetime

from opendata_module.anonymizer.anonymizer import Anonymizer
from opendata_module.anonymizer.iio.mongodb_manager import MongoDB_Manager
from opendata_module.anonymizer.iio.opendata_writer import OpenDataWriter
from opendata_module.anonymizer.anonymizer_config import AnonymizerConfig

from integration_tests.helpers import cl_db_handler
from integration_tests.helpers.ci_postgres_handler import PostgreSQL_Manager
import integration_tests.ci_anonymizer.ci_anonymizer_settings as settings
from integration_tests.ci_anonymizer.ci_helper import read_data_from_json

TEST_DIR = os.path.abspath(os.path.dirname(__file__))


class TestAnonymizationCI(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None

    def setUp(self):
        # Initialize MongoDB
        self._mongodb_h = cl_db_handler.MongoDBHandler(
            settings.mongo_db['user'], settings.mongo_db['password'], settings.mongo_db['host_address'])
        self._mongodb_h.remove_all()
        self._mongodb_h.create_indexes()

        # Initialize PostgreSQL
        postgres_settings = settings.postgres.copy()
        del postgres_settings['buffer_size']
        del postgres_settings['readonly_users']
        self._postgres_manager = PostgreSQL_Manager(**postgres_settings)
        self._postgres_manager.remove_all()

    def test_anonymizing_no_documents(self):
        # Set up Anonymizer
        config = AnonymizerConfig(os.path.join(TEST_DIR, 'ci_anonymizer_settings.py'))

        # mongodb_h.add_clean_documents([])

        mongo_manager = MongoDB_Manager(config, MockPreviousRunManager(0))
        mongo_manager._logger = MockLogger()

        writer = OpenDataWriter(config)

        anonymizer = Anonymizer(mongo_manager, writer, config)
        anonymized_records = anonymizer.anonymize()

        self.assertEqual(0, anonymized_records)
        self.assertEqual(0, len(self._postgres_manager.get_all_logs()))

    def test_ignoring_processing_documents(self):
        # Add test documents
        documents = read_data_from_json(os.path.join(TEST_DIR, 'data', 'clean_processing_documents.json'))
        self._mongodb_h.add_clean_documents(documents)

        # Set up Anonymizer
        config = AnonymizerConfig(os.path.join(TEST_DIR, 'ci_anonymizer_settings.py'))

        mongo_manager = MongoDB_Manager(config, MockPreviousRunManager(0))
        mongo_manager._logger = MockLogger()

        writer = OpenDataWriter(config)

        anonymizer = Anonymizer(mongo_manager, writer, config)
        anonymized_records = anonymizer.anonymize()

        self.assertEqual(0, anonymized_records)
        self.assertEqual(0, len(self._postgres_manager.get_all_logs()))

    def test_done_and_processing_documents(self):
        # Add test documents
        documents = read_data_from_json(os.path.join(TEST_DIR, 'data', 'clean_documents.json'))
        self._mongodb_h.add_clean_documents(documents)

        # Set up Anonymizer
        config = AnonymizerConfig(os.path.join(TEST_DIR, 'ci_anonymizer_settings.py'))

        mongo_manager = MongoDB_Manager(config, MockPreviousRunManager(0))
        mongo_manager._logger = MockLogger()

        writer = OpenDataWriter(config)

        anonymizer = Anonymizer(mongo_manager, writer, config)
        anonymized_records = anonymizer.anonymize()

        self.assertEqual(5, anonymized_records)
        self.assertEqual(10, len(self._postgres_manager.get_all_logs()))

    def test_anonymizing_outdated_documents(self):
        # Add test documents
        documents = read_data_from_json(os.path.join(TEST_DIR, 'data', 'clean_documents.json'))
        self._mongodb_h.add_clean_documents(documents)

        # Set up Anonymizer
        config = AnonymizerConfig(os.path.join(TEST_DIR, 'ci_anonymizer_settings.py'))

        mongo_manager = MongoDB_Manager(config, MockPreviousRunManager(15079097630))
        mongo_manager._logger = MockLogger()

        writer = OpenDataWriter(config)

        anonymizer = Anonymizer(mongo_manager, writer, config)
        anonymized_records = anonymizer.anonymize()

        self.assertEqual(0, anonymized_records)
        self.assertEqual(0, len(self._postgres_manager.get_all_logs()))

    def test_anonymizing_documents(self):
        # Add test documents
        documents = read_data_from_json(os.path.join(TEST_DIR, 'data', 'clean_documents.json'))
        self._mongodb_h.add_clean_documents(documents)

        # Set up Anonymizer
        config = AnonymizerConfig(os.path.join(TEST_DIR, 'ci_anonymizer_settings.py'))

        mongo_manager = MongoDB_Manager(config, MockPreviousRunManager(0))
        mongo_manager._logger = MockLogger()

        # writer = MockWriter()
        writer = OpenDataWriter(config)

        anonymizer = Anonymizer(mongo_manager, writer, config)
        anonymized_records = anonymizer.anonymize()

        expected_logs = read_data_from_json(os.path.join(TEST_DIR, 'data', 'processed_documents.json'))

        self.assertEqual(5, anonymized_records)
        self.assertCountEqual(expected_logs, self._postgres_manager.get_all_logs())

    def test_scheduled_anonymization(self):
        # Add test documents
        documents = read_data_from_json(os.path.join(TEST_DIR, 'data', 'clean_documents.json'))
        self._mongodb_h.add_clean_documents(documents)

        # Set up Anonymizer
        config = AnonymizerConfig(os.path.join(TEST_DIR, 'ci_anonymizer_settings.py'))

        mongo_manager = MongoDB_Manager(config, MockPreviousRunManager(0))
        mongo_manager._logger = MockLogger()

        # writer = MockWriter()
        writer = OpenDataWriter(config)

        anonymizer = Anonymizer(mongo_manager, writer, config)
        anonymized_records = anonymizer.anonymize()

        expected_logs = read_data_from_json(os.path.join(TEST_DIR, 'data', 'processed_documents.json'))

        self.assertEqual(5, anonymized_records)
        self.assertCountEqual(expected_logs, self._postgres_manager.get_all_logs())

        # Add another batch of test documents

        documents = read_data_from_json(os.path.join(TEST_DIR, 'data', 'more_clean_documents.json'))
        for document in documents:
            document['correctorTime'] = datetime.now().timestamp()

        self._mongodb_h.add_clean_documents(documents)

        # Anonymize the new batch
        anonymized_records = anonymizer.anonymize()

        expected_logs = read_data_from_json(os.path.join(TEST_DIR, 'data', 'more_processed_documents.json'))

        self.assertEqual(1, anonymized_records)
        self.assertCountEqual(expected_logs, self._postgres_manager.get_all_logs())


class MockPreviousRunManager(object):

    def __init__(self, previous_run_timestamp):
        self._previous_run = previous_run_timestamp

    def get_previous_run(self):
        return self._previous_run

    def set_previous_run(self, run):
        self._previous_run = run


class MockLogger(object):

    def info(self, msg):
        return

    def error(self, msg):
        return

    def debug(self, msg):
        return


class MockWriter(object):

    def __init__(self):
        self._db_manager = MockDBManager()
        self._stored_documents_path = os.path.join(TEST_DIR, 'data', 'more_processed_documents.json')

    def write_records(self, processed_records):
        with open(self._stored_documents_path, 'w') as records_file:
            for record in processed_records:
                record['requestInDate'] = datetime.fromtimestamp(record['requestInTs'] / 1000).strftime('%Y-%m-%d')
                lower_case_record = {key.lower(): record[key] for key in record}
                records_file.write(json.dumps(lower_case_record))
                records_file.write('\n')


class MockDBManager(object):

    def get_new_ids(self, ids):
        return ids

    def add_index_entries(self, entries):
        pass
