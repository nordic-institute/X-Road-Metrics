import pytest
import os
import pathlib

from opmon_collector.settings import OpmonSettingsManager
from opmon_collector.collector_multiprocessing import run_threaded_collector
from opmon_collector.collector_multiprocessing import process_thread_pool
import opmon_collector


TEST_SERVERS = [1, 2, 3]


@pytest.fixture()
def mock_server_manager(mocker):
    manager = mocker.Mock()
    manager.get_server_list_from_database = mocker.Mock(return_value=(TEST_SERVERS, 1))
    mocker.patch('opmon_collector.collector_multiprocessing.DatabaseManager', return_value=manager)
    return manager


@pytest.fixture()
def basic_settings():
    os.chdir(pathlib.Path(__file__).parent.absolute())
    return OpmonSettingsManager().settings


@pytest.fixture()
def mock_thread_pool(mocker):
    pool = mocker.Mock()
    pool.map = mocker.Mock(return_value=([(True, None), (False, FileNotFoundError('test error')), (True, None)]))
    mocker.patch('opmon_collector.collector_multiprocessing.Pool', return_value=pool)
    return pool


def mock_thread(test_input):
    if test_input == 2:
        return False, FileNotFoundError('test error')
    return True, None


def test_run_threaded_collector(mocker, mock_server_manager, mock_thread_pool, basic_settings):
    mock_logger = mocker.Mock()
    run_threaded_collector(mock_logger, basic_settings)

    assert mock_thread_pool.map.call_count == 1
    args, _ = mock_thread_pool.map.call_args
    function, inputs = args

    assert function == opmon_collector.collector_multiprocessing.run_collector_thread

    assert len(inputs) == 3
    for i in inputs:
        assert i['settings'] == basic_settings
        assert i['server_data'] in TEST_SERVERS


def test_process_thread_pool():
    settings = {'collector': {'thread-count': 5}}
    inputs = [1, 2, 3]
    opmon_collector.collector_multiprocessing.run_collector_thread = mock_thread
    done, error = process_thread_pool(settings, inputs)

    assert done == 2
    assert error == 1
