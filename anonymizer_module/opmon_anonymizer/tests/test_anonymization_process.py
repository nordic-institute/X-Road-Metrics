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
import json

import pytest
import pathlib
from unittest.mock import Mock

from opmon_anonymizer.anonymizer import Anonymizer
from opmon_anonymizer.settings_parser import OpmonSettingsManager

TEST_DIR = os.path.abspath(os.path.dirname(__file__))


@pytest.fixture
def basic_settings():
    os.chdir(pathlib.Path(__file__).parent.absolute())
    return OpmonSettingsManager().settings


def test_anonymizing_without_documents(basic_settings):
    MockAnonymizer.anonymize = Anonymizer.anonymize

    anonymizer = MockAnonymizer()
    anonymizer._settings = basic_settings

    anonymizer._reader = MockEmptyReader()
    anonymizer._allowed_fields = None

    assert anonymizer.anonymize() == 0
    assert anonymizer.anonymize(log_limit=1) == 0


def test_anonymizing_without_constraints(basic_settings):
    reader = MockStandardReader()
    writer = MockWriter()

    anonymizer = Anonymizer(reader, writer, basic_settings, logger_manager=Mock())

    dual_records_anonymized = anonymizer.anonymize()
    anonymized_documents = writer.get_written_records()

    assert 5 == dual_records_anonymized  # 5 dual records processed
    assert 10 == len(anonymized_documents)  # 2*5 individual logs extracted

    with open(os.path.join(TEST_DIR, 'data', 'expected_documents_without_constraints.json')) as expected_documents_file:
        expected_documents = [json.loads(line.strip()) for line in expected_documents_file]

    assert len(expected_documents) == len(anonymized_documents)


def test_anonymizing_with_time_precision_reduction(basic_settings):
    reader = MockStandardReader()
    writer = MockWriter()

    anonymizer = Anonymizer(reader, writer, basic_settings, logger_manager=Mock())

    dual_records_anonymized = anonymizer.anonymize()
    anonymized_documents = writer.get_written_records()

    assert 5 == dual_records_anonymized  # 5 dual records processed
    assert 10 == len(anonymized_documents)  # 2*5 individual logs extracted

    with open(os.path.join(TEST_DIR, 'data',
                           'expected_documents_with_reduced_time_precision.json')) as expected_documents_file:
        expected_documents = [json.loads(line.strip()) for line in expected_documents_file]

    assert len(expected_documents) == len(anonymized_documents)


def test_anonymizing_with_hiding_rules(basic_settings):
    reader = MockStandardReader()
    writer = MockWriter()

    basic_settings['anonymizer']['hiding-rules'] = [[{'feature': 'clientSubsystemCode', 'regex': '^.*-dev-app-kalkulaator$'}]]

    anonymizer = Anonymizer(reader, writer, basic_settings, logger_manager=Mock())

    dual_records_anonymized = anonymizer.anonymize()
    anonymized_documents = writer.get_written_records()

    assert 5 == dual_records_anonymized  # 5 dual records processed
    assert 4 == len(anonymized_documents)  # 2*2 individual logs extracted, 2*3 logs ignored

    with open(os.path.join(TEST_DIR, 'data',
                           'expected_documents_with_hiding_rules.json')) as expected_documents_file:
        expected_documents = [json.loads(line.strip()) for line in expected_documents_file]

    assert len(expected_documents) == len(anonymized_documents)


def test_anonymizing_with_substitution_rules(basic_settings):
    reader = MockStandardReader()
    writer = MockWriter()

    basic_settings['anonymizer']['substitution-rules'] = [
        {
            'conditions': [
                {'feature': 'securityServerType', 'regex': '^Client$'}
            ],
            'substitutes': [
                {'feature': 'representedPartyCode', 'value': '1'}
            ]
        }
    ]

    anonymizer = Anonymizer(reader, writer, basic_settings, logger_manager=Mock())

    dual_records_anonymized = anonymizer.anonymize()
    anonymized_documents = writer.get_written_records()

    assert 5 == dual_records_anonymized  # 5 dual records processed
    assert 10 == len(anonymized_documents)  # 2*2 individual logs extracted, 2*3 logs ignored

    with open(os.path.join(TEST_DIR, 'data',
                           'expected_documents_with_substitution_rules.json')) as expected_documents_file:
        expected_documents = [json.loads(line.strip()) for line in expected_documents_file]

    assert len(expected_documents) == len(anonymized_documents)


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
