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
import asyncore
import smtpd
import threading

import pytest

from opmon_reports.notification_manager import NotificationManager

TEST_HOST = '127.0.0.1'
TEST_PORT = 1025

test_notification = {
    'x_road_instance': 'FOO',
    'member_class': 'BAR',
    'member_code': 'BAZ',
    'subsystem_code': 'sub1',
    'start_date': '2021-04-14',
    'end_date': '2021-04-14',
    'report_name': 'Test Report'
}

receiver = {
    'name': 'E. Mailer',
    'email': 'mailer@foo.org'
}


@pytest.fixture
def basic_settings():
    return {
        'sender': 'sender@foo.com',
        'subject': 'Hi!',
        'message': 'Hello, world!',
        'smtp': {
            'host': TEST_HOST,
            'port': TEST_PORT,
            'encryption': 'None'
        }
    }


class ThreadedSmtpServer:
    def __init__(self):
        self.thread = threading.Thread(target=asyncore.loop, name="SMTP Server Asyncore Loop")
        self.server = smtpd.DebuggingServer((TEST_HOST, TEST_PORT), None)
        self.thread.start()


@pytest.fixture
def smtp_thread():
    server = ThreadedSmtpServer()
    yield server
    server.server.close()
    server.thread.join()


def test_send_mail(basic_settings, smtp_thread, mocker, capsys):
    manager = NotificationManager(basic_settings, mocker.Mock(), mocker.Mock())
    manager.send_mail(test_notification, receiver)
    smtp_output = capsys.readouterr().out
    assert 'From: sender@foo.com' in smtp_output
    assert 'Subject: Hi!' in smtp_output
    assert 'Hello, world!' in smtp_output


# Tests below are only for manual use. Fill in some valid config for a real SMTP server to ssl_settings fixture,
# set your e-mail address into receiver and the test cases should send you an email.
# smtpd.DebuggingServer does not support TLS so it cannot be used to automatically test sending notifications over TLS.

@pytest.fixture
def ssl_settings(basic_settings):
    basic_settings['sender'] = 'opmon.tester@gmail.com'
    basic_settings['smtp'] = {
        'host': 'smtp.gmail.com',
        'port': 465,
        'encryption': 'TLS',
        'password': 'secret'
    }
    return basic_settings


@pytest.fixture
def startssl_settings(ssl_settings):
    ssl_settings['smtp']['encryption'] = 'STARTTLS'
    ssl_settings['smtp']['port'] = 587
    return ssl_settings


@pytest.mark.skip(reason="This test can be run only manually.")
def test_send_mail_explicit_ssl(ssl_settings, mocker):
    manager = NotificationManager(ssl_settings, mocker.Mock(), mocker.Mock())
    manager.send_mail(test_notification, receiver)


@pytest.mark.skip(reason="This test can be run only manually.")
def test_send_mail_startssl(startssl_settings, mocker):
    manager = NotificationManager(startssl_settings, mocker.Mock(), mocker.Mock())
    manager.send_mail(test_notification, receiver)
