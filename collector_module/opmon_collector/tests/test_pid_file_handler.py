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
import os
import pathlib
import shutil

from opmon_collector.settings import OpmonSettingsManager
from opmon_collector.pid_file_handler import OpmonPidFileHandler


@pytest.fixture()
def basic_settings():
    os.chdir(pathlib.Path(__file__).parent.absolute())
    return OpmonSettingsManager().settings


@pytest.fixture(autouse=True)
def cleanup_test_pid_files():
    pid_file = './xroad_metrics_collector_DEFAULT.pid'
    if os.path.isfile(pid_file):
        os.remove(pid_file)


@pytest.fixture()
def non_existing_dir():
    non_existing_dir = "/tmp/opmon/test/nonexist"
    shutil.rmtree(non_existing_dir, ignore_errors=True)
    return non_existing_dir


def test_pid_file_handler_init(basic_settings):
    handler = OpmonPidFileHandler(basic_settings)
    assert handler.pid_file == './xroad_metrics_collector_DEFAULT.pid'
    assert not handler.file_created


def test_pid_exists_basic(mocker):
    mocker.patch('os.kill', return_value=True)
    assert OpmonPidFileHandler.pid_exists(1)


def test_pid_exists_negative_input():
    assert not OpmonPidFileHandler.pid_exists(-1)


def test_pid_exists_process_not_found(mocker):
    mocker.patch('os.kill', side_effect=ProcessLookupError(""))
    assert not OpmonPidFileHandler.pid_exists(1)


def test_pid_exists_process_exists_but_no_permission(mocker):
    mocker.patch('os.kill', side_effect=PermissionError(""))
    assert OpmonPidFileHandler.pid_exists(1)


def test_create_pid_file(basic_settings):
    handler = OpmonPidFileHandler(basic_settings)

    pid_file = './xroad_metrics_collector_DEFAULT.pid'
    assert not os.path.isfile(pid_file)

    handler.create_pid_file()
    assert os.path.isfile(pid_file)

    with open(pid_file, 'r') as f:
        int(f.readline())

    assert handler.file_created


def test_create_pid_file_to_non_existing_path(basic_settings, non_existing_dir):
    basic_settings['collector']['pid-directory'] = non_existing_dir
    handler = OpmonPidFileHandler(basic_settings)

    pid_file = f'{non_existing_dir}/xroad_metrics_collector_DEFAULT.pid'
    assert not os.path.isdir(non_existing_dir)

    handler.create_pid_file()
    assert os.path.isfile(pid_file)


def create_pid_file_when_pid_exists(basic_settings):
    pid_file = './xroad_metrics_collector_DEFAULT.pid'
    handler = OpmonPidFileHandler(basic_settings)
    assert not os.path.isfile(pid_file)

    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))  # write an existing pid into file

    with pytest.raises(RuntimeError):
        handler.create_pid_file()


def test_another_instance_is_running(basic_settings):
    handler = OpmonPidFileHandler(basic_settings)

    pid_file = './xroad_metrics_collector_DEFAULT.pid'
    assert not os.path.isfile(pid_file)
    assert not handler.another_instance_is_running()

    handler.create_pid_file()
    assert handler.another_instance_is_running()


def test_another_instance_is_running_with_stale_file(basic_settings):
    handler = OpmonPidFileHandler(basic_settings)

    pid_file = './xroad_metrics_collector_DEFAULT.pid'
    assert not os.path.isfile(pid_file)

    with open(pid_file, 'w') as f:
        f.write(str(999999999))  # no process should have a pid this big

    assert not handler.another_instance_is_running()
    assert not os.path.isfile(pid_file)


def test_another_instance_is_running_with_invalid_file(basic_settings):
    handler = OpmonPidFileHandler(basic_settings)

    pid_file = './xroad_metrics_collector_DEFAULT.pid'
    assert not os.path.isfile(pid_file)

    with open(pid_file, 'w') as f:
        f.write("blah")

    assert not handler.another_instance_is_running()
    assert not handler.another_instance_is_running()
    assert not os.path.isfile(pid_file)


def test_cleanup(basic_settings):
    handler = OpmonPidFileHandler(basic_settings)

    pid_file = './xroad_metrics_collector_DEFAULT.pid'
    assert not os.path.isfile(pid_file)

    handler.create_pid_file()
    assert os.path.isfile(pid_file)

    handler._cleanup()
    assert not os.path.isfile(pid_file)

    handler._cleanup()  # should not raise FileNotFoundException


def test_cleanup_only_if_handler_created_a_file(basic_settings):
    handler = OpmonPidFileHandler(basic_settings)

    pid_file = './xroad_metrics_collector_DEFAULT.pid'
    assert not os.path.isfile(pid_file)

    pid_file = './xroad_metrics_collector_DEFAULT.pid'
    assert not os.path.isfile(pid_file)

    with open(pid_file, 'w') as f:
        f.write("blah")

    handler._cleanup()
    assert os.path.isfile(pid_file)
