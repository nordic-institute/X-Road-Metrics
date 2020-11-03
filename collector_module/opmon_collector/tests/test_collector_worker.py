import pytest
import os
import pathlib
import responses

from opmon_collector.collector_worker import CollectorWorker
from opmon_collector.database_manager import DatabaseManager
from opmon_collector.settings import OpmonSettingsManager


@pytest.fixture()
def mock_server_manager(mocker):
    manager = mocker.Mock()

    manager.insert_data_to_raw_messages = mocker.Mock()
    manager.get_soap_body = DatabaseManager.get_soap_body
    manager.get_soap_monitoring_client = DatabaseManager.get_soap_monitoring_client
    manager.get_timestamp = mocker.Mock(return_value=1605000000.123)
    manager.get_next_records_timestamp = mocker.Mock(return_value=1604000000.456)
    manager.set_next_records_timestamp = mocker.Mock()
    return manager


@pytest.fixture
def basic_settings():
    os.chdir(pathlib.Path(__file__).parent.absolute())
    return OpmonSettingsManager().settings


@pytest.fixture()
def basic_data(mocker, mock_server_manager, basic_settings):

    server = {
        'server': '--testservername--',
        'instance': 'DEFAULT',
        'memberClass': 'ORG',
        'memberCode': '1234',
        'subsystemCode': 'U-TEST',
        'serverCode': 's123'
    }

    data = {
        'settings': basic_settings,
        'server_data': server,
        'logger_manager': mocker.Mock(),
        'server_manager': mock_server_manager,

    }

    return data


@pytest.fixture()
def mock_response_content():
    with open("opmon_response.txt", "rb") as f:
        data = f.read()
    return data


@responses.activate
def test_collector_worker_without_retry(mock_server_manager, basic_data, mock_response_content):
    responses.add(responses.POST, 'http://x-road-ss', body=mock_response_content, status=200)

    worker = CollectorWorker(basic_data)
    result, error = worker.work()
    if error is not None:
        raise error

    assert result


