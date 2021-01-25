import os
import json

import unittest
from unittest.mock import Mock

from ..anonymizer import Anonymizer
from ..anonymizer_config import AnonymizerConfig

TEST_DIR = os.path.abspath(os.path.dirname(__file__))


class TestAnonymizationProcess(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None

    def test_anonymizing_without_documents(self):
        MockAnonymizer.anonymize = Anonymizer.anonymize
        MockAnonymizer.anonymize_with_limit = Anonymizer.anonymize_with_limit

        anonymizer = MockAnonymizer()

        config = Mock()
        config.postgres = {'buffer_size': 10}
        config.anonymizer = {'threads': 1}

        anonymizer._config = config

        anonymizer._reader = MockEmptyReader()
        anonymizer._allowed_fields = None

        self.assertEqual(anonymizer.anonymize(), 0)
        self.assertEqual(anonymizer.anonymize_with_limit(1), 0)

    def test_anonymizing_without_constraints(self):
        reader = MockStandardReader()
        writer = MockWriter()

        config = AnonymizerConfig(os.path.join(TEST_DIR, 'anonymizer_settings.py'))

        anonymizer = Anonymizer(reader, writer, config)

        dual_records_anonymized = anonymizer.anonymize()
        anonymized_documents = writer.get_written_records()

        self.assertEqual(5, dual_records_anonymized)  # 5 dual records processed
        self.assertEqual(10, len(anonymized_documents))  # 2*5 individual logs extracted

        with open(os.path.join(TEST_DIR, 'data', 'expected_documents_without_constraints.json')) as expected_documents_file:
            expected_documents = [json.loads(line.strip()) for line in expected_documents_file]

        self.assertCountEqual(expected_documents, anonymized_documents)

    def test_anonymizing_with_time_precision_reduction(self):
        reader = MockStandardReader()
        writer = MockWriter()

        config = AnonymizerConfig(os.path.join(TEST_DIR, 'anonymizer_settings.py'))
        config.anonymizer['transformers'] = ['default.reduce_request_in_ts_precision']

        anonymizer = Anonymizer(reader, writer, config)

        dual_records_anonymized = anonymizer.anonymize()
        anonymized_documents = writer.get_written_records()

        self.assertEqual(5, dual_records_anonymized)  # 5 dual records processed
        self.assertEqual(10, len(anonymized_documents))  # 2*5 individual logs extracted

        with open(os.path.join(TEST_DIR, 'data',
                               'expected_documents_with_reduced_time_precision.json')) as expected_documents_file:
            expected_documents = [json.loads(line.strip()) for line in expected_documents_file]

        self.assertCountEqual(expected_documents, anonymized_documents)

    def test_anonymizing_with_hiding_rules(self):
        reader = MockStandardReader()
        writer = MockWriter()

        config = AnonymizerConfig(os.path.join(TEST_DIR, 'anonymizer_settings.py'))
        config.hiding_rules = [[{'feature': 'clientSubsystemCode', 'regex': '^.*-dev-app-kalkulaator$'}]]

        anonymizer = Anonymizer(reader, writer, config)

        dual_records_anonymized = anonymizer.anonymize()
        anonymized_documents = writer.get_written_records()

        self.assertEqual(5, dual_records_anonymized)  # 5 dual records processed
        self.assertEqual(4, len(anonymized_documents))  # 2*2 individual logs extracted, 2*3 logs ignored

        with open(os.path.join(TEST_DIR, 'data',
                               'expected_documents_with_hiding_rules.json')) as expected_documents_file:
            expected_documents = [json.loads(line.strip()) for line in expected_documents_file]

        self.assertCountEqual(expected_documents, anonymized_documents)

    def test_anonymizing_with_substitution_rules(self):
        reader = MockStandardReader()
        writer = MockWriter()

        config = AnonymizerConfig(os.path.join(TEST_DIR, 'anonymizer_settings.py'))
        config.substitution_rules = [
            {
                'conditions': [
                    {'feature': 'securityServerType', 'regex': '^Client$'}
                ],
                'substitutes': [
                    {'feature': 'representedPartyCode', 'value': '1'}
                ]
            }
        ]

        anonymizer = Anonymizer(reader, writer, config)

        dual_records_anonymized = anonymizer.anonymize()
        anonymized_documents = writer.get_written_records()

        self.assertEqual(5, dual_records_anonymized)  # 5 dual records processed
        self.assertEqual(10, len(anonymized_documents))  # 2*2 individual logs extracted, 2*3 logs ignored

        with open(os.path.join(TEST_DIR, 'data',
                               'expected_documents_with_substitution_rules.json')) as expected_documents_file:
            expected_documents = [json.loads(line.strip()) for line in expected_documents_file]

        self.assertCountEqual(expected_documents, anonymized_documents)


class MockAnonymizer(object):
    pass


class MockStandardReader(object):

    last_processed_timestamp = None

    def get_records(self, allowed_fields):
        with open(os.path.join(TEST_DIR, 'data', 'original_documents.json')) as records_file:
            records = records_file.readlines()

        for record in records:
            yield json.loads(record)


class MockEmptyReader(object):

    last_processed_timestamp = None

    @staticmethod
    def get_records(allowed_fields):
        yield from []


class MockWriter(object):

    def __init__(self):
        self._db_manager = MockDBManager()
        self._stored_documents_path = os.path.join(TEST_DIR, 'data', 'processed_documents.json')

    def write_records(self, processed_records):
        with open(self._stored_documents_path, 'w') as records_file:
            for record in processed_records:
                records_file.write(json.dumps(record))
                records_file.write('\n')

    def get_written_records(self):
        records = []

        with open(self._stored_documents_path) as records_file:
            records = [json.loads(line.strip()) for line in records_file]

        os.remove(self._stored_documents_path)

        return records


class MockDBManager(object):

    def get_new_ids(self, ids):
        return ids

    def add_index_entries(self, entries):
        pass
