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

import pytest
import os
import shutil
import json

from opmon_collector.logger_manager import LoggerManager


@pytest.fixture()
def log_path():
    log_path = '/tmp/opmon-tests/logs'
    shutil.rmtree(log_path, ignore_errors=True)
    os.makedirs(log_path)
    os.chdir(log_path)
    assert len(os.listdir(log_path)) == 0

    return log_path


@pytest.fixture()
def logger_settings(log_path):
    return {
        'name': 'defaultlog',
        'module': 'default',
        'level': 'DEBUG',
        'log-path': log_path,
        'heartbeat-path': log_path
    }


def log_on_every_level(logger):
    logger.log_info('test-info-activity', 'test-info-message')
    logger.log_warning('test-warn-activity', 'test-warn-message')
    logger.log_error('test-error-activity', 'test-error-message')


def read_log_rows(log_path, instance, type='log'):
    with open(f'{log_path}/{type}_defaultlog_{instance}.json', "r") as f:
        json_rows = f.readlines()

    return [json.loads(r) for r in json_rows]


def assert_levels(rows, expected_levels):
    for row, expected_level in zip(rows, expected_levels):
        assert row['level'] == expected_level


def assert_messages(rows, expected_messages):
    for row, expected_msg in zip(rows, expected_messages):
        assert row['msg'] == expected_msg


def assert_log_fields(rows):
    for row in rows:
        assert set(row.keys()) == {'activity', 'level', 'local_timestamp', 'module', 'msg', 'timestamp', 'version'}


def assert_heartbeat_fields(rows):
    for row in rows:
        assert set(row.keys()) == {'msg', 'timestamp', 'version', 'status', 'module', 'local_timestamp'}


def test_logging_without_limits(log_path, logger_settings):
    instance = 'INFOTEST'
    logger = LoggerManager(logger_settings, instance, '1')
    log_on_every_level(logger)

    rows = read_log_rows(log_path, instance)
    assert (len(rows) == 3)
    assert_levels(rows, ['INFO', 'WARNING', 'ERROR'])
    assert_log_fields(rows)


def test_logging_with_warning_limit(log_path, logger_settings):
    logger_settings['level'] = 'WARNING'
    instance = 'WARNTEST'
    logger = LoggerManager(logger_settings, instance, '1')
    log_on_every_level(logger)

    rows = read_log_rows(log_path, instance)
    assert (len(rows) == 2)
    assert_levels(rows, ['WARNING', 'ERROR'])
    assert_messages(rows, ['test-warn-message', 'test-error-message'])
    assert_log_fields(rows)


def test_logging_with_error_limit(log_path, logger_settings):
    logger_settings['level'] = 'ERROR'
    instance = 'ERRORTEST'
    logger = LoggerManager(logger_settings, instance, '')
    log_on_every_level(logger)

    rows = read_log_rows(log_path, instance)
    assert (len(rows) == 1)
    assert_levels(rows, ['ERROR'])
    assert_messages(rows, ['test-error-message'])
    assert_log_fields(rows)


def test_heartbeat(logger_settings, log_path):
    instance = 'HEARTBEATTEST'
    logger = LoggerManager(logger_settings, instance, '')
    logger.log_heartbeat('hb-test-msg', 'hb-test-status')
    logger.log_heartbeat('hb-test-msg2', 'hb-test-status2')
    rows = read_log_rows(log_path, instance, 'heartbeat')
    assert len(rows) == 1
    assert_heartbeat_fields(rows)

    assert rows[0]['msg'] == 'hb-test-msg2'
