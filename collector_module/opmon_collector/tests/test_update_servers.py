import pytest
import opmon_collector.update_servers as updater


@pytest.fixture()
def mock_server_manager(mocker):
    manager = mocker.Mock()
    manager.get_list_from_central_server = mocker.Mock(return_value=[1, 2, 3])
    mocker.patch('opmon_collector.update_servers._init_server_manager', return_value=manager)
    return manager


def test_update_database_server_list(mock_server_manager):
    updater.update_database_server_list('dummy_settings')
    mock_server_manager.get_list_from_central_server.assert_called_once_with()
    mock_server_manager.save_server_list_to_database.assert_called_once_with([1, 2, 3])


def test_print_server_list(mock_server_manager):
    updater.print_server_list('dummy_settings')
    mock_server_manager.get_list_from_central_server.assert_called_once_with()
    mock_server_manager.save_server_list_to_database.assert_not_called()
