#!/usr/bin/env python3
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
Unit tests for collector settings.py
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

import os
import pathlib
import pytest
from yaml import YAMLError

from opmon_analyzer_ui.settings_parser import OpmonSettingsManager


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
