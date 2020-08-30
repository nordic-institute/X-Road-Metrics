import time
import traceback

from reports_module import settings
from reports_module.reportslib.database_manager import DatabaseManager
from reports_module.reportslib.logger_manager import LoggerManager
from reports_module.reportslib.mongodb_handler import MongoDBHandler
from reports_module.reportslib.notification_manager import NotificationManager


def send_notifications(notification_manager, logger_manager):
    """
    Get all the unsent notifications from the queue and send them.
    :param notification_manager: The NotificationManager object.
    :param logger_manager: The LoggerManager object.
    :return:
    """
    # Start e-mail sending
    start_processing_time = time.time()
    logger_manager.log_info('sending_notifications', 'Sending notifications')
    # No need to heartbeat here, it might confuse application monitoring
    # logger_m.log_heartbeat("Sending notifications", settings.HEARTBEAT_LOGGER_PATH, settings.REPORT_HEARTBEAT_NAME,
    #                        "SUCCEEDED")

    # Get the list of emails to be sent
    notifications_list = notification_manager.get_items_from_queue()

    emails_sent = 0
    emails_not_sent = 0
    for notification in notifications_list:

        report_path_subsystem = "{0}/{1}/{2}/{3}".format(notification['x_road_instance'], notification['member_class'],
                                                         notification['member_code'], notification['subsystem_code'])

        report_name = notification['report_name']
        list_of_receivers = notification['email_info']
        start_date = notification['start_date']
        end_date = notification['end_date']
        x_road_instance = notification['x_road_instance']
        member_class = notification['member_class']
        member_code = notification['member_code']
        subsystem_code = notification['subsystem_code']

        for email in list_of_receivers:
            receiver_email = email['email']
            receiver_name = email['name']
            try:
                notification_manager.send_mail(receiver_email, receiver_name, start_date, end_date,
                                               report_name, x_road_instance, member_class, member_code, subsystem_code)
                notification_manager.mark_as_sent(notification['_id'])
                emails_sent += 1
            except Exception as ex:
                notification_manager.mark_as_sent_error(notification['_id'], "not_sent_error: {0}".format(repr(ex)))
                emails_not_sent += 1
                logger_manager.log_error(
                    'failed_sending_email',
                    "Exception: {0} {1}".format(repr(ex), traceback.format_exc()).replace("\n", "")
                )
                logger_manager.log_error(
                    'failed_sending_email',
                    "Failed sending email: " + str(receiver_email) + "/" + str(receiver_name) + "/" +
                    str(report_name) + "/" + str(report_path_subsystem) + "/" + notification[
                        'x_road_instance'] + "/" + notification['member_class'] + "/" +
                    notification['member_code'] + "/" + notification['subsystem_code']
                )
                logger_manager.log_heartbeat(
                    "Failed sending email: " + str(receiver_email) + "/" + str(receiver_name) + "/" +
                    str(report_name) + "/" + str(report_path_subsystem) + "/" + notification[
                        'x_road_instance'] + "/" + notification['member_class'] + "/" +
                    notification['member_code'] + "/" + notification['subsystem_code'], settings.HEARTBEAT_LOGGER_PATH,
                    settings.REPORT_HEARTBEAT_NAME, "FAILED")

    end_processing_time = time.time()
    total_time = time.strftime("%H:%M:%S", time.gmtime(end_processing_time - start_processing_time))
    logger_m.log_info('notification_sending_finished',
                      'Sent {0} e-mails, didn''t send {1} e-mails'.format(emails_sent, emails_not_sent))
    logger_m.log_info('notification_sending_time', 'Total sending time: {0}'.format(total_time))
    logger_manager.log_info('finish_sending_notifications', 'Finished sending notifications')
    logger_m.log_heartbeat("Finished sending notifications", settings.HEARTBEAT_LOGGER_PATH,
                           settings.REPORT_HEARTBEAT_NAME, "SUCCEEDED" if emails_not_sent == 0 else "FAILED")


def main(logger_manager):
    """
    The main method.
    :param logger_manager: The LoggerManager object.
    :return:
    """
    logger_manager.log_info('send_notifications', 'starting to send notifications')

    # Initialize managers
    mdb_suffix = settings.MONGODB_SUFFIX
    mdb_user = settings.MONGODB_USER
    mdb_pwd = settings.MONGODB_PWD
    mdb_server = settings.MONGODB_SERVER
    db_handler = MongoDBHandler(mdb_suffix, mdb_user, mdb_pwd, mdb_server)
    db_m = DatabaseManager(db_handler, logger_manager)
    notification_manager = NotificationManager(
        db_m, logger_manager, settings.SENDER_EMAIL, settings.SMTP_HOST, settings.SMTP_PORT, settings.REPORT_USERNAME,
        settings.EMAIL_BODY, settings.EMAIL_SUBJECT)

    # Send notifications
    send_notifications(notification_manager, logger_manager)


if __name__ == '__main__':
    logger_m = LoggerManager(settings.LOGGER_NAME, 'reports_module')
    try:
        main(logger_m)
    except Exception as e:
        logger_m.log_error('running_notifications', '{0}'.format(repr(e)))
        logger_m.log_heartbeat("error", settings.HEARTBEAT_LOGGER_PATH, settings.REPORT_HEARTBEAT_NAME, "FAILED")
        raise e
