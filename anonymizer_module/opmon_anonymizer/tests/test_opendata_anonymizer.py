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
from logging import StreamHandler
from operator import eq, gt, is_not, le, lt
from typing import Dict, List, Optional, Union

import pytest

from opmon_anonymizer.iio.mongodbmanager import MongoDbOpenDataManager
from opmon_anonymizer.opendata_anonymizer import OpenDataAnonymizer
from opmon_anonymizer.utils import logger_manager


class MockResult:
    def __init__(self, data=None):
        self._data = data

    def sort(self, key, ordering):
        reverse = False
        if ordering == -1:
            reverse = True
        return sorted(self._data, key=lambda d: d[key], reverse=reverse)


class MockCollection:
    def __init__(self):
        self._storage = []

    def insert_many(self, documents: List[Dict[str, Union[str, int]]]) -> None:
        self._storage.extend(documents)

    def find(self, query: Optional[dict] = None,
             projection: Optional[dict] = None,
             no_cursor_timeout: bool = True
             ) -> 'MockResult':
        if not query:
            query = {}
        if not projection:
            projection = {}
        data = self._find(query)
        if projection:
            data = self._set_projection(projection, data)
        return MockResult(data)

    def _set_projection(self, projection: Optional[dict] = None,
                        data: Optional[List[dict]] = None
                        ) -> List[Dict[str, Union[str, int]]]:
        if projection is None:
            projection = {}
        if data is None:
            data = []
        projected_data = []
        for item in data:
            new_item = {}
            for field, value in projection.items():
                if value is True and field in item:
                    new_item[field] = item[field]
            if new_item:
                projected_data.append(new_item)
        return projected_data

    def insert_one(self, document: dict) -> None:
        self._storage.append(document)

    def update(self, query: dict, update: dict, upsert: bool = False) -> None:
        entry_to_upsert = {}
        found = self.find_one(query)
        if found:
            entry_to_upsert.update(found)
            if upsert:
                self._storage.remove(found)

        else:
            entry_to_upsert.update(query)

        entry_to_upsert.update(update)
        self._storage.append(entry_to_upsert)

    def _match(self, query: dict, item: dict) -> bool:
        return all(
            [
                operator(item.get(query['field']), query['value'])
                for operator in query['operators']
            ]
        )

    def _find(self, query: dict) -> List[dict]:
        prepared_query = self._prepare_query(query)
        return [
            item for item in self._storage
            if all(
                self._match(query_item, item)
                for query_item
                in prepared_query
            )
        ]

    def _prepare_query(self, query: dict) -> List[dict]:
        prepared_queries = []
        for key, item in query.items():
            if isinstance(item, str):
                prepared_queries.append({
                    'field': key,
                    'value': item,
                    'operators': [eq]
                })
            if isinstance(item, dict):
                for q_key, q_item in item.items():
                    if q_key == '$gt':
                        prepared_queries.append({
                            'field': key,
                            'value': q_item,
                            'operators': [gt]
                        })
                    if q_key == '$lte':
                        prepared_queries.append({
                            'field': key,
                            'value': q_item,
                            'operators': [lt, le]
                        })
                    if q_key == '$ne':
                        prepared_queries.append({
                            'field': key,
                            'value': q_item,
                            'operators': [is_not]
                        })

        return prepared_queries

    def find_one(self, query: Optional[dict] = None) -> Optional[dict]:
        if query is None:
            query = {}
        found = None
        result = self._find(query)
        if result:
            if len(result) > 1:
                raise Exception('Multiple items found, not one')
            found = result[0]
        return found

    def update_one(self, query: dict, update: dict, upsert: bool = False) -> None:
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

    def get_all(self) -> List[dict]:
        return self._storage


@pytest.fixture
def mongodb_client(mocker):
    mock_client = mocker.MagicMock()
    db_mock = mocker.MagicMock()

    db_mock.opendata_state = MockCollection()
    db_mock.opendata_data = MockCollection()

    mock_client.__getitem__.return_value = db_mock
    mocker.patch(
        'opmon_anonymizer.iio.mongodbmanager.MongoClient',
        return_value=mock_client
    )
    yield db_mock


SETTINGS = {
    'xroad': {
        'instance': 'test'
    },
    'anonymizer': {
        'field-translations-file': '',
        'hiding-rules': [],
        'substitution-rules': [],
        'transformers': {
            'reduce-request-in-ts-precision': False,
            'force-durations-to-integer-range': False
        },
    },
    'logger': {
        'name': 'test',
        'module': 'anonymizer',
        'level': 'DEBUG',
        'log-path': 'test',
        'heartbeat-path': 'test'
    },
    'postgres': {
        'buffer-size': 10
    },
    'mongodb': {
        'user': 'test',
        'password': 'test',
        'host': 'test',
    },
}


@pytest.fixture
def writer(mocker):
    yield mocker.Mock()


@pytest.fixture
def field_trans_file(mocker, tmp_path):
    test_file = os.path.join(tmp_path, 'test_file.list')
    with open(test_file, 'w') as ff:
        ff.write(
            'not-important -> clientXRoadInstance \n'
            'not-important -> _id'
        )
    SETTINGS['anonymizer']['field-translations-file'] = test_file


def test_anonymize_success(mocker, mongodb_client, writer, caplog, field_trans_file):
    mocker.patch('opmon_anonymizer.utils.logger_manager.LoggerManager._create_file_handler', return_value=StreamHandler())
    mongodb_client.opendata_data.insert_many(
        [
            {
                '_id': 'test',
                'insertTime': 2,
                'clientXRoadInstance': 'Test'
            },
            {
                '_id': 'test',
                'insertTime': 10,
                'clientXRoadInstance': 'Test'
            }
        ]
    )

    logger = logger_manager.LoggerManager(SETTINGS['logger'], SETTINGS['xroad']['instance'], '1.0.0')
    reader = MongoDbOpenDataManager(SETTINGS, logger)
    anonymizer_instance = OpenDataAnonymizer(reader, writer, SETTINGS, logger)
    records = anonymizer_instance.anonymize(100)
    assert records == 2
    assert 'OpenDataAnonymizationJob.run' in caplog.text
    assert 'Processing done. Records to write 2' in caplog.text
