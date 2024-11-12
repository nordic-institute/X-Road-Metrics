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
"""
Unit tests for main.py
"""
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

import pytest

import opmon_collector.main as main


@pytest.fixture()
def mock_collector(mocker):
    mocker.patch('opmon_collector.main.collector_main')
    mocker.patch('opmon_collector.main.update_database_server_list')
    mocker.patch('opmon_collector.main.print_server_list')


@pytest.fixture()
def mock_settings_manager(mocker):
    mock_settings_manager = mocker.Mock()
    mock_settings_manager.get = mocker.Mock(return_value='testvalue')
    mock_settings_manager.settings = 'testsettings'
    mocker.patch('opmon_collector.main.OpmonSettingsManager', return_value=mock_settings_manager)
    return mock_settings_manager


def test_action_collect(mocker, mock_collector, mock_settings_manager):
    mocker.patch('opmon_collector.main.settings_action_handler')
    mocker.patch('sys.argv', ['test_program_name', '--profile', 'TEST', 'collect'])

    main.main()
    main.OpmonSettingsManager.assert_called_once_with('TEST')
    main.collector_main.assert_called_once_with('testsettings')
    main.update_database_server_list.assert_not_called()
    main.print_server_list.assert_not_called()
    main.settings_action_handler.assert_not_called()


def test_action_update(mocker, mock_collector, mock_settings_manager):
    mocker.patch('opmon_collector.main.settings_action_handler')
    mocker.patch('sys.argv', ['test_program_name', '--profile', 'TEST', 'update'])

    main.main()
    main.OpmonSettingsManager.assert_called_once_with('TEST')
    main.collector_main.assert_not_called()
    main.update_database_server_list.assert_called_once_with('testsettings')
    main.print_server_list.assert_not_called()
    main.settings_action_handler.assert_not_called()


def test_action_list(mocker, mock_collector, mock_settings_manager):
    mocker.patch('opmon_collector.main.settings_action_handler')
    mocker.patch('sys.argv', ['test_program_name', '--profile', 'TEST', 'list'])

    main.main()
    main.OpmonSettingsManager.assert_called_once_with('TEST')
    main.collector_main.assert_not_called()
    main.update_database_server_list.assert_not_called()
    main.print_server_list.assert_called_once_with('testsettings')
    main.settings_action_handler.assert_not_called()


def test_action_settings_get(mocker, mock_collector, mock_settings_manager):
    mocker.patch('sys.argv', ['test_program_name', '--profile', 'TEST', 'settings', 'get', 'some.setting'])

    main.main()
    main.OpmonSettingsManager.assert_called_once_with('TEST')
    main.collector_main.assert_not_called()
    main.update_database_server_list.assert_not_called()
    main.print_server_list.assert_not_called()
    mock_settings_manager.get.assert_called_once_with('some.setting')


def test_invalid_action(mocker, mock_collector, mock_settings_manager):
    mocker.patch('sys.argv', ['test_program_name', '--unkown', 'args'])
    main.OpmonSettingsManager.assert_not_called()
    main.collector_main.assert_not_called()
    main.update_database_server_list.assert_not_called()
    main.print_server_list.assert_not_called()
