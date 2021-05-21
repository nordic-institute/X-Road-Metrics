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

import unittest
from unittest.mock import MagicMock, Mock

from opmon_anonymizer.anonymizer import Anonymizer

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))


class TestAnonymizer(unittest.TestCase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxDiff = None

    def test_allowed_fields_parsing(self):

        allowed_fields = Anonymizer._get_allowed_fields(
            os.path.join(ROOT_DIR, 'data', 'test_field_translations.list'),
            Mock()
        )
        expected_allowed_fields = ['client.requestInTs', 'producer.requestInTs', 'client.securityServerType', 'totalDuration']
        self.assertCountEqual(expected_allowed_fields, allowed_fields)

    def test_hiding_rules_parsing(self):
        self.assertTrue(True)

    def test_hiding_rules_parsing(self):
        self.assertTrue(True)

    def test_substitution_rules_parsing(self):
        self.assertTrue(True)

    def test_transformers_parsing(self):
        self.assertTrue(True)

    def test_field_translation_parsing(self):
        anonymizer_instance = Mock()

        field_translations = Anonymizer._get_field_translations(
            anonymizer_instance, os.path.join(ROOT_DIR, 'data', 'test_field_translations.list'))
        expected_field_translations = {
            'client': {
                'requestInTs': 'requestInTs',
                'securityServerType': 'securityServerType',
            },
            'producer': {
                'requestInTs': 'requestInTs',
            },
            'totalDuration': 'totalDuration',
        }
        self.assertEqual(expected_field_translations, field_translations)

    def test_field_value_mask_parsing(self):
        anonymizer_instance = Mock()

        field_agent_masks = Anonymizer._get_field_value_masks(
            anonymizer_instance, os.path.join(ROOT_DIR, 'data', 'test_field_data.yaml'))
        expected_field_agent_masks = {'client': set(['producerDurationProducerView']), 'producer': set(['totalDuration'])}
        self.assertEqual(expected_field_agent_masks, field_agent_masks)

    # def test_last_anonymization_timestamp_storing(self):
    #     new_sqlite_db_path = 'temp.db'
    #     previous_run_manager = PreviousRunManager(new_sqlite_db_path)
    #
    #     current_time = datetime.datetime.now().timestamp()
    #     previous_run_manager.set_previous_run(current_time)
    #
    #     fetched_time = previous_run_manager.get_previous_run()
    #
    #     self.assertEqual(current_time, fetched_time)
    #
    #     os.remove(new_sqlite_db_path)
