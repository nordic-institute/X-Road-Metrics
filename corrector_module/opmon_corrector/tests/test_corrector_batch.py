import os
import operator
import multiprocessing
import json
import pytest
import bson
import pathlib
import logging
from freezegun import freeze_time

from opmon_corrector.corrector_batch import CorrectorBatch
from opmon_corrector.logger_manager import LoggerManager
from opmon_corrector.settings_parser import OpmonSettingsManager
from opmon_corrector.corrector_worker import CorrectorWorker

import pymongo
import mongomock

multiprocessing.freeze_support()

TEST_DIR = os.path.abspath(os.path.dirname(__file__))


def read_data_from_json(path):
    with open(path) as json_file:
        data = json.loads(json_file.read())
    return data


@pytest.fixture
def set_dir():
    os.chdir(pathlib.Path(__file__).parent.absolute())


@pytest.fixture
def mongo():
    with mongomock.patch(servers=(('mongo', 27017),)):
        yield pymongo.MongoClient('mongo').query_db_UNITTEST


@pytest.fixture
def raw_messages(request, mongo):
    marker = request.node.get_closest_marker("raw_messages_fixture")
    if marker is None:
        data = 'raw_messages_batch_1'
    else:
        data = marker.args[0]
    data = read_data_from_json(
        os.path.join(TEST_DIR, 'fixtures', f"{data}.json")
    )
    raw_messages = mongo['raw_messages']
    raw_messages.insert_many(data)
    yield data


@pytest.fixture
def duplicate_raw_messages(mongo):
    data = 'raw_messages_batch_1'
    data = read_data_from_json(
        os.path.join(TEST_DIR, 'fixtures', f"{data}.json")
    )
    raw_messages = mongo['raw_messages']
    raw_messages.insert_many(data)
    yield data


@pytest.fixture
def expected_clean_data(mongo):
    data = read_data_from_json(
        os.path.join(TEST_DIR, 'fixtures', 'clean_data_batch_1.json')
    )
    data = normalize_corrector_time(data)
    yield data


def remove_id(obj):
    if isinstance(obj, dict):
        if '_id' in obj:
            obj.pop('_id')
        for key, value in obj.items():
            remove_id(value)
    elif isinstance(obj, list):
        for item in obj:
            remove_id(item)


def normalize_timestamps(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, bson.int64.Int64):
                obj[key] = int(value)
            else:
                normalize_timestamps(value)
    elif isinstance(obj, list):
        for item in obj:
            normalize_timestamps(item)


def normalize_corrector_time(obj):
    return [{k: v for k, v in d.items() if k != 'correctorTime'} for d in obj]


@pytest.fixture
def mock_logger_manager(mocker):
    mocker.patch(
        'opmon_corrector.database_manager.LoggerManager',
        return_value=mocker.Mock()
    )
    mocker.patch(
        'opmon_corrector.document_manager.LoggerManager',
        return_value=mocker.Mock()
    )
    yield mocker.Mock()


@pytest.fixture
def batch(set_dir, mocker):
    settings = OpmonSettingsManager('UNITTEST').settings
    logger_m = LoggerManager(
        settings['logger'], settings['xroad']['instance'], ''
    )
    batch = CorrectorBatch(settings, logger_m)
    yield batch


def read_fixture(file_name):
    data = read_data_from_json(
        os.path.join(TEST_DIR, 'fixtures', f"{file_name}.json")
    )
    data = normalize_corrector_time(data)
    return data


def insert_fixture(mongo, name, data):
    collection = mongo[name]
    collection.insert_many(data)
    return data


def get_documents(mongo, name, query={}):
    collection = mongo[name]
    cursor = collection.find(query)
    data = [doc for doc in cursor]
    remove_id(data)
    normalize_timestamps(data)
    data = normalize_corrector_time(data)
    return data


def compare_documents(actual, expected, sort='xRequestId'):
    actual = sorted(actual, key=lambda x: (x[sort], x.get('totalDuration', '') or 1))
    expected = sorted(expected, key=lambda x: (x[sort], x.get('totalDuration', '') or 1))
    assert actual == expected


@freeze_time("2022-12-10")
@mongomock.patch(servers=(('mongodb', 27017),))
def test_corrector_batch_1(set_dir):
    mongo = pymongo.MongoClient('mongodb').query_db_UNITTEST
    raw_messages = insert_fixture(mongo, 'raw_messages', read_fixture('raw_messages_batch_1'))

    settings = OpmonSettingsManager('UNITTEST').settings
    logger_m = LoggerManager(
        settings['logger'], settings['xroad']['instance'], ''
    )
    batch = CorrectorBatch(settings, logger_m)
    batch.run({})

    expected_clean_data = read_fixture('clean_data_batch_1')
    actual_clean_data = get_documents(mongo, 'clean_data')
    compare_documents(actual_clean_data, expected_clean_data)
    corrected_raw_documents = get_documents(mongo, 'raw_messages', {'corrected': True})
    assert len(corrected_raw_documents) == len(raw_messages)


@freeze_time("2022-12-10")
@mongomock.patch(servers=(('mongodb', 27017),))
def test_corrector_batch_2(set_dir):
    mongo = pymongo.MongoClient('mongodb').query_db_UNITTEST
    # first batch
    insert_fixture(mongo, 'raw_messages', read_fixture('raw_messages_batch_1'))

    settings = OpmonSettingsManager('UNITTEST').settings
    logger_m = LoggerManager(
        settings['logger'], settings['xroad']['instance'], ''
    )
    batch = CorrectorBatch(settings, logger_m)
    batch.run({})
    assert get_documents(mongo, 'raw_messages', {'corrected': True})
    # We have several clean documents waiting its match
    assert len(get_documents(mongo, 'clean_data', {"correctorStatus": "processing"})) == 5
    # second batch with 2 missing documents
    insert_fixture(mongo, 'raw_messages', read_fixture('raw_messages_batch_2'))
    batch.run({})
    assert get_documents(mongo, 'raw_messages', {'corrected': True})
    # Missing provider or client must be found
    assert len(get_documents(mongo, 'clean_data', {"correctorStatus": "processing"})) == 3

    expected_clean_data = read_fixture('clean_data_after_batch_2')
    actual_clean_data = get_documents(mongo, 'clean_data')
    compare_documents(actual_clean_data, expected_clean_data)


@freeze_time("2022-12-10")
@mongomock.patch(servers=(('mongodb', 27017),))
def test_corrector_batch_duplicates(set_dir, caplog):
    caplog.set_level(logging.INFO)

    mongo = pymongo.MongoClient('mongodb').query_db_UNITTEST
    raw_messages = insert_fixture(mongo, 'raw_messages', read_fixture('raw_messages_batch_1'))
    # 4 duplicate documents
    duplicates = insert_fixture(mongo, 'raw_messages', read_fixture('raw_messages_duplicates'))

    settings = OpmonSettingsManager('UNITTEST').settings
    logger_m = LoggerManager(
        settings['logger'], settings['xroad']['instance'], ''
    )
    batch = CorrectorBatch(settings, logger_m)
    batch.run({})
    # duplicates must be removed from raw_messages
    assert len(get_documents(mongo, 'raw_messages', {'corrected': True})) == len(raw_messages)
    assert f"Number of duplicates: {len(duplicates)}" in caplog.text
    assert f"Total of {len(duplicates)} duplicate documents removed from raw messages"


@freeze_time("2022-12-24")
@mongomock.patch(servers=(('mongodb', 27017),))
def test_corrector_batch_timeout_documents(set_dir, caplog):
    mongo = pymongo.MongoClient('mongodb').query_db_UNITTEST
    insert_fixture(mongo, 'raw_messages', read_fixture('raw_messages_batch_1'))

    caplog.set_level(logging.INFO)

    settings = OpmonSettingsManager('UNITTEST').settings
    logger_m = LoggerManager(
        settings['logger'], settings['xroad']['instance'], ''
    )
    batch = CorrectorBatch(settings, logger_m)
    batch.run({})

    client_query = {
        "client": {"$ne": None},
        "correctorStatus": "processing"
    }
    producer_query = {
        "producer": {"$ne": None},
        "correctorStatus": "processing"
    }
    timeouted_client_documents = get_documents(mongo, 'clean_data', client_query)
    assert len(timeouted_client_documents) == 3

    timeouted_producer_documents = get_documents(mongo, 'clean_data', producer_query)
    assert len(timeouted_producer_documents) == 2

    settings = OpmonSettingsManager('UNITTEST').settings
    settings['corrector']['timeout-days'] = 1
    logger_m = LoggerManager(
        settings['logger'], settings['xroad']['instance'], ''
    )
    batch = CorrectorBatch(settings, logger_m)
    # will mark timeouted documents as done
    batch.run({})

    timeouted_documents = get_documents(mongo, 'clean_data', {"correctorStatus": "processing"})
    assert len(timeouted_documents) == 0

    assert f"Total of {len(timeouted_client_documents)} orphans from Client updated to status \'done\'." in caplog.text
    assert f"Total of {len(timeouted_producer_documents)} orphans from Producer updated to status \'done\'." in caplog.text
