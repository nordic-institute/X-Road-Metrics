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
from unittest.mock import Mock, MagicMock

import yaml

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
        """Should parse hiding rules into list of (feature, compiled_regex) tuples."""
        anonymizer_instance = Mock()
        anonymizer_instance._settings = yaml.safe_load("""
            anonymizer:
                hiding-rules:
                  -   # exclude all records where client id is "foo" and service id is "bar"
                    - feature: 'clientMemberCode'
                      regex: '^(foo)$'
                    - feature: 'serviceMemberCode'
                      regex: '^(bar)$'
                  -
                    - feature: 'clientMemberCode'
                      regex: '^(baz)$'
        """)
        anonymizer_instance._logger = Mock()

        hiding_rules = Anonymizer._get_hiding_rules(anonymizer_instance)

        # Should have 2 rules
        self.assertEqual(len(hiding_rules), 2)

        # First rule should have 2 conditions
        self.assertEqual(len(hiding_rules[0]), 2)
        self.assertEqual(hiding_rules[0][0][0], 'clientMemberCode')
        self.assertIsInstance(hiding_rules[0][0][1], type(re.compile('')))
        self.assertTrue(hiding_rules[0][0][1].match('foo'))
        self.assertFalse(hiding_rules[0][0][1].match('fooo'))

        # Second rule should have 1 condition
        self.assertEqual(len(hiding_rules[1]), 1)
        self.assertEqual(hiding_rules[1][0][0], 'clientMemberCode')
        self.assertTrue(hiding_rules[1][0][1].match('baz'))

    def test_substitution_rules_parsing(self):
        """Should parse substitution rules with conditions and substitutes."""
        anonymizer_instance = Mock()
        anonymizer_instance._settings = yaml.safe_load("""
            anonymizer:
                substitution-rules:
                  - conditions:
                      - feature: 'clientMemberCode'
                        regex: '^foo2$'
                    substitutes:
                      - feature: 'clientMemberCode'
                        value: 'N/A'
                      - feature: 'serviceMemberCode'
                        value: 'N/A'
                  - conditions:
                      - feature: 'clientMemberCode'
                        regex: '^bar2$'
                      - feature: 'messageType'
                        regex: '^query$'
                    substitutes:
                      - feature: 'messageId'
                        value: '0'
        """)
        anonymizer_instance._logger = Mock()

        substitution_rules = Anonymizer._get_substitution_rules(anonymizer_instance)

        # Should have 2 rules
        self.assertEqual(len(substitution_rules), 2)

        # First rule
        first_rule = substitution_rules[0]
        self.assertEqual(len(first_rule['conditions']), 1)
        self.assertEqual(first_rule['conditions'][0][0], 'clientMemberCode')
        self.assertIsInstance(first_rule['conditions'][0][1], type(re.compile('')))
        self.assertTrue(first_rule['conditions'][0][1].match('foo2'))

        self.assertEqual(len(first_rule['substitutes']), 2)
        self.assertEqual(first_rule['substitutes'][0]['feature'], 'clientMemberCode')
        self.assertEqual(first_rule['substitutes'][0]['value'], 'N/A')

        # Second rule conditions
        second_rule = substitution_rules[1]
        self.assertEqual(len(second_rule['conditions']), 2)
        self.assertEqual(second_rule['conditions'][0][0], 'clientMemberCode')
        self.assertEqual(second_rule['conditions'][1][0], 'messageType')
        self.assertTrue(second_rule['conditions'][1][1].match('query'))

    def test_transformers_parsing(self):
        """Should parse transformer settings and return enabled transformers."""
        anonymizer_instance = Mock()
        anonymizer_instance._settings = yaml.safe_load("""
            anonymizer:
                transformers:
                    reduce-request-in-ts-precision: true
                    force-durations-to-integer-range: false
        """)
        anonymizer_instance._logger = Mock()

        transformers = Anonymizer._get_transformers(anonymizer_instance)

        # Should have 1 transformer (only the enabled one)
        self.assertEqual(len(transformers), 1)
        self.assertTrue(callable(transformers[0]))

    def test_hiding_rules_parsing_with_invalid_regex(self):
        """Should raise exception when regex pattern is invalid."""
        anonymizer_instance = Mock()
        anonymizer_instance._settings = {
            'anonymizer': {
                'hiding-rules': [
                    [
                        {'feature': 'clientMemberCode', 'regex': '[invalid(regex'},
                    ],
                ]
            }
        }
        anonymizer_instance._logger = Mock()

        with self.assertRaises(Exception):
            Anonymizer._get_hiding_rules(anonymizer_instance)

    def test_substitution_rules_parsing_with_missing_conditions(self):
        """Should raise exception when substitution rule missing 'conditions' key."""
        anonymizer_instance = Mock()
        anonymizer_instance._settings = {
            'anonymizer': {
                'substitution-rules': [
                    {
                        # Missing 'conditions' key
                        'substitutes': [
                            {'feature': 'clientMemberCode', 'value': 'N/A'},
                        ]
                    },
                ]
            }
        }
        anonymizer_instance._logger = Mock()

        with self.assertRaises(Exception):
            Anonymizer._get_substitution_rules(anonymizer_instance)

    def test_hiding_rules_parsing_empty_list(self):
        """Should handle empty hiding rules list."""
        anonymizer_instance = Mock()
        anonymizer_instance._settings = {
            'anonymizer': {
                'hiding-rules': []
            }
        }
        anonymizer_instance._logger = Mock()

        hiding_rules = Anonymizer._get_hiding_rules(anonymizer_instance)

        self.assertEqual(hiding_rules, [])

    def test_substitution_rules_parsing_empty_list(self):
        """Should handle empty substitution rules list."""
        anonymizer_instance = Mock()
        anonymizer_instance._settings = {
            'anonymizer': {
                'substitution-rules': []
            }
        }
        anonymizer_instance._logger = Mock()

        substitution_rules = Anonymizer._get_substitution_rules(anonymizer_instance)

        self.assertEqual(substitution_rules, [])

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

    def test_field_translation_parsing_with_missing_file(self):
        """Should raise FileNotFoundError when translation file doesn't exist."""
        anonymizer_instance = Mock()

        with self.assertRaises(FileNotFoundError):
            Anonymizer._get_field_translations(
                anonymizer_instance, '/path/that/does/not/exist.list'
            )

    def test_allowed_fields_parsing_with_missing_file(self):
        """Should raise FileNotFoundError when field translations file doesn't exist."""
        logger = Mock()

        with self.assertRaises(FileNotFoundError):
            Anonymizer._get_allowed_fields('/path/that/does/not/exist.list', logger)


    def test_field_value_mask_parsing_with_missing_file(self):
        """Should raise FileNotFoundError when field data file doesn't exist."""
        anonymizer_instance = Mock()

        with self.assertRaises(FileNotFoundError):
            Anonymizer._get_field_value_masks(
                anonymizer_instance, '/path/that/does/not/exist.yaml'
            )

    def test_field_value_mask_parsing_with_invalid_yaml(self):
        """Should raise exception when YAML is invalid."""
        anonymizer_instance = Mock()

        with self.assertRaises(Exception):
            # Using field translations file which is not valid YAML
            Anonymizer._get_field_value_masks(
                anonymizer_instance, os.path.join(ROOT_DIR, 'data', 'test_field_translations.list')
            )

    def test_hiding_rules_parsing_with_missing_feature_key(self):
        """Should raise exception when hiding rule condition missing 'feature' key."""
        anonymizer_instance = Mock()
        anonymizer_instance._settings = yaml.safe_load("""
            anonymizer:
                hiding-rules:
                  -
                    - regex: '^(foo)$'  # Missing 'feature' key
        """)
        anonymizer_instance._logger = Mock()

        with self.assertRaises(Exception):
            Anonymizer._get_hiding_rules(anonymizer_instance)

    def test_substitution_rules_parsing_with_missing_feature_in_substitutes(self):
        """Should raise exception when substitution missing 'feature' in substitutes."""
        anonymizer_instance = Mock()
        anonymizer_instance._settings = yaml.safe_load("""
            anonymizer:
                substitution-rules:
                  - conditions:
                        regex: '^foo2$'
                    substitutes:
                      - value: 'N/A'  # Missing 'feature' key
        """)
        anonymizer_instance._logger = Mock()

        with self.assertRaises(Exception):
            Anonymizer._get_substitution_rules(anonymizer_instance)

    def test_transformers_parsing_with_missing_transformer_key(self):
        """Should raise KeyError when transformer settings missing expected key."""
        anonymizer_instance = Mock()
        anonymizer_instance._settings = yaml.safe_load("""
            anonymizer:
                transformers:
                    reduce-request-in-ts-precision: true
                    # Missing 'force-durations-to-integer-range' key
        """)
        anonymizer_instance._logger = Mock()

        with self.assertRaises(KeyError):
            Anonymizer._get_transformers(anonymizer_instance)


    def test_anonymizer_anonymize_normal_batch(self):
        """Test Anonymizer.anonymize processes and writes all records in normal operation."""
        from opmon_anonymizer.anonymizer import Anonymizer
        mock_reader = MagicMock()
        mock_writer = MagicMock()
        # 5 records, buffer size 2, so 2 batches + 1 final batch
        mock_reader.get_records.return_value = [
            {'client': {'foo': 'a'}, 'producer': {'bar': 'b'}},
            {'client': {'foo': 'c'}, 'producer': {'bar': 'd'}},
            {'client': {'foo': 'e'}, 'producer': {'bar': 'f'}},
            {'client': {'foo': 'g'}, 'producer': {'bar': 'h'}},
            {'client': {'foo': 'i'}, 'producer': {'bar': 'j'}},
        ]
        mock_reader.last_processed_timestamp = 0
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
        result = anonymizer.anonymize()
        # Should process all 5 records
        self.assertEqual(result, 5)
        # Should process 3 batches
        self.assertEqual(mock_writer.write_records.call_count, 3)
        logger.log_info.assert_called()

