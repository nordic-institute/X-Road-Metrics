import json
import logging
import os
import pathlib
from logging import StreamHandler

import bson
import mongomock
import pymongo
import pytest
from freezegun import freeze_time

from opmon_corrector.corrector_batch import CorrectorBatch
from opmon_corrector.corrector_worker import CorrectorWorker
from opmon_corrector.logger_manager import LoggerManager
from opmon_corrector.settings_parser import OpmonSettingsManager

TEST_DIR = os.path.abspath(os.path.dirname(__file__))


class SingleProcessedCorrectorBatch(CorrectorBatch):
    def _process_workers(self, list_to_process, duplicates):
        worker = CorrectorWorker(self.settings, 'worker 1')
        worker.run(list_to_process, duplicates)


def read_data_from_json(path):
    with open(path) as json_file:
        data = json.loads(json_file.read())
    return data


def normalize_data(obj):
    if isinstance(obj, dict):
        if '_id' in obj:
            obj.pop('_id')
        if 'correctorTime' in obj:
            obj.pop('correctorTime')

        # normalize timestamps
        for key, value in obj.items():
            if isinstance(value, bson.int64.Int64):
                obj[key] = int(value)
            else:
                normalize_data(value)
    elif isinstance(obj, list):
        for item in obj:
            normalize_data(item)


def read_fixture(file_name):
    data = read_data_from_json(
        os.path.join(TEST_DIR, 'fixtures', f"{file_name}.json")
    )
    return data


def insert_fixture(mongo, name, data):
    collection = mongo[name]
    collection.insert_many(data)
    return data


def get_documents(mongo, name, query={}):
    collection = mongo[name]
    cursor = collection.find(query)
    data = [doc for doc in cursor]
    return data


def compare_documents(actual, expected, sort='xRequestId'):
    for data in [actual, expected]:
        normalize_data(data)

    actual = sorted(actual, key=lambda x: (x[sort], x.get('totalDuration', '') or 1))
    expected = sorted(expected, key=lambda x: (x[sort], x.get('totalDuration', '') or 1))
    assert actual == expected


@pytest.fixture
def set_dir():
    os.chdir(pathlib.Path(__file__).parent.absolute())


@pytest.fixture(autouse=True)
def mock_logger_manager(mocker):
    mocker.patch('opmon_corrector.logger_manager.LoggerManager._create_file_handler', return_value=StreamHandler())
    mocker.patch('opmon_corrector.logger_manager.LoggerManager.log_heartbeat')
    yield mocker.Mock()


@pytest.fixture
def batch(set_dir, mocker):
    settings = OpmonSettingsManager('UNITTEST').settings
    logger_m = LoggerManager(
        settings['logger'], settings['xroad']['instance'], ''
    )
    batch = SingleProcessedCorrectorBatch(settings, logger_m)
    yield batch


@pytest.fixture
def mongo():
    with mongomock.patch(servers=(('mongodb', 27017),)):
        yield pymongo.MongoClient('mongodb').query_db_UNITTEST


@freeze_time("2022-12-10")
def test_corrector_batch_1(mongo, batch):
    raw_messages = insert_fixture(mongo, 'raw_messages', read_fixture('raw_messages_batch_1'))
    batch.run({})

    expected_clean_data = read_fixture('clean_data_batch_1')
    actual_clean_data = get_documents(mongo, 'clean_data')
    compare_documents(actual_clean_data, expected_clean_data)
    corrected_raw_documents = get_documents(mongo, 'raw_messages', {'corrected': True})
    assert len(corrected_raw_documents) == len(raw_messages)


@freeze_time("2022-12-10")
def test_corrector_batch_2(mongo, batch):
    # first batch
    insert_fixture(mongo, 'raw_messages', read_fixture('raw_messages_batch_1'))

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
def test_corrector_batch_duplicates(mongo, batch, caplog):
    caplog.set_level(logging.INFO)

    raw_messages = insert_fixture(mongo, 'raw_messages', read_fixture('raw_messages_batch_1'))
    # 4 duplicate documents
    duplicates = insert_fixture(mongo, 'raw_messages', read_fixture('raw_messages_duplicates'))

    batch.run({})
    # duplicates must be removed from raw_messages
    assert len(get_documents(mongo, 'raw_messages', {'corrected': True})) == len(raw_messages)
    assert f"Number of duplicates: {len(duplicates)}" in caplog.text
    assert f"Total of {len(duplicates)} duplicate documents removed from raw messages"


@freeze_time("2022-12-24")
def test_corrector_batch_timeout_documents(mongo, batch, caplog):
    insert_fixture(mongo, 'raw_messages', read_fixture('raw_messages_batch_1'))

    caplog.set_level(logging.INFO)
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
    batch = SingleProcessedCorrectorBatch(settings, logger_m)
    # will mark timeouted documents as done
    batch.run({})

    timeouted_documents = get_documents(mongo, 'clean_data', {"correctorStatus": "processing"})
    assert len(timeouted_documents) == 0

    assert f"Total of {len(timeouted_client_documents)} orphans from Client updated to status \'done\'." in caplog.text
    assert f"Total of {len(timeouted_producer_documents)} orphans from Producer updated to status \'done\'." in caplog.text
