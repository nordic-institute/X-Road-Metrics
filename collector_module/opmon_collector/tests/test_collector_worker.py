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

import os
import pathlib
from logging import StreamHandler

import pytest
import responses

from opmon_collector.collector_worker import CollectorWorker
from opmon_collector.logger_manager import LoggerManager
from opmon_collector.security_server_client import SecurityServerClient
from opmon_collector.settings import OpmonSettingsManager

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
def mock_response_contents(request):
    os.chdir(pathlib.Path(__file__).parent.absolute())
    os.chdir('./responses')
    data = []
    for name in request.param:
        with open(name, 'rb') as f:
            data.append(f.read())
    return data


@responses.activate
@pytest.mark.parametrize(
    'mock_response_contents', [('metrics_response1.dat', 'metrics_response2.dat')], indirect=True
)
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
@pytest.mark.parametrize(
    'mock_response_contents', [('metrics_response1.dat',)], indirect=True
)
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


@responses.activate
@pytest.mark.parametrize('documents_log_dir, num_records_logged_to_file', [('Test', 5230), (None, 0)])
@pytest.mark.parametrize(
    'mock_response_contents', [('metrics_response1.dat',)], indirect=True
)
def test_collector_worker_logs_to_file(documents_log_dir, num_records_logged_to_file,
                                       mock_server_manager, basic_data, mock_response_contents, caplog):
    responses.add(responses.POST, 'http://x-road-ss', body=mock_response_contents[0], status=200)

    basic_data['settings']['collector']['documents-log-directory'] = documents_log_dir
    basic_data['settings']['collector']['repeat-limit'] = 1

    worker = CollectorWorker(basic_data)
    result, error = worker.work()

    if error is not None:
        raise error
    records = mock_server_manager.insert_data_to_raw_messages.call_args_list[0][0][0]

    assert len(records) == 5230
    assert len(caplog.records) == num_records_logged_to_file


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


@responses.activate
@pytest.mark.parametrize(
    'mock_response_contents', [('metrics_client_proxy_ssl_auth_failed.dat',)], indirect=True
)
def test_collector_worker_client_fault_response(basic_data, mock_response_contents, basic_settings, caplog, mocker):

    mocker.patch('opmon_collector.logger_manager.LoggerManager._create_file_handler', return_value=StreamHandler())
    responses.add(responses.POST, 'http://x-road-ss', body=mock_response_contents[0], status=200)

    settings = basic_settings
    logger_m = LoggerManager(settings['logger'], settings['xroad']['instance'], 'v1')
    basic_data['logger_manager'] = logger_m
    worker = CollectorWorker(basic_data)
    result, error = worker.work()
    assert result is False
    assert error
    assert worker.status == CollectorWorker.Status.DATA_AVAILABLE
    server_client_error_msg = (
        'Collector caught exception. Server: --testservername-- Cause: '
        'ServerClientProxyError(\'Message: Client (SUBSYSTEM:PLAYGROUND/COM/1234567-8/TestClient) '
        'specifies HTTPS but did not supply TLS certificate. '
        'Code: Server.ClientProxy.SslAuthenticationFailed. '
        'Detail: b782c3a4-f279-43d1-8684-2af318ec2ca5\')')
    assert server_client_error_msg in caplog.text, 'Expected error message not found in caplog'


@responses.activate
@pytest.mark.parametrize(
    'mock_response_contents', [
        ('metrics_server_proxy_access_denied_failed.dat',)],
    indirect=True
)
def test_collector_worker_server_fault_response(basic_data, mock_response_contents, basic_settings, caplog, mocker):

    mocker.patch('opmon_collector.logger_manager.LoggerManager._create_file_handler', return_value=StreamHandler())
    responses.add(responses.POST, 'http://x-road-ss', body=mock_response_contents[0], status=200)

    settings = basic_settings
    logger_m = LoggerManager(settings['logger'], settings['xroad']['instance'], 'v1')
    basic_data['logger_manager'] = logger_m
    worker = CollectorWorker(basic_data)
    result, error = worker.work()
    assert result is False
    assert error
    assert worker.status == CollectorWorker.Status.DATA_AVAILABLE
    server_error_msg = (
        'Message: Request is not allowed: '
        'SERVICE: instanceIdentifier/memberClass/memberCode/subsystemCode/serviceCode/serviceVersion. '
        'Code: Server.ServerProxy.AccessDenied. Detail: 132ff5d7-a6c7-4807-968e-430c515bf32a'
    )
    assert server_error_msg in caplog.text, 'Expected error message not found in caplog'
