import pytest
import os
import pathlib
import responses

from opmon_collector.collector_worker import CollectorWorker
from opmon_collector.settings import OpmonSettingsManager
from opmon_collector.security_server_client import SecurityServerClient

NOW = 1605000000.123


@pytest.fixture()
def mock_server_manager(mocker):
    manager = mocker.Mock()

    manager.insert_data_to_raw_messages = mocker.Mock()
    manager.get_soap_body = SecurityServerClient.get_soap_body
    manager.get_soap_monitoring_client = SecurityServerClient.get_soap_monitoring_client
    manager.get_timestamp = mocker.Mock(return_value=NOW)
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
def mock_response_contents():
    os.chdir(pathlib.Path(__file__).parent.absolute())
    os.chdir('./responses')
    data = []
    filenames = ["opmon_response1.dat", "opmon_response2.dat"]
    for name in filenames:
        with open(name, "rb") as f:
            data.append(f.read())
    return data


@responses.activate
def test_collector_worker_work(mock_server_manager, basic_data, mock_response_contents):
    for content in mock_response_contents:
        responses.add(responses.POST, 'http://x-road-ss', body=content, status=200)

    worker = CollectorWorker(basic_data)
    result, error = worker.work()

    if error is not None:
        raise error

    assert mock_server_manager.set_next_records_timestamp.call_count == 2
    next_time_in_response1 = 1604420300
    mock_server_manager.set_next_records_timestamp.assert_any_call('--testservername--', next_time_in_response1)

    end_time = int(NOW) - basic_data['settings']['collector']['records-to-offset']
    mock_server_manager.set_next_records_timestamp.assert_any_call('--testservername--', end_time)

    mock_server_manager.insert_data_to_raw_messages.assert_called_once()
    records = mock_server_manager.insert_data_to_raw_messages.call_args_list[0][0][0]
    records_in_response1 = 5230
    assert len(records) == records_in_response1

    assert worker.status == CollectorWorker.Status.ALL_COLLECTED


@responses.activate
def test_collector_worker_work_max_repeats(mock_server_manager, basic_data, mock_response_contents):
    responses.add(responses.POST, 'http://x-road-ss', body=mock_response_contents[0], status=200)

    basic_data['settings']['collector']['repeat-limit'] = 1

    worker = CollectorWorker(basic_data)
    result, error = worker.work()

    if error is not None:
        raise error

    assert mock_server_manager.set_next_records_timestamp.call_count == 1
    next_time_in_response = 1604420300
    mock_server_manager.set_next_records_timestamp.assert_called_once_with('--testservername--', next_time_in_response)

    assert mock_server_manager.insert_data_to_raw_messages.call_count == 1
    mock_server_manager.insert_data_to_raw_messages.assert_called_once()
    records = mock_server_manager.insert_data_to_raw_messages.call_args_list[0][0][0]
    records_in_response1 = 5230
    assert len(records) == records_in_response1

    assert worker.status == CollectorWorker.Status.DATA_AVAILABLE


def test_worker_status(mock_server_manager, basic_data):
    worker = CollectorWorker(basic_data)

    assert worker.batch_start < worker.batch_end
    assert worker.batch_start > 3
    assert worker.status == CollectorWorker.Status.DATA_AVAILABLE

    worker.records = [i for i in range(1000)]
    assert worker.status == CollectorWorker.Status.DATA_AVAILABLE

    worker.records = [1, 2, 3]
    worker.update_status()
    assert worker.status == CollectorWorker.Status.TOO_SMALL_BATCH

    worker.status = CollectorWorker.Status.DATA_AVAILABLE
    worker.batch_start = worker.batch_end + 1
    worker.records = [i for i in range(1000)]
    worker.update_status()
    assert worker.status == CollectorWorker.Status.ALL_COLLECTED

    worker.status = CollectorWorker.Status.DATA_AVAILABLE
    worker.batch_start = worker.batch_end
    worker.update_status()
    assert worker.status == CollectorWorker.Status.ALL_COLLECTED
