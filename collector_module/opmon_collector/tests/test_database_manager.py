#!/usr/bin/env python3
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

"""
Unit tests for database_manager.py
"""
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

    # Verify that no timestamp is found for server 'test-server' in mock db
    collection = pymongo.MongoClient(d.mongo_uri)[d.db_collector_state]['collector_pointer']
    document = collection.find_one({'server': 'test-server'})
    assert document is None

    # Verify that a new timestamp can be added
    d.set_next_records_timestamp('test-server', 123)
    t = d.get_next_records_timestamp('test-server', 0)
    assert t == 123

    # Verify that an existing timestamp can be changed
    d.set_next_records_timestamp('test-server', 456)
    t = d.get_next_records_timestamp('test-server', 0)
    assert t == 456


@mongomock.patch(servers=(('defaultmongodb', 27017),))
def test_get_next_records_timestamp_non_existent_key(basic_settings, mocker):
    mongo_settings = basic_settings['mongodb']
    xroad_instance = basic_settings['xroad']['instance']

    d = DatabaseManager(mongo_settings, xroad_instance, mocker.Mock())

    t = d.get_next_records_timestamp('newkey', 0)
    assert t == pytest.approx(float(time.time()), 1)
