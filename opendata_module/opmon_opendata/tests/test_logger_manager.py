import logging

from opmon_opendata.logger_manager import LoggerManager


def test_logger_manager_handler_is_single(tmp_path):
    # Regression test for
    # https://github.com/nordic-institute/X-Road-Metrics/pull/14/files

    temp_log_dir = tmp_path / 'log'
    temp_log_dir.mkdir()

    settings = {
        'name': 'iamsingle',
        'module': 'test',
        'level': 2,
        'log-path': temp_log_dir,
        'heartbeat-path': 'test',
    }
    LoggerManager(settings, 'test', '1')
    LoggerManager(settings, 'test', '1')
    LoggerManager(settings, 'test', '1')

    original_logger = logging.getLogger('iamsingle')
    assert len(original_logger.handlers) == 1
