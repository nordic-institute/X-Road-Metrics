import smtplib
import socket
from email.header import Header
from email.mime.text import MIMEText
from email.utils import make_msgid, formatdate, formataddr


class NotificationManager:
    def __init__(self, database_manager, logger_manager, sender_email, smtp_host, smtp_port, notification_username,
                 message, subject):
        """
        Creates a NotificationManager object that keeps the e-mail settings/parameters inside.
        :param database_manager: The DatabaseManager object.
        :param logger_manager: The LoggerManager object.
        :param sender_email: The sender e-mail.
        :param smtp_host: The SMTP host url.
        :param smtp_port: The SMTP port.
        :param notification_username: The username identifier.
        :param message: The e-mail body message.
        :param subject: The e-mail subject string.
        """
        self.database_manager = database_manager
        self.logger_manager = logger_manager
        self.sender_email = sender_email
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.notification_username = notification_username
        self.message = message
        self.subject = subject

    def add_item_to_queue(self, member_code, subsystem_code, member_class, x_road_instance, start_date, end_date,
                          language, report_name, email_info):
        """
        Add notification to the queue (database).
        :param email_info: The list of emails and receiver names.
        :param member_code: The memberCode string.
        :param subsystem_code: The subsystemCode string.
        :param member_class: The memberClass string.
        :param x_road_instance: The xRoadInstance string.
        :param start_date: The start_date string.
        :param end_date: The end_date string.
        :param language: The report language.
        :param report_name: Name of the report.
        :return:
        """
        self.database_manager.add_notification_to_queue(
            member_code, subsystem_code, member_class, x_road_instance, start_date, end_date, language,
            self.notification_username, report_name, email_info)

    def get_items_from_queue(self):
        """
        Gets all the notifications (documents) from the queue that haven't been processed yet.
        :return: Returns a list of notifications (documents) from the queue that haven't been processed yet.
        """
        not_processed_notifications = self.database_manager.get_not_processed_notifications(self.notification_username)
        return not_processed_notifications

    def send_mail(self, receiver_email, receiver_name, start_date, end_date, report_name, x_road_instance, member_class,
                  member_code, subsystem_code):
        """
        Send e-mail based on the given input parameters.
        :param receiver_email: The receiver e-mail.
        :param receiver_name: Receiver name string.
        :param start_date: The start_date string.
        :param end_date: The end_date string.
        :param report_name: Name of the report.
        :return:
        """
        # member_path_split = subsystem_path.split("/")
        # member_path = '/'.join(member_path_split[:len(member_path_split) - 1])
        msg = MIMEText(
            self.message.format(EMAIL_NAME=receiver_name, MEMBER_CODE=member_code, SUBSYSTEM_CODE=subsystem_code,
                                X_ROAD_INSTANCE=x_road_instance, START_DATE=start_date, END_DATE=end_date,
                                MEMBER_CLASS=member_class, REPORT_NAME=report_name))
        msg['Subject'] = self.subject.format(
            X_ROAD_INSTANCE=x_road_instance, MEMBER_CLASS=member_class, MEMBER_CODE=member_code,
            SUBSYSTEM_CODE=subsystem_code, START_DATE=start_date, END_DATE=end_date)
        msg['From'] = self.sender_email
        msg['To'] = formataddr((str(Header(u'{0}'.format(receiver_name), 'utf-8')), receiver_email))
        msg['Message-ID'] = make_msgid(domain=self.smtp_host)
        msg['Date'] = formatdate(localtime=True)
        s = smtplib.SMTP(host=self.smtp_host, port=self.smtp_port)
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
