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

import pathlib
import os
import pytest

import metrics_opendata_collector.main as main


SOURCES_SETTINGS = {
    'TEST-SOURCE1': {
        'url': 'test url',
        'limit': 1000,
    },
    'TEST-SOURCE2': {
        'url': 'test url',
        'limit': 500,
    },
}

SETTINGS = {
    'opendata-collector': {
        'instance': 'TEST',
        'sources-settings-path': 'test_opendata_sources_settings.yaml',
        'sources-settings': SOURCES_SETTINGS,
    },
    'mongodb': {
        'host': 'localhost',
        'user': 'test_user',
        'password': 'test_password',
        'tls': None,
        'tls-ca-file': None
    },
    'logger': {
        'name': 'opendata-collector',
        'module': 'opendata-collector',
        'level': 'INFO',
        'log-path': '/var/log/xroad-metrics/opendata-collector/logs',
        'heartbeat-path': '/var/log/xroad-metrics/opendata-collector/heartbeat'
    }
}


@pytest.fixture
def set_dir():
    # take settings files from tests dir
    os.chdir(pathlib.Path(__file__).parent.absolute())


@pytest.mark.skip()
def test_action_collect(mocker, set_dir):
    mocker.patch('metrics_opendata_collector.main.collect_opendata')
    mocker.patch('sys.argv', ['test_program_name', '--profile', 'TEST', 'TEST-SOURCE1'])
    main.main()
    main.collect_opendata.assert_called_once_with(
        SETTINGS, SOURCES_SETTINGS['TEST-SOURCE1']
    )


def test_action_collect_playground(mocker, set_dir):
    mocker.patch('sys.argv', ['test_program_name', '--profile', 'TEST', 'PLAYGROUND-TEST'])
    main.main()
