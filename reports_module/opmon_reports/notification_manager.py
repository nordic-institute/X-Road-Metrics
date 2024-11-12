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

import os
import smtplib
import ssl
from typing import Iterable
from email.header import Header
from email.mime.text import MIMEText
from email.utils import make_msgid, formatdate, formataddr
from .database_manager import DatabaseManager
from .logger_manager import LoggerManager


class NotificationManager:
    def __init__(
            self,
            email_settings: dict,
            database_manager: DatabaseManager,
            logger_manager: LoggerManager
    ):
        """
        Creates a NotificationManager object that keeps the e-mail settings/parameters inside.
        :param email_settings: reports.email section of settings.yaml as a dictionary
        :param database_manager: DatabaseManager object.
        :param logger_manager: LoggerManager object.
        """

        logger_manager.log_info('create_notification_manager', 'Prepare notification manager.')
        self.database_manager = database_manager
        self.logger_manager = logger_manager
        self.settings = email_settings
        self.smtp_host = email_settings['smtp']['host']
        self.smtp_port = email_settings['smtp']['port']
        self.smtp_password = email_settings['smtp'].get('password')
        self.smtp_user = email_settings['smtp'].get('user') or email_settings['sender']

    def add_item_to_queue(self, target, report_name, receivers: Iterable[dict]):
        """
        Add notification to the queue (database).
        :param target: target subsystem
        :param report_name: Name of the report.
        :param receivers: The list of emails and receiver names.
        :return:
        """
        self.database_manager.add_notification_to_queue(target, report_name, receivers)

    def get_items_from_queue(self):
        """
        Gets all the notifications (documents) from the queue that haven't been processed yet.
        :return: Returns a list of notifications (documents) from the queue that haven't been processed yet.
        """
        not_processed_notifications = self.database_manager.get_not_processed_notifications()
        return not_processed_notifications

    def send_mail(self, notification: dict, receiver: dict):
        """
        Send e-mail based on the given input parameters.
        :param notification: dictionary with notification data
        :param receiver: dictionary with name and email of receiver
        :return:
        """

        format_args = {
            'X_ROAD_INSTANCE': notification['x_road_instance'],
            'MEMBER_CLASS': notification['member_class'],
            'MEMBER_CODE': notification['member_code'],
            'SUBSYSTEM_CODE': notification['subsystem_code'],
            'START_DATE': notification['start_date'],
            'END_DATE': notification['end_date'],
            'REPORT_NAME_NO_EXT': os.path.splitext(notification['report_name'])[0]
        }

        msg = MIMEText(self.settings['message'].format(
            EMAIL_NAME=receiver.get('name') or 'recipient',
            REPORT_NAME=notification['report_name'],
            **format_args
        ))

        msg['Subject'] = self.settings['subject'].format(**format_args)

        msg['From'] = self.settings['sender']
        msg['To'] = formataddr((str(Header(f'{receiver["name"]}', 'utf-8')), receiver["email"]))
        msg['Message-ID'] = make_msgid(domain=self.settings['smtp']['host'])
        msg['Date'] = formatdate(localtime=True)

        self._send_over_smtp(msg)

    def _get_smtp_context(self):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS)
        if self.settings['smtp'].get('certfile') and self.settings['smtp'].get('keyfile'):
            context.load_cert_chain(
                certfile=self.settings['smtp'].get('certfile'),
                keyfile=self.settings['smtp'].get('keyfile'))
        return context

    def _get_smtp_server(self):
        if self.settings['smtp']['encryption'] == 'TLS':
            return smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=self._get_smtp_context(), timeout=15)
        return smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15)

    def _send_over_smtp(self, msg):
        encryption = self.settings['smtp']['encryption']
        with self._get_smtp_server() as server:
            if encryption == 'STARTTLS':
                server.starttls(context=self._get_smtp_context())
            if self.smtp_password and encryption in ['TLS', 'STARTTLS']:
                server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)

    def mark_as_sent(self, object_id):
        """
        Mark the specified (object_id) notification as done in the queue.
        :param object_id: Notification object_id in the MongoDB
        :return:
        """
        self.database_manager.mark_as_sent(object_id)

    def mark_as_sent_error(self, object_id, error_message):
        """
        Mark the specified (object_id) notification as not sent in the queue.
        :param error_message: The message to be displayed in the MongoDB.
        :param object_id: Notification object_id in the MongoDB.
        :return:
        """
        self.database_manager.mark_as_sent_error(object_id, error_message)
