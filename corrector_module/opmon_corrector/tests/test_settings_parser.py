#!/usr/bin/env python3

"""
Unit tests for collector settings.py
"""
import os
import pathlib
import pytest
from yaml import YAMLError

from opmon_corrector.settings_parser import OpmonSettingsManager


@pytest.fixture
def set_dir():
    os.chdir(pathlib.Path(__file__).parent.absolute())


def test_list_files_in_non_existing_dir(set_dir):
    files = OpmonSettingsManager._get_all_files('/testing/opmon/__notfound__/1234')
    assert len(files) == 0


def test_finding_settings_file(set_dir):
    file = OpmonSettingsManager._find_settings_file("UNITTEST")
    assert file == './settings_UNITTEST.yaml'


def test_loading_default_settings_file(set_dir):
    settings = OpmonSettingsManager().settings

    assert settings['xroad']['instance'] == 'DEFAULT'
    assert settings['mongodb'] == {
        'host': 'defaultmongodb',
        'user': 'defaultuser',
        'password': 'defaultpass'
    }


def test_loading_settings_file_with_profile(set_dir):
    settings = OpmonSettingsManager('UNITTEST').settings

    assert settings['xroad']['instance'] == 'UNITTEST'
    assert settings['mongodb'] == {
        'host': 'mongodb',
        'user': 'testuser',
        'password': 'testpass'
    }


def test_loading_non_existing_settings_file(set_dir):
    with pytest.raises(FileNotFoundError):
        settings = OpmonSettingsManager('NOTFOUND').settings


def test_loading_invalid_settings_file(set_dir):
    with pytest.raises(YAMLError):
        settings = OpmonSettingsManager('INVALID').settings


def test_get_setting(set_dir):
    sm = OpmonSettingsManager('UNITTEST')
    assert sm.get('xroad.monitoring-client.membercode') == 'B-code'
