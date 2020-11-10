#!/usr/bin/env python3

"""
Unit tests for database_manager.py
"""
import pytest
import os
import pathlib
import time
import mongomock
import pymongo

from opmon_collector.database_manager import DatabaseManager
from opmon_collector.settings import OpmonSettingsManager


@pytest.fixture
def basic_settings():
    os.chdir(pathlib.Path(__file__).parent.absolute())
    return OpmonSettingsManager().settings


@pytest.fixture()
def mock_db_client(mocker):
    client = {
        'collector_state_DEFAULT': {'server_list': mocker.Mock()},
        'query_db_DEFAULT': {'raw_messages': mocker.Mock()}
    }

    mocker.patch('opmon_collector.database_manager.pymongo.MongoClient', return_value=client)
    return client


def test_db_manager_init(basic_settings):
    mongo_settings = basic_settings['mongodb']
    xroad_instance = basic_settings['xroad']['instance']

    d = DatabaseManager(mongo_settings, xroad_instance, 'testlogmanager')
    assert d.mongo_uri == \
           f"mongodb://{mongo_settings['user']}:{mongo_settings['password']}@{mongo_settings['host']}/auth_db"

    assert d.db_name == 'query_db_DEFAULT'
    assert d.db_collector_state == 'collector_state_DEFAULT'
    assert d.collector_id == 'collector_DEFAULT'
    assert d.logger_m == 'testlogmanager'


@mongomock.patch(servers=(('defaultmongodb', 27017),))
def test_save_server_list_to_database(basic_settings, mocker):
    mongo_settings = basic_settings['mongodb']
    xroad_instance = basic_settings['xroad']['instance']

    d = DatabaseManager(mongo_settings, xroad_instance, mocker.Mock())
    d.save_server_list_to_database([1, 2, 3])

    server_list, timestamp = d.get_server_list_from_database()
    assert timestamp == pytest.approx(float(time.time()), abs=1)
    assert server_list == [1, 2, 3]


@mongomock.patch(servers=(('defaultmongodb', 27017),))
def test_insert_data_to_raw_messages(basic_settings, mocker):
    mongo_settings = basic_settings['mongodb']
    xroad_instance = basic_settings['xroad']['instance']

    d = DatabaseManager(mongo_settings, xroad_instance, mocker.Mock())
    test_data = [{'test': 1}, {'data': 2}]
    d.insert_data_to_raw_messages(test_data)

    client = pymongo.MongoClient(d.mongo_uri)
    items = list(client['query_db_DEFAULT']['raw_messages'].find())
    for item in items:
        assert item['insertTime'] == pytest.approx(float(time.time()), abs=1)

    assert test_data == items
    assert test_data is not items


@mongomock.patch(servers=(('defaultmongodb', 27017),))
def test_set_next_records_timestamp(basic_settings, mocker):
    mongo_settings = basic_settings['mongodb']
    xroad_instance = basic_settings['xroad']['instance']

    d = DatabaseManager(mongo_settings, xroad_instance, mocker.Mock())
    d.set_next_records_timestamp('key', 123)

    t = d.get_next_records_timestamp('key', 0)
    assert t == 123


@mongomock.patch(servers=(('defaultmongodb', 27017),))
def test_get_next_records_timestamp_non_existent_key(basic_settings, mocker):
    mongo_settings = basic_settings['mongodb']
    xroad_instance = basic_settings['xroad']['instance']

    d = DatabaseManager(mongo_settings, xroad_instance, mocker.Mock())

    t = d.get_next_records_timestamp('newkey', 0)
    assert t == pytest.approx(float(time.time()), 1)
