import pytest
import opmon_collector.update_servers as updater


@pytest.fixture()
def mock_clients(mocker):
    cs_client = mocker.Mock()
    cs_client.get_security_servers = mocker.Mock(return_value=[1, 2, 3])

    db_client = mocker.Mock()
    mocker.patch('opmon_collector.update_servers._init_clients', return_value=(cs_client, db_client))
    return cs_client, db_client


def test_update_database_server_list(mock_clients):
    updater.update_database_server_list('dummy_settings')
    cs_client, db_client = mock_clients
    cs_client.get_security_servers.assert_called_once_with()
    db_client.save_server_list_to_database.assert_called_once_with([1, 2, 3])


def test_print_server_list(mock_clients):
    updater.print_server_list('dummy_settings')
    cs_client, db_client = mock_clients
    cs_client.get_security_servers.assert_called_once_with()
    db_client.save_server_list_to_database.assert_not_called()
