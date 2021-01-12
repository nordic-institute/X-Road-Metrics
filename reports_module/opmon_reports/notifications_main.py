import time
import traceback

from .database_manager import DatabaseManager
from .logger_manager import LoggerManager
from .notification_manager import NotificationManager
from .reports_arguments import OpmonReportsArguments


def send_notifications(notification_manager, logger_m):
    """
    Get all the unsent notifications from the queue and send them.
    :param notification_manager: The NotificationManager object.
    :param logger_m: The LoggerManager object.
    :return:
    """
    # Start e-mail sending
    logger_m.log_info('sending_notifications', 'Sending notifications')

    notifications_list = notification_manager.get_items_from_queue()

    emails_sent = 0
    emails_not_sent = 0
    for notification in notifications_list:

        list_of_receivers = notification['email_info']

        for receiver in list_of_receivers:
            try:
                notification_manager.send_mail(notification, receiver)
                notification_manager.mark_as_sent(notification['_id'])
                emails_sent += 1
            except Exception as ex:
                emails_not_sent += 1
                log_notification_error(ex, receiver, logger_m, notification)

    log_notification_finish(emails_sent, emails_not_sent, logger_m)


def notify_main(args: OpmonReportsArguments):
    """
    The main method.
    :param args: OpmonReportsArguments object with command line arguments and settings file data
    :return:
    """
    logger_m = LoggerManager(args.settings['logger'], args.xroad_instance)
    try:
        logger_m.log_info('send_notifications', 'starting to send notifications')
        start_processing_time = time.time()

        database_m = DatabaseManager(args, logger_m)
        notification_m = NotificationManager(args.settings['reports']['email'], database_m, logger_m)

        send_notifications(notification_m, logger_m)
        end_processing_time = time.time()
        total_time = time.strftime("%H:%M:%S", time.gmtime(end_processing_time - start_processing_time))
        logger_m.log_info('send_notifications', f'Done sending notifications. Time elapsed: {total_time}')

    except Exception as e:
        logger_m.log_error('running_notifications', f'{repr(e)}')
        logger_m.log_heartbeat("error", "FAILED")
        raise e


def log_notification_error(e, receiver, logger_m, notification):
    logger_m.log_error(
        'failed_sending_email',
        f'Exception: {repr(e)} {traceback.format_exc()}'.replace("\n", "")
    )

    subsystem_string = f"{notification['x_road_instance']}:" \
                       + f"{notification['member_class']}:" \
                       + f"{notification['member_code']}:" \
                       + f"{notification['subsystem_code']}"

    logger_m.log_error(
        'failed_report_generation',
        f'Failed sending email to {receiver} on report for subsystem {subsystem_string}'
    )
    logger_m.log_heartbeat(f"Error: {e}", "FAILED")


def log_notification_finish(success_count, fail_count, logger_m):
    total_count = success_count + fail_count
    log_msg = f'{success_count}/{total_count} emails sent successfully. Failed to send {fail_count} emails.'
    logger_m.log_info('finished_sending_email', log_msg)
    logger_m.log_heartbeat(log_msg, "SUCCEEDED" if fail_count == 0 else "FAILED")

