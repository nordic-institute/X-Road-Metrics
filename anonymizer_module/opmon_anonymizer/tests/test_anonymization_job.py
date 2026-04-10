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

import os
import re

import unittest
from unittest.mock import MagicMock

import yaml

from opmon_anonymizer.anonymizer import AnonymizationJob

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))



class TestAnonymizationJob(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None

    def test_record_hiding_with_rules(self):
        hiding_rules = [
            [('feature1', re.compile('value.')), ('feature2', re.compile(r'value\d+'))],
        ]

        records = [
            {'feature1': 'value1', 'feature2': 'value2', 'feature3': 'value3'},
            {'feature1': 'valueA', 'feature2': 'value51', 'feature3': 'value3'},
            {'feature1': 'value1', 'feature2': 'value_two', 'feature3': 'value3'},
        ]

        MockAnonymizationJob._should_be_hidden = AnonymizationJob._should_be_hidden
        anonymization_job = MockAnonymizationJob()
        anonymization_job._record_matches_conditions = AnonymizationJob._record_matches_conditions
        anonymization_job._hiding_rules = hiding_rules

        logger = MagicMock()

        passed_records = []
        for record in records:
            if not anonymization_job._should_be_hidden(record, logger):
                passed_records.append(record)

        expected_passed_records = [records[2]]

        self.assertCountEqual(expected_passed_records, passed_records)

    def test_record_substitution(self):
        substitution_rules = [
            {
                'conditions': [
                    ('feature1', re.compile('value.')),
                    ('feature2', re.compile(r'value\d+')),
                ],
                'substitutes': [
                    {'feature': 'feature1', 'value': 'new_value1'},
                    {'feature': 'feature3', 'value': 'new_value3'},
                ],
            }
        ]

        records = [
            {'feature1': 'value1', 'feature2': 'value2', 'feature3': 'old_value'},
            {'feature1': 'valueB', 'feature2': 'value_two', 'feature3': 'old_value'},
        ]

        expected_processed_records = [
            {'feature1': 'new_value1', 'feature2': 'value2', 'feature3': 'new_value3'},
            {'feature1': 'valueB', 'feature2': 'value_two', 'feature3': 'old_value'},
        ]

        MockAnonymizationJob._substitute = AnonymizationJob._substitute
        anonymization_job = MockAnonymizationJob()
        anonymization_job._record_matches_conditions = AnonymizationJob._record_matches_conditions
        anonymization_job._substitution_rules = substitution_rules

        logger = MagicMock()

        processed_records = [anonymization_job._substitute(record, logger) for record in records]

        self.assertCountEqual(expected_processed_records, processed_records)

    def test_dual_record_splitting(self):
        field_translations = {
            'client': {
                'requestInTs': 'requestInTs',
                'securityServerType': 'securityServerType',
            },
            'producer': {
                'requestInTs': 'requestInTs',
                'securityServerType': 'securityServerType',
            },
            'totalDuration': 'totalDuration',
            'producerDurationProducerView': 'producerDurationProducerView'
        }

        field_value_masks = {'client': set(['producerDurationProducerView']), 'producer': set(['totalDuration'])}

        dual_records = [
            {
                'client': {
                    'requestInTs': 'requestInTs_client_value',
                    'securityServerType': 'securityServerType_client_value',
                    'srcServer': 'DEV/ORG/NIIS/ss1/test-server',
                },
                'producer': {
                    'requestInTs': 'requestInTs_producer_value',
                    'securityServerType': 'securityServerType_producer_value',
                    'srcServer': 'DEV/ORG/NIIS/ss1/test-server',
                },
                'totalDuration': 'totalDuration_value'
            }
        ]

        expected_individual_records = [
            {
                'requestInTs': 'requestInTs_client_value',
                'securityServerType': 'securityServerType_client_value',
                'totalDuration': 'totalDuration_value',
                'producerDurationProducerView': None    # Masked for client
            },
            {
                'requestInTs': 'requestInTs_producer_value',
                'securityServerType': 'securityServerType_producer_value',
                'totalDuration': None   # Masked for producer
            }
        ]

        MockAnonymizationJob._get_agent_record = AnonymizationJob._get_agent_record
        MockAnonymizationJob._get_records = AnonymizationJob._get_records
        anonymization_job = MockAnonymizationJob()
        anonymization_job._field_value_masks = field_value_masks
        anonymization_job._field_translations = field_translations

        logger = MagicMock()

        individual_records = []
        for dual_record in dual_records:
            for individual_record in anonymization_job._get_records(dual_record, logger):
                individual_records.append(individual_record)

        self.assertCountEqual(expected_individual_records, individual_records)

    def test_anonymize_rolls_back_timestamp_on_batch_failure(self):
        """When batch processing fails, reader timestamp should be rolled back."""
        from opmon_anonymizer.anonymizer import Anonymizer

        mock_reader = MagicMock()
        mock_reader.last_processed_timestamp = 100
        mock_reader.get_records.return_value = [
            {'client': {'data': 'test1'}, 'producer': {}},
            {'client': {'data': 'test2'}, 'producer': {}},
        ]

        mock_writer = MagicMock()

        settings = yaml.safe_load("""
        anonymizer:
          hiding-rules: []
          substitution-rules: []
          transformers:
            reduce-request-in-ts-precision: false
            force-durations-to-integer-range: false
          field-translations-file: "./opmon_anonymizer/tests/data/test_field_translations.list"
          field-data-file: "./opmon_anonymizer/tests/data/test_field_data.yaml"

        postgres:
          buffer-size: 1
        """)

        logger = MagicMock()

        mock_writer.write_records.side_effect = Exception("Writer failed")

        anonymizer = Anonymizer(mock_reader, mock_writer, settings, logger)

        # Set initial timestamp
        mock_reader.last_processed_timestamp = 100

        # Run anonymize - should fail and rollback
        result = anonymizer.anonymize()

        mock_reader.update_last_processed_timestamp.assert_called_with(100)

        self.assertEqual(result, 0)

    def test_anonymize_handles_log_limit(self):
        """Should stop processing when log_limit is reached. This is currently only as precise as the postgres_buffer-size is."""
        from opmon_anonymizer.anonymizer import Anonymizer

        mock_reader = MagicMock()
        mock_reader.last_processed_timestamp = 100
        mock_reader.get_records.return_value = [
            {'client': {}, 'producer': {}} for _ in range(20)
        ]

        mock_writer = MagicMock()
        settings = yaml.safe_load("""
        anonymizer:
          hiding-rules: []
          substitution-rules: []
          transformers:
            reduce-request-in-ts-precision: false
            force-durations-to-integer-range: false
          field-translations-file: "./opmon_anonymizer/tests/data/test_field_translations.list"
          field-data-file: "./opmon_anonymizer/tests/data/test_field_data.yaml"

        postgres:
          buffer-size: 2
        """)

        logger = MagicMock()

        anonymizer = Anonymizer(mock_reader, mock_writer, settings, logger)
        mock_reader.last_processed_timestamp = 100

        result = anonymizer.anonymize(log_limit=5)

        self.assertEqual(result, 6)

    def test_anonymizationjob_run_normal_flow(self):
        """Test AnonymizationJob.run processes and writes records as expected, including hiding, substitution, and transformers."""
        mock_writer = MagicMock()
        mock_logger = MagicMock()
        # Transformer that adds a field
        def transformer(record):
            record['transformed'] = True
            return record
        # Hiding rule: hide if foo == 'hide'
        hiding_rules = [[('foo', re.compile('hide'))]]
        # Substitution rule: if bar == 'sub', set baz = 'substituted'
        substitution_rules = [{
            'conditions': [('bar', re.compile('sub'))],
            'substitutes': [{'feature': 'baz', 'value': 'substituted'}]
        }]
        transformers = [transformer]
        field_translations = {'client': {'foo': 'foo'}, 'producer': {'bar': 'bar'}, 'baz': 'baz'}
        field_value_masks = {'client': set(), 'producer': set()}
        job = AnonymizationJob(
            writer=mock_writer,
            hiding_rules=hiding_rules,
            substitution_rules=substitution_rules,
            transformers=transformers,
            field_translations=field_translations,
            field_value_masks=field_value_masks,
            logger_manager=mock_logger
        )
        dual_records = [
            {'client': {'foo': 'abc'}, 'producer': {'bar': 'sub'}, 'baz': 'bazval', 'qux': 'quxval'},  # triggers substitution
            {'client': {'foo': 'hide'}, 'producer': {'bar': 'xyz'}, 'baz': 'bazval', 'qux': 'quxval'}, # triggers hiding
        ]
        job.run(dual_records)

        args, _ = mock_writer.write_records.call_args
        written = args[0]
        # Check the hidden record (client with foo=='hide') should not be present
        self.assertEqual(len(written), 3)
        # Check transforming
        for rec in written:
            self.assertTrue(rec['transformed'])
        # Check field translations
        for rec in written:
            self.assertNotIn('qux', rec)
        for rec in written:
            self.assertIn('baz', rec)
        # Check substitution
        baz_values = [rec.get('baz') for rec in written]
        self.assertIn('substituted', baz_values)

        mock_logger.log_info.assert_called()

    def test_anonymizationjob_run_exception_logging(self):
        """Test AnonymizationJob.run logs and raises on exception in transformer."""
        mock_writer = MagicMock()
        mock_logger = MagicMock()
        def bad_transformer(record):
            raise ValueError('fail')
        hiding_rules = []
        substitution_rules = []
        transformers = [bad_transformer]
        field_translations = {'client': {}, 'producer': {}}
        field_value_masks = {'client': set(), 'producer': set()}
        job = AnonymizationJob(
            writer=mock_writer,
            hiding_rules=hiding_rules,
            substitution_rules=substitution_rules,
            transformers=transformers,
            field_translations=field_translations,
            field_value_masks=field_value_masks,
            logger_manager=mock_logger
        )
        dual_records = [
            {'client': {'foo': 'abc'}, 'producer': {'bar': 'xyz'}, 'baz': 'bazval'}
        ]
        with self.assertRaises(ValueError):
            job.run(dual_records)
        mock_logger.log_exception.assert_called()


class MockAnonymizationJob(object):
    pass
