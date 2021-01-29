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
