import os
import pathlib

import pytest
import opmon_collector.update_servers as updater
from opmon_collector.settings import OpmonSettingsManager


@pytest.fixture()
def mock_clients(mocker):
    cs_client = mocker.Mock()
    cs_client.get_security_servers = mocker.Mock(return_value=[1, 2, 3])

    db_client = mocker.Mock()
    mocker.patch('opmon_collector.update_servers._init_clients', return_value=(cs_client, db_client))
    mocker.patch('opmon_collector.update_servers.LoggerManager', return_value=(mocker.Mock()))
    return cs_client, db_client


@pytest.fixture()
def basic_settings():
    os.chdir(pathlib.Path(__file__).parent.absolute())
    return OpmonSettingsManager().settings


@pytest.fixture(autouse=True)
def cleanup_test_pid_files():
    pid_file = './opmon_collector_DEFAULT.pid'
    if os.path.isfile(pid_file):
        os.remove(pid_file)


def test_update_database_server_list(mock_clients, basic_settings):
    updater.update_database_server_list(basic_settings)
    cs_client, db_client = mock_clients
    cs_client.get_security_servers.assert_called_once_with()
    db_client.save_server_list_to_database.assert_called_once_with([1, 2, 3])


def test_update_database_server_list_with_existing_pid_file(mock_clients, basic_settings):
    pid_file = './opmon_collector_DEFAULT.pid'
    cs_client, db_client = mock_clients

    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))  # write an existing pid into file

    with pytest.raises(RuntimeError):
        updater.update_database_server_list(basic_settings)

    cs_client.get_security_servers.assert_not_called()
    db_client.save_server_list_to_database.assert_not_called()


def test_print_server_list(mock_clients, basic_settings):
    updater.print_server_list(basic_settings)
    cs_client, db_client = mock_clients
    cs_client.get_security_servers.assert_called_once_with()
    db_client.save_server_list_to_database.assert_not_called()
