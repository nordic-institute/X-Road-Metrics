import os
import pathlib

import mongomock
import pytest

from opmon_corrector.correctord import handle_results, parse_args, run_batch
from opmon_corrector.logger_manager import LoggerManager
from opmon_corrector.settings_parser import OpmonSettingsManager

TEST_DIR = os.path.abspath(os.path.dirname(__file__))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def basic_settings():
    os.chdir(pathlib.Path(__file__).parent.absolute())
    return OpmonSettingsManager().settings

@pytest.fixture
def mongo_client():
    return mongomock.MongoClient()


@pytest.fixture
def logger_m(mocker):
    return mocker.MagicMock(spec=LoggerManager)


# ---------------------------------------------------------------------------
# parse_args
# ---------------------------------------------------------------------------

class TestParseArgs:

    def test_default_profile_is_none(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["correctord"])
        args = parse_args()
        assert args.profile is None

    def test_explicit_profile_is_parsed(self, monkeypatch):
        monkeypatch.setattr("sys.argv", ["correctord", "--profile", "PROD"])
        args = parse_args()
        assert args.profile == "PROD"


# ---------------------------------------------------------------------------
# handle_results
# ---------------------------------------------------------------------------


def test_handle_results_error_path_sleeps_for_wait_on_error_and_logs_heartbeat(
    mocker, basic_settings, logger_m
):
    mock_sleep = mocker.patch("opmon_corrector.correctord.time.sleep")
    handle_results({"doc_len": -1}, basic_settings, logger_m)

    mock_sleep.assert_called_once_with(basic_settings["corrector"]["wait-on-error"])
    logger_m.log_heartbeat.assert_called_once_with("error", "FAILED")

def test_handle_results_success_path_sleeps_five_seconds_and_does_not_log_error(
    mocker, basic_settings, logger_m
):
    mock_sleep = mocker.patch("opmon_corrector.correctord.time.sleep")
    handle_results({"doc_len": basic_settings["corrector"]["documents-min"] + 1}, basic_settings, logger_m)

    mock_sleep.assert_called_once_with(5)
    logger_m.log_error.assert_not_called()

# ---------------------------------------------------------------------------
# run_batch
# ---------------------------------------------------------------------------

def test_process_is_started_and_joined(mocker, basic_settings, logger_m):
    mocker.patch("opmon_corrector.correctord.CorrectorBatch")
    mocker.patch("opmon_corrector.correctord.Manager").return_value.dict.return_value = {"doc_len": 0}
    mock_process_instance = mocker.MagicMock()
    mocker.patch("opmon_corrector.correctord.Process").return_value = mock_process_instance

    run_batch(basic_settings, logger_m)

    mock_process_instance.start.assert_called_once()
    mock_process_instance.join.assert_called_once()
