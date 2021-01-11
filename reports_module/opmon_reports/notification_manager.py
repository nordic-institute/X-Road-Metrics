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

    def send_mail(self, reports_arguments, receiver_email, receiver_name, report_name):
        """
        Send e-mail based on the given input parameters.
        :param reports_arguments: OpmonReportsArguments object
        :param receiver_email: The receiver e-mail.
        :param receiver_name: Receiver name string.
        :param report_name: Name of the report.
        :return:
        """

        msg = MIMEText(
            self.settings['message'].format(
                EMAIL_NAME=receiver_name,
                X_ROAD_INSTANCE=reports_arguments.xroad_instance,
                MEMBER_CLASS=reports_arguments.member_class,
                MEMBER_CODE=reports_arguments.member_code,
                SUBSYSTEM_CODE=reports_arguments.subsystem_code,
                START_DATE=reports_arguments.start_date,
                END_DATE=reports_arguments.end_date,
                REPORT_NAME=report_name
            )
        )
        msg['Subject'] = self.settings['subject'].format(
            X_ROAD_INSTANCE=reports_arguments.xroad_instance,
            MEMBER_CLASS=reports_arguments.member_class,
            MEMBER_CODE=reports_arguments.member_code,
            SUBSYSTEM_CODE=reports_arguments.subsystem_code,
            START_DATE=reports_arguments.start_date,
            END_DATE=reports_arguments.end_date,
        )
        msg['From'] = self.settings['sender']
        msg['To'] = formataddr((str(Header(f'{receiver_name}', 'utf-8')), receiver_email))
        msg['Message-ID'] = make_msgid(domain=self.settings['smtp-host'])
        msg['Date'] = formatdate(localtime=True)
        s = smtplib.SMTP(host=self.settings['smtp-host'], port=self.settings['smtp-port'])
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
