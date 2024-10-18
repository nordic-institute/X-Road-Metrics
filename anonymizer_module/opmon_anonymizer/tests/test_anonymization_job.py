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

import os
import re

import unittest
from unittest.mock import MagicMock

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
                    'securityServerType': 'securityServerType_client_value'
                },
                'producer': {
                    'requestInTs': 'requestInTs_producer_value',
                    'securityServerType': 'securityServerType_producer_value'
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


class MockAnonymizationJob(object):
    pass
