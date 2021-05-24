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

import pytest
import pathlib
import os
from copy import deepcopy

from opmon_corrector.settings_parser import OpmonSettingsManager
from opmon_corrector.document_manager import DocumentManager


@pytest.fixture
def basic_settings():
    os.chdir(pathlib.Path(__file__).parent.absolute())
    return OpmonSettingsManager().settings


@pytest.fixture
def mock_logger_manager(mocker):
    mocker.patch('opmon_corrector.document_manager.LoggerManager', return_value=mocker.Mock())


@pytest.fixture
def matching_docs():
    doc1 = {
        'securityServerType': 'Client',
        'requestInTs': 100,
        'clientMemberClass': 'foo'
    }

    doc2 = {
        'producer': {
            'requestInTs': 105,
            'clientMemberClass': 'foo'
        },
        'client': {}
    }

    return doc1, doc2


test_doc = {
    'client': {
        'requestInTs': 89,
        'requestOutTs': 91,
        'responseInTs': 107,
        'responseOutTs': 110,
        'requestSoapSize': 1234,
        'requestAttachmentCount': 0,
        'responseSoapSize': 4321,
        'responseAttachmentCount': 0
    },
    'producer': {
        'requestInTs': 98,
        'requestOutTs': 100,
        'responseInTs': 103,
        'responseOutTs': 105,
        'requestSoapSize': 2345,
        'requestAttachmentCount': 0,
        'responseSoapSize': 5432,
        'responseAttachmentCount': 0
    }
}


def test_enable_all_client_calculations(mock_logger_manager, basic_settings):
    dm = DocumentManager(basic_settings)
    doc = dm._client_calculations(deepcopy(test_doc))

    assert (doc['producer'] == test_doc['producer'])
    assert (doc['client'] == test_doc['client'])

    assert (doc['totalDuration'] == 21)
    assert (doc['clientSsRequestDuration'] == 2)
    assert (doc['clientSsResponseDuration'] == 3)


def test_client_calculations_without_client(mock_logger_manager, basic_settings):
    dm = DocumentManager(basic_settings)
    doc = deepcopy(test_doc)
    doc.pop('client')

    doc = dm._client_calculations(doc)

    assert (doc['producer'] == test_doc['producer'])
    assert (doc.get('client') is None)

    assert (doc['totalDuration'] is None)
    assert (doc['clientSsRequestDuration'] is None)
    assert (doc['clientSsResponseDuration'] is None)


def test_disable_client_calculations(mock_logger_manager, basic_settings):
    dm = DocumentManager(basic_settings)

    doc = dm._client_calculations(deepcopy(test_doc))
    assert ('totalDuration' in doc.keys())
    assert ('clientSsRequestDuration' in doc.keys())
    assert ('clientSsResponseDuration' in doc.keys())

    basic_settings['corrector']['calc']['total-duration'] = False
    doc = dm._client_calculations(deepcopy(test_doc))
    assert ('totalDuration' not in doc.keys())
    assert ('clientSsRequestDuration' in doc.keys())
    assert ('clientSsResponseDuration' in doc.keys())

    basic_settings['corrector']['calc']['client-request-duration'] = False
    doc = dm._client_calculations(deepcopy(test_doc))
    assert ('totalDuration' not in doc.keys())
    assert ('clientSsRequestDuration' not in doc.keys())
    assert ('clientSsResponseDuration' in doc.keys())

    basic_settings['corrector']['calc']['client-response-duration'] = False
    doc = dm._client_calculations(deepcopy(test_doc))
    assert ('totalDuration' not in doc.keys())
    assert ('clientSsRequestDuration' not in doc.keys())
    assert ('clientSsResponseDuration' not in doc.keys())


def test_client_calculations_with_invalid_data(mock_logger_manager, basic_settings):
    invalid_doc = {
        'client': {
            'requestInTs': 'blah',
            'responseInTs': 99,
            'responseOutTs': None
        }
    }

    dm = DocumentManager(basic_settings)
    doc = dm._client_calculations(deepcopy(invalid_doc))

    assert (doc['totalDuration'] is None)
    assert (doc['clientSsRequestDuration'] is None)
    assert (doc['clientSsResponseDuration'] is None)


def test_enable_all_producer_calculations(mock_logger_manager, basic_settings):
    dm = DocumentManager(basic_settings)
    doc = dm._producer_calculations(deepcopy(test_doc))

    assert (doc['producer'] == test_doc['producer'])
    assert (doc['client'] == test_doc['client'])

    assert (doc['producerDurationProducerView'] == 7)
    assert (doc['producerSsRequestDuration'] == 2)
    assert (doc['producerSsResponseDuration'] == 2)
    assert (doc['producerIsDuration'] == 3)


def test_producer_calculations_without_producer(mock_logger_manager, basic_settings):
    dm = DocumentManager(basic_settings)
    doc = deepcopy(test_doc)
    doc.pop('producer')

    doc = dm._producer_calculations(doc)

    assert (doc['client'] == test_doc['client'])
    assert (doc.get('producer') is None)

    assert (doc['producerDurationProducerView'] is None)
    assert (doc['producerSsRequestDuration'] is None)
    assert (doc['producerSsResponseDuration'] is None)
    assert (doc['producerIsDuration'] is None)


def test_disable_producer_calculations(mock_logger_manager, basic_settings):
    dm = DocumentManager(basic_settings)

    doc = dm._producer_calculations(deepcopy(test_doc))
    assert ('producerDurationProducerView' in doc.keys())
    assert ('producerSsRequestDuration' in doc.keys())
    assert ('producerSsResponseDuration' in doc.keys())
    assert ('producerIsDuration' in doc.keys())

    basic_settings['corrector']['calc']['producer-duration-producer-view'] = False
    doc = dm._producer_calculations(deepcopy(test_doc))
    assert ('producerDurationProducerView' not in doc.keys())
    assert ('producerSsRequestDuration' in doc.keys())
    assert ('producerSsResponseDuration' in doc.keys())
    assert ('producerIsDuration' in doc.keys())

    basic_settings['corrector']['calc']['producer-request-duration'] = False
    doc = dm._producer_calculations(deepcopy(test_doc))
    assert ('producerDurationProducerView' not in doc.keys())
    assert ('producerSsRequestDuration' not in doc.keys())
    assert ('producerSsResponseDuration' in doc.keys())
    assert ('producerIsDuration' in doc.keys())

    basic_settings['corrector']['calc']['producer-response-duration'] = False
    doc = dm._producer_calculations(deepcopy(test_doc))
    assert ('producerDurationProducerView' not in doc.keys())
    assert ('producerSsRequestDuration' not in doc.keys())
    assert ('producerSsResponseDuration' not in doc.keys())
    assert ('producerIsDuration' in doc.keys())

    basic_settings['corrector']['calc']['producer-is-duration'] = False
    doc = dm._producer_calculations(deepcopy(test_doc))
    assert ('producerDurationProducerView' not in doc.keys())
    assert ('producerSsRequestDuration' not in doc.keys())
    assert ('producerSsResponseDuration' not in doc.keys())
    assert ('producerIsDuration' not in doc.keys())


def test_producer_calculations_with_invalid_data(mock_logger_manager, basic_settings):
    invalid_doc = {
        'producer': {
            'requestInTs': 'blah',
            'responseInTs': 99,
            'responseOutTs': None
        }
    }

    dm = DocumentManager(basic_settings)
    doc = dm._producer_calculations(invalid_doc)

    assert (doc['producerDurationProducerView'] is None)
    assert (doc['producerSsRequestDuration'] is None)
    assert (doc['producerSsResponseDuration'] is None)
    assert (doc['producerIsDuration'] is None)


def test_pair_calculations(mock_logger_manager, basic_settings):
    dm = DocumentManager(basic_settings)
    doc = dm._pair_calculations(deepcopy(test_doc))

    assert (doc['requestNwDuration'] == 7)
    assert (doc['responseNwDuration'] == 2)
    assert (doc['clientRequestSize'] == 1234)
    assert (doc['producerRequestSize'] == 2345)
    assert (doc['clientResponseSize'] == 4321)
    assert (doc['producerResponseSize'] == 5432)


def test_pair_calculations_without_client_and_producer(mock_logger_manager, basic_settings):
    dm = DocumentManager(basic_settings)
    doc = {
        'client': None,
        'producer': None
    }
    doc = dm._pair_calculations(doc)

    assert (doc['requestNwDuration'] is None)
    assert (doc['responseNwDuration'] is None)
    assert (doc['clientRequestSize'] is None)
    assert (doc['producerRequestSize'] is None)
    assert (doc['clientResponseSize'] is None)
    assert (doc['producerResponseSize'] is None)


def test_pair_calculations_with_attachments(mock_logger_manager, basic_settings):
    dm = DocumentManager(basic_settings)
    attachment_doc = deepcopy(test_doc)

    client_attachment = {
        'requestAttachmentCount': 100,
        'requestMimeSize': 7654321,
        'responseAttachmentCount': 2,
        'responseMimeSize': 654321
    }

    producer_attachment = {
        'requestAttachmentCount': 1,
        'requestMimeSize': 123456,
        'responseAttachmentCount': 3,
        'responseMimeSize': 1234567
    }

    attachment_doc['client'] = {**attachment_doc['client'], **client_attachment}
    attachment_doc['producer'] = {**attachment_doc['producer'], **producer_attachment}

    doc = dm._pair_calculations(attachment_doc)

    assert (doc['requestNwDuration'] == 7)
    assert (doc['responseNwDuration'] == 2)
    assert (doc['clientRequestSize'] == 7654321)
    assert (doc['producerRequestSize'] == 123456)
    assert (doc['clientResponseSize'] == 654321)
    assert (doc['producerResponseSize'] == 1234567)


def test_disable_pair_calculations(mock_logger_manager, basic_settings):
    doc_keys_per_setting = {
        'request-nw-duration': ['requestNwDuration'],
        'response-nw-duration': ['responseNwDuration'],
        'request-size': ['clientRequestSize', 'producerRequestSize'],
        'response-size': ['clientResponseSize', 'producerResponseSize']
    }

    all_doc_keys = sum(doc_keys_per_setting.values(), [])
    disabled_doc_keys = []

    calc = basic_settings['corrector']['calc']

    for setting in doc_keys_per_setting.keys():
        calc[setting] = False
        disabled_doc_keys += doc_keys_per_setting[setting]
        dm = DocumentManager(basic_settings)
        doc = dm._pair_calculations(deepcopy(test_doc))
        for doc_key in all_doc_keys:
            if doc_key in disabled_doc_keys:
                assert (doc_key not in doc.keys())
            else:
                assert (doc_key in doc.keys())


def test_pair_calculation_with_invalid_data(mock_logger_manager, basic_settings):
    invalid_doc = {
        'client': {
            'requestOutTs': None,
            'responseInTs': 'abc',
            'responseOutTs': 110,
            'requestSoapSize': 'def'
        },
        'producer': {
            'requestInTs': 'abc',
            'requestOutTs': None,
            'responseInTs': None,
            'responseOutTs': None,
            'requestAttachmentCount': None,
        }
    }

    dm = DocumentManager(basic_settings)
    doc = dm._pair_calculations(invalid_doc)

    assert (doc['requestNwDuration'] is None)
    assert (doc['responseNwDuration'] is None)
    assert (doc['clientRequestSize'] is None)
    assert (doc['producerRequestSize'] is None)
    assert (doc['clientResponseSize'] is None)
    assert (doc['producerResponseSize'] is None)


def test_get_boundary_value():
    low = -2 ** 31 + 1
    hi = 2 ** 31 - 1
    assert DocumentManager.get_boundary_value(low) == low
    assert DocumentManager.get_boundary_value(low - 1) == low
    assert DocumentManager.get_boundary_value(low + 1) == low + 1
    assert DocumentManager.get_boundary_value(low / 2) == low / 2
    assert DocumentManager.get_boundary_value(low * 2) == low
    assert DocumentManager.get_boundary_value(0) == 0
    assert DocumentManager.get_boundary_value(1) == 1
    assert DocumentManager.get_boundary_value(-1) == -1
    assert DocumentManager.get_boundary_value(hi) == hi
    assert DocumentManager.get_boundary_value(hi - 1) == hi - 1
    assert DocumentManager.get_boundary_value(hi + 1) == hi
    assert DocumentManager.get_boundary_value(hi / 2) == hi / 2
    assert DocumentManager.get_boundary_value(hi * 2) == hi
    assert DocumentManager.get_boundary_value(None) is None


def test_limit_calculation_values(mock_logger_manager, basic_settings, mocker):
    mocker.patch('opmon_corrector.document_manager.DocumentManager.get_boundary_value')

    doc = {
        'clientSsResponseDuration': 1,
        'producerSsResponseDuration': 2,
        'requestNwDuration': 3,
        'totalDuration': 4,
        'producerDurationProducerView': 5,
        'responseNwDuration': 6,
        'producerResponseSize': 7,
        'producerDurationClientView': 8,
        'clientResponseSize': 9,
        'producerSsRequestDuration': 10,
        'clientRequestSize': 11,
        'clientSsRequestDuration': 12,
        'producerRequestSize': 13,
        'producerIsDuration': 14,
        'foobar': 0,
    }

    dm = DocumentManager(basic_settings)
    dm._limit_calculation_values(deepcopy(doc))

    assert DocumentManager.get_boundary_value.call_count == 14
    assert mocker.call(doc['foobar']) not in DocumentManager.get_boundary_value.call_args_list
    doc.pop('foobar')

    for value in doc.values():
        DocumentManager.get_boundary_value.assert_any_call(value)


def test_match_documents(mock_logger_manager, basic_settings, matching_docs):
    doc1, doc2 = matching_docs
    dm = DocumentManager(basic_settings)
    assert dm.match_documents(doc1, doc2)


def test_mach_documents_attribute_comparison_list(mock_logger_manager, basic_settings, matching_docs):
    doc1, doc2 = matching_docs
    dm = DocumentManager(basic_settings)

    for attribute in basic_settings['corrector']['comparison-list']:
        doc1[attribute] = 'baz'
        assert not dm.match_documents(doc1, doc2)

        doc2[attribute] = 'baz'
        assert not dm.match_documents(doc1, doc2)


def test_mach_documents_attribute_orphan_comparison_list(mock_logger_manager, basic_settings, matching_docs):
    doc1, doc2 = matching_docs
    dm = DocumentManager(basic_settings)

    for attribute in basic_settings['corrector']['comparison_list_orphan']:
        doc1[attribute] = 'baz'
        assert not dm.match_documents(doc1, doc2, orphan=True)

        doc2[attribute] = 'baz'
        assert not dm.match_documents(doc1, doc2, orphan=True)


def test_mach_documents_time_window(mock_logger_manager, basic_settings, matching_docs):
    doc1, doc2 = matching_docs
    dm = DocumentManager(basic_settings)
    doc1['requestInTs'] += basic_settings['corrector']['time-window'] + 100

    assert not dm.match_documents(doc1, doc2)


def test_mach_documents_mandatory_fields(mock_logger_manager, basic_settings, matching_docs):
    doc1, doc2 = matching_docs
    dm = DocumentManager(basic_settings)

    doc1.pop('requestInTs')
    doc2['producer'].pop('requestInTs')
    assert not dm.match_documents(doc1, doc2)

    doc1['requestInTs'] = 100
    assert not dm.match_documents(doc1, doc2)

    doc2['producer']['requestInTs'] = 105
    assert dm.match_documents(doc1, doc2)

    doc2.pop('producer')
    assert not dm.match_documents(doc1, doc2)


def test_matching_documents_for_producer(mock_logger_manager, basic_settings, matching_docs):
    doc1, doc2 = matching_docs
    dm = DocumentManager(basic_settings)

    doc1['securityServerType'] = 'Producer'
    doc2['client'] = doc2['producer']

    assert dm.match_documents(doc1, doc2)


def test_matching_documents_missing_producer(mock_logger_manager, basic_settings, matching_docs):
    doc1, doc2 = matching_docs
    doc2.pop('producer')
    dm = DocumentManager(basic_settings)

    assert not dm.match_documents(doc1, doc2)


def test_matching_documents_missing_documents(mock_logger_manager, basic_settings, matching_docs):
    doc1, doc2 = matching_docs
    dm = DocumentManager(basic_settings)

    assert not dm.match_documents(doc1, None)
    assert not dm.match_documents(None, doc2)
    assert not dm.match_documents(None, None)


def test_matching_documents_invalid_security_server_type(mock_logger_manager, basic_settings, matching_docs):
    doc1, doc2 = matching_docs
    doc1['securityServerType'] = 'foobar'
    dm = DocumentManager(basic_settings)

    assert not dm.match_documents(doc1, doc2)


def test_find_match(mock_logger_manager, basic_settings, mocker):
    doc_a = 'doc'
    doc_list = ['1', '2', '3']

    mocker.patch('opmon_corrector.document_manager.DocumentManager.match_documents', return_value=False)

    dm = DocumentManager(basic_settings)
    dm.find_match(doc_a, doc_list)
    assert DocumentManager.match_documents.call_count == 3
    DocumentManager.match_documents.assert_any_call('doc', '1', False)
    DocumentManager.match_documents.assert_any_call('doc', '2', False)
    DocumentManager.match_documents.assert_any_call('doc', '3', False)

    dm.find_match(doc_a, doc_list, orphan=True)
    assert DocumentManager.match_documents.call_count == 6
    DocumentManager.match_documents.assert_any_call('doc', '1', True)
    DocumentManager.match_documents.assert_any_call('doc', '2', True)
    DocumentManager.match_documents.assert_any_call('doc', '3', True)


def test_create_json():
    json = DocumentManager.create_json('foo', 1, {'a': 123}, [3, 4, 5], 12.2)
    assert json == {
        'client': 'foo',
        'producer': 1,
        'clientHash': {'a': 123},
        'producerHash': [3, 4, 5],
        'messageId': 12.2
    }


def test_correct_structure(mock_logger_manager, basic_settings):
    dm = DocumentManager(basic_settings)
    doc = dm.correct_structure({})

    assert tuple(doc.keys()) == dm.must_fields
    assert all([v is None for v in doc.values()])


def test_calculate_hash():
    hashed = DocumentManager.calculate_hash({
        '_id': '123',
        'insertTime': 123,
        'corrected': False,
        'monitoringDataTs': 123456
    })

    assert hashed == '123456_ef36bf5fa911a8e6360f6be2a5f1ceb9'
