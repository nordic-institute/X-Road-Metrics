import smtplib
import socket
from email.header import Header
from email.mime.text import MIMEText
from email.utils import make_msgid, formatdate, formataddr


class NotificationManager:
    def __init__(
            self,
            database_manager,
            logger_manager,
            email_settings
    ):
        """
        Creates a NotificationManager object that keeps the e-mail settings/parameters inside.
        :param database_manager: The DatabaseManager object.
        :param logger_manager: The LoggerManager object.
        :param email_settings: reports.email section of settings.yaml as a dictionary
        """
        self.database_manager = database_manager
        self.logger_manager = logger_manager
        self.settings = email_settings

    def add_item_to_queue(
            self,
            reports_arguments,
            report_name,
            email_info
    ):
        """
        Add notification to the queue (database).
        :param reports_arguments: OpmonReportsArguments object specifying target subsystem
        :param report_name: Name of the report.
        :param email_info: The list of emails and receiver names.
        :return:
        """
        self.database_manager.add_notification_to_queue(
            reports_arguments,
            report_name,
            email_info
        )

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
            'END_DATE': notification['end_date']
        }

        msg = MIMEText(self.settings['message'].format(
            EMAIL_NAME=receiver.get('name') or 'recipient',
            REPORT_NAME=notification['report_name'],
            **format_args
        ))

        msg['Subject'] = self.settings['subject'].format(**format_args)

        msg['From'] = self.settings['sender']
        msg['To'] = formataddr((str(Header(f'{receiver["name"]}', 'utf-8')), receiver["email"]))
        msg['Message-ID'] = make_msgid(domain=self.settings['smtp-host'])
        msg['Date'] = formatdate(localtime=True)

        s = smtplib.SMTP(host=self.settings['smtp-host'], port=self.settings['smtp-port'], timeout=15)
        s.helo(socket.gethostname())
        s.send_message(msg)
        s.quit()

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
