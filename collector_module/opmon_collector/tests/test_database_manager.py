#!/usr/bin/env python3

"""
Unit tests for database_manager.py
"""
import pytest
import os
import pathlib
import time
from io import StringIO
import xml.etree.ElementTree as ET
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

    d = DatabaseManager(mongo_settings, basic_settings['xroad'], 'testlogmanager')
    assert d.mongo_uri == \
           f"mongodb://{mongo_settings['user']}:{mongo_settings['password']}@{mongo_settings['host']}/auth_db"

    assert d.db_name == 'query_db_DEFAULT'
    assert d.db_collector_state == 'collector_state_DEFAULT'
    assert d.collector_id == 'collector_DEFAULT'
    assert d.logger_m == 'testlogmanager'


@mongomock.patch(servers=(('defaultmongodb', 27017),))
def test_save_server_list_to_database(basic_settings, mocker):
    d = DatabaseManager(basic_settings['mongodb'], basic_settings['xroad'], mocker.Mock())
    d.save_server_list_to_database([1, 2, 3])

    server_list, timestamp = d.get_server_list_from_database()
    assert timestamp == pytest.approx(float(time.time()), abs=1)
    assert server_list == [1, 2, 3]


@mongomock.patch(servers=(('defaultmongodb', 27017),))
def test_insert_data_to_raw_messages(basic_settings, mocker):
    d = DatabaseManager(basic_settings['mongodb'], basic_settings['xroad'], mocker.Mock())
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
    d = DatabaseManager(basic_settings['mongodb'], basic_settings['xroad'], mocker.Mock())
    d.set_next_records_timestamp('key', 123)

    t = d.get_next_records_timestamp('key', 0)
    assert t == 123


@mongomock.patch(servers=(('defaultmongodb', 27017),))
def test_get_next_records_timestamp_non_existent_key(basic_settings, mocker):
    d = DatabaseManager(basic_settings['mongodb'], basic_settings['xroad'], mocker.Mock())

    t = d.get_next_records_timestamp('newkey', 0)
    assert t == pytest.approx(float(time.time()), 1)


def test_get_soap_body():
    xroad_settings = {
        'instance': 'DEV',
        'monitoring-client': {
            'memberclass': 'testclass',
            'membercode': 'testcode',
            'subsystemcode': 'testsubcode'
        }
    }

    serverdata = {
        'instance': 'DEV',
        'memberClass': 'targetclass',
        'memberCode': 'targetcode',
        'serverCode': 'targetserver'
    }

    reqid = '123'
    recordsfrom = '12'
    recordsto = '34'

    client_xml = DatabaseManager.get_soap_monitoring_client(xroad_settings)
    full_xml = DatabaseManager.get_soap_body(
        client_xml,
        serverdata,
        reqid,
        recordsfrom,
        recordsto
    )

    root = _parse_xml_without_namespaces(full_xml)

    _assert_client_tag(root[0][0], xroad_settings)
    _assert_service_tag(root[0][1], xroad_settings, serverdata)
    _assert_server_tag(root[0][2], xroad_settings, serverdata)
    _assert_id_tag(root[0][3], reqid)
    _assert_search_criteria_tag(root[1][0][0], recordsfrom, recordsto)


def _assert_client_tag(client, xroad_settings):
    assert client.tag == 'client'
    assert client.find('xRoadInstance').text == xroad_settings['instance']
    assert client.find('memberClass').text == xroad_settings['monitoring-client']['memberclass']
    assert client.find('memberCode').text == xroad_settings['monitoring-client']['membercode']


def _assert_service_tag(service, xroad_settings, serverdata):
    assert service.tag == 'service'
    assert service.find('xRoadInstance').text == xroad_settings['instance']
    assert service.find('memberClass').text == serverdata['memberClass']
    assert service.find('memberCode').text == serverdata['memberCode']


def _assert_server_tag(server, xroad_settings, serverdata):
    assert server.tag == 'securityServer'
    assert server.find('xRoadInstance').text == xroad_settings['instance']
    assert server.find('memberClass').text == serverdata['memberClass']
    assert server.find('memberCode').text == serverdata['memberCode']
    assert server.find('serverCode').text == serverdata['serverCode']


def _assert_id_tag(id_tag, reqid):
    assert id_tag.tag == 'id'
    assert id_tag.text == reqid


def _assert_search_criteria_tag(search_criteria, recordsfrom, recordsto):
    assert search_criteria.tag == 'searchCriteria'
    assert search_criteria.find('recordsFrom').text == recordsfrom
    assert search_criteria.find('recordsTo').text == recordsto


def _parse_xml_without_namespaces(xml):
    it = ET.iterparse(StringIO(xml))
    for _, el in it:
        prefix, has_namespace, postfix = el.tag.partition('}')
        if has_namespace:
            el.tag = postfix
    return it.root
