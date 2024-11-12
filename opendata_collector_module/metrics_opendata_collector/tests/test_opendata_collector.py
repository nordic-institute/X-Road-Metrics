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
import pathlib
from logging import StreamHandler
from unittest.mock import patch

import pytest
import vcr  # type: ignore
from requests.exceptions import ConnectionError

from metrics_opendata_collector.opendata_collector import collect_opendata
from metrics_opendata_collector.settings import MetricsSettingsManager


class MockCollection:
    def __init__(self):
        self._storage = []

    def insert_many(self, documents):
        self._storage.extend(documents)

    def insert_one(self, document):
        self._storage.append(document)

    def _find(self, query):
        return [
            item for item in self._storage
            if all(
                query_item in item.items()
                for query_item
                in query.items()
            )
        ]

    def find_one(self, query):
        found = None
        result = self._find(query)
        if result:
            if len(result) > 1:
                raise Exception('Multiple items found, not one')
            found = result[0]
        return found

    def update_one(self, query, update, upsert=False):
        entry_to_upsert = {}
        found = self.find_one(query)
        if found:
            entry_to_upsert.update(found)
            if upsert:
                self._storage.remove(found)

        else:
            entry_to_upsert.update(query)

        entry_to_upsert.update(update['$set'])
        self._storage.append(entry_to_upsert)

    def get_all(self):
        return self._storage


@pytest.fixture(autouse=True)
def mock_logger_manager(mocker):
    mocker.patch(
        'metrics_opendata_collector.logger_manager.LoggerManager._create_file_handler',
        return_value=StreamHandler()
    )
    yield mocker.Mock()


@pytest.fixture
def set_dir():
    # take settings files from tests dir
    os.chdir(pathlib.Path(__file__).parent.absolute())


@pytest.fixture
def mock_mongo_db(mocker):
    mock_client = mocker.MagicMock()
    db_mock = mocker.MagicMock()

    db_mock.state = MockCollection()
    db_mock.opendata_data = MockCollection()

    mock_client.__getitem__.return_value = db_mock
    mocker.patch(
        'metrics_opendata_collector.mongodb_manager.MongoClient',
        return_value=mock_client
    )
    yield db_mock


@vcr.use_cassette('fixtures/vcr_cassettes/get_harvest_all.yaml')
def test_collect_opendata_gets_all(set_dir, mocker, mock_mongo_db, caplog):
    # Gel all Opendata rows from 2023-03-27
    # Numbers of Opendata rows by requestindate

    # 2023-03-27    |   164
    # 2023-03-28    |    90
    # 2023-04-07    |     6
    settings_manager = MetricsSettingsManager('TEST')
    open_data_source_settings = settings_manager.get_opendata_source_settings('TEST-SOURCE1')
    open_data_source_settings['url'] = 'http://example/api/harvest'
    open_data_source_settings['from_dt'] = '2023-03-27T00:00:00'
    open_data_source_settings['limit'] = 10
    collect_opendata('TEST-SOURCE1', settings_manager)
    assert len(mock_mongo_db.opendata_data.get_all()) == 260
    assert mock_mongo_db.state.get_all() == [
        {
            'instance_id': 'TEST-SOURCE1',
            'last_inserted_requestints': 1680850800000,  # 2023-04-07T10:00:00
            'last_inserted_row_id': '16480'
        }
    ]
    assert 'TEST-SOURCE1: fetching opendata from_dt: 2023-03-27T00:00:00+0000, from_row_id: None' in caplog.text
    assert 'TEST-SOURCE1: total inserted 260 opendata documents into MongoDB' in caplog.text


@vcr.use_cassette('fixtures/vcr_cassettes/get_harvest_until.yaml')
def test_collect_opendata_gets_until(set_dir, mocker, mock_mongo_db, caplog):
    # Gel all Opendata rows for date 2023-03-28 and not later ones
    # Numbers of Opendata rows by requestindate

    # 2023-03-27    |   164
    # 2023-03-28    |    90
    # 2023-04-07    |     6
    settings_manager = MetricsSettingsManager('TEST')
    open_data_source_settings = settings_manager.get_opendata_source_settings('TEST-SOURCE1')
    open_data_source_settings['url'] = 'http://example/api/harvest'
    open_data_source_settings['from_dt'] = '2023-03-28T00:00:00'
    open_data_source_settings['until_dt'] = '2023-03-28T23:59:59'
    open_data_source_settings['limit'] = 10
    collect_opendata('TEST-SOURCE1', settings_manager)
    assert len(mock_mongo_db.opendata_data.get_all()) == 90
    assert mock_mongo_db.state.get_all() == [
        {
            'instance_id': 'TEST-SOURCE1',
            'last_inserted_requestints': 1680012000000,   # 2023-03-28T14:00:00
            'last_inserted_row_id': '16474'
        }
    ]
    assert 'TEST-SOURCE1: fetching opendata from_dt: 2023-03-28T00:00:00+0000, from_row_id: None' in caplog.text
    assert 'TEST-SOURCE1: total inserted 90 opendata documents into MongoDB' in caplog.text
    assert 'until_dt: 2023-03-28T23:59:59+0000' in caplog.text


def test_collect_opendata_with_state(set_dir, mocker, mock_mongo_db, caplog):
    mock_mongo_db.state.insert_one(
        {
            'instance_id': 'TEST-SOURCE1',
            'last_inserted_requestints': 1680850800000,  # 2023-04-07T10:00:00
            'last_inserted_row_id': '16480'
        }
    )
    settings_manager = MetricsSettingsManager('TEST')
    open_data_source_settings = settings_manager.get_opendata_source_settings('TEST-SOURCE1')
    open_data_source_settings['url'] = 'http://example/api/harvest'
    open_data_source_settings['from_dt'] = '2023-03-27T00:00:00'
    open_data_source_settings['opendata_api_tz_offset'] = '+0200'
    open_data_source_settings['limit'] = 10
    with patch('requests.get') as mock_get:
        mock_response = {'data': []}
        mock_get.return_value.json.return_value = mock_response
        collect_opendata('TEST-SOURCE1', settings_manager)
    assert not mock_mongo_db.opendata_data.get_all()
    assert 'TEST-SOURCE1: fetching opendata from_dt: 2023-04-07T07:00:00+0200, from_row_id: 16480' in caplog.text
    assert 'TEST-SOURCE1: total inserted 0 opendata documents into MongoDB' in caplog.text


def test_collect_opendata_error_from_dt_value(mock_mongo_db, caplog):
    settings_manager = MetricsSettingsManager('TEST')
    open_data_source_settings = settings_manager.get_opendata_source_settings('TEST-SOURCE1')
    open_data_source_settings['from_dt'] = '2023-03-27'
    collect_opendata('TEST-SOURCE1', settings_manager)
    assert not mock_mongo_db.opendata_data.get_all()
    assert 'params_preparation_failed' in caplog.text
    assert 'from_dt format should match format %Y-%m-%dT%H:%M:%S' in caplog.text


def test_collect_opendata_connection_error(set_dir, mocker, mock_mongo_db, caplog):
    settings_manager = MetricsSettingsManager('TEST')
    open_data_source_settings = settings_manager.get_opendata_source_settings('TEST-SOURCE1')
    open_data_source_settings['url'] = 'http://notvalid'
    open_data_source_settings['from_dt'] = '2023-03-27T00:00:00'
    open_data_source_settings['limit'] = 10
    with patch('requests.get') as mock_get:
        mock_get.side_effect = ConnectionError()
        collect_opendata('TEST-SOURCE1', settings_manager)
    assert not mock_mongo_db.opendata_data.get_all()
    assert 'get_opendata_connection_failed' in caplog.text
    assert f'Connection to {open_data_source_settings["url"]} failed' in caplog.text
