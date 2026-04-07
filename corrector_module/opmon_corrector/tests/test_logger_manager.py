import json
import os

import mongomock
import pytest
import shutil


from opmon_corrector.logger_manager import LoggerManager

TEST_DIR = os.path.abspath(os.path.dirname(__file__))

FROZEN_TIME = "2024-06-01 12:00:00"
FROZEN_TIMESTAMP = 1717243200


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def log_path():
    log_path = '/tmp/opmon-tests/logs'
    shutil.rmtree(log_path, ignore_errors=True)
    os.makedirs(log_path)
    os.chdir(log_path)
    assert len(os.listdir(log_path)) == 0

    return log_path

@pytest.fixture
def mongo_client():
    return mongomock.MongoClient()

@pytest.fixture()
def logger_settings(log_path):
    return {
        'name': 'defaultlog',
        'module': 'default',
        'log-path': log_path,
        'heartbeat-path': log_path,
        'level': 'DEBUG',

    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def log_on_every_level(logger):
    logger.log_info('test-info-activity', 'test-info-message')
    logger.log_warning('test-warn-activity', 'test-warn-message')
    logger.log_error('test-error-activity', 'test-error-message')


def read_log_rows(log_path, instance, type='log'):
    with open(f'{log_path}/{type}_defaultlog_{instance}.json', 'r') as f:
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


# ---------------------------------------------------------------------------
# log_info / log_warning / log_error
# ---------------------------------------------------------------------------

def test_logging_without_limits(log_path, logger_settings):
    logger = LoggerManager(logger_settings, 'INFOTEST', '1')
    log_on_every_level(logger)

    rows = read_log_rows(log_path, 'INFOTEST')
    assert len(rows) == 3
    assert_levels(rows, ['INFO', 'WARNING', 'ERROR'])
    assert_messages(rows, ['test-info-message', 'test-warn-message', 'test-error-message'])
    assert_log_fields(rows)


def test_logging_with_warning_limit(log_path, logger_settings):
    logger_settings['level'] = 'WARNING'
    instance = 'WARNTEST'
    logger = LoggerManager(logger_settings, 'WARNTEST', '1')
    log_on_every_level(logger)

    rows = read_log_rows(log_path, instance)
    assert (len(rows) == 2)
    assert_levels(rows, ['WARNING', 'ERROR'])
    assert_messages(rows, ['test-warn-message', 'test-error-message'])
    assert_log_fields(rows)

def test_logging_with_error_limit(log_path, logger_settings):
    logger_settings['level'] = 'ERROR'
    instance = 'ERRORTEST'
    logger = LoggerManager(logger_settings, 'ERRORTEST', '1')
    log_on_every_level(logger)

    rows = read_log_rows(log_path, instance)
    assert (len(rows) == 1)
    assert_levels(rows, ['ERROR'])
    assert_messages(rows, ['test-error-message'])
    assert_log_fields(rows)


# ---------------------------------------------------------------------------
# log_exception
# ---------------------------------------------------------------------------

def test_log_exception_writes_error_level_and_fields(log_path, logger_settings):
    logger = LoggerManager(logger_settings, 'EXCTEST', '1')
    logger.log_exception('test-exc-activity', 'test-exc-message')

    log_file = os.path.join(log_path, f'log_defaultlog_EXCTEST.json')
    assert os.path.exists(log_file)

    with open(log_file, 'r') as f:
        rows = f.readlines()
        assert len(rows) == 2
        data = json.loads(rows[0])
        assert data['level'] == 'ERROR'
        assert data['msg'] == 'test-exc-message'
        assert rows[1] == 'NoneType: None\n'


# ---------------------------------------------------------------------------
# log_heartbeat
# ---------------------------------------------------------------------------

def test_heartbeat(logger_settings, log_path):
    instance = 'HEARTBEATTEST'
    logger = LoggerManager(logger_settings, instance, '')
    logger.log_heartbeat('hb-test-msg', 'hb-test-status')
    logger.log_heartbeat('hb-test-msg2', 'hb-test-status2')
    rows = read_log_rows(log_path, instance, 'heartbeat')
    assert len(rows) == 1
    assert_heartbeat_fields(rows)

    assert rows[0]['msg'] == 'hb-test-msg2'
