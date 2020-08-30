import argparse
import json
import subprocess
import time
import traceback

from . import settings
from .reportslib.database_manager import DatabaseManager
from .reportslib.logger_manager import LoggerManager
from .reportslib.mongodb_handler import MongoDBHandler
from .reportslib.notification_manager import NotificationManager
from .reportslib.report_manager import ReportManager
from .reportslib.translator import Translator


def read_in_json(file_name, log_m):
    """
    Reads in the given .json file.
    :param log_m: The LoggerManager object.
    :param file_name: Path to the .json file.
    :return: Returns the data that is in the file.
    """
    data = None
    try:
        with open(file_name, 'r') as f:
            json_data = f.read()
        data = json.loads(json_data)
    except FileNotFoundError:
        log_m.log_warning("reading_in_json", "The riha.json does not exist, will run without it.")

    return data


def get_start_and_end_time(file_path):
    """
    Get start date and end date from the given bash file.
    :param file_path: The path to bash file that generates the start and end dates.
    :return: Returns the start date and the end date.
    """
    proc = subprocess.Popen(file_path, stdout=subprocess.PIPE)
    tmp = proc.stdout.read()
    dates = str(tmp).split(" ")

    return dates[0][2:], dates[1][:len(dates[1]) - 3]


def report_main(log_m):
    """
    The main method.
    :param log_m: The LoggedManager object.
    :return:
    """
    # Parse input arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--language', dest='language', help='Language ("et"/"en")', required=True)
    args = parser.parse_args()

    # Initialize variables
    language = args.language

    # Start timer
    start_processing_time = time.time()

    # Initialize handlers
    mdb_suffix = settings.MONGODB_SUFFIX
    mdb_user = settings.MONGODB_USER
    mdb_pwd = settings.MONGODB_PWD
    mdb_server = settings.MONGODB_SERVER
    db_handler = MongoDBHandler(mdb_suffix, mdb_user, mdb_pwd, mdb_server)
    db_m = DatabaseManager(db_handler, log_m)
    notification_manager = NotificationManager(db_m, log_m, settings.SENDER_EMAIL, settings.SMTP_HOST,
                                               settings.SMTP_PORT, settings.REPORT_USERNAME, settings.EMAIL_BODY,
                                               settings.EMAIL_SUBJECT)
    # Initialize translator
    with open(settings.TRANSLATION_FILES.format(LANGUAGE=language), 'rb') as language_file:
        language_template = json.loads(language_file.read().decode("utf-8"))
    translator = Translator(language_template)

    # Log starting
    # No need to heartbeat here, it might confuse application monitoring
    # log_m.log_heartbeat("start", settings.HEARTBEAT_LOGGER_PATH, settings.REPORT_HEARTBEAT_NAME, "SUCCEEDED")
    log_m.log_info('reports_start', 'Starting report.py for reports generation')

    # Gathering subsystems from riha.json
    log_m.log_info('reports_subsystems_start', 'Starting to gather subsystems from riha.json')
    # No need to heartbeat here, it might confuse application monitoring
    # log_m.log_heartbeat("in_progress", settings.HEARTBEAT_LOGGER_PATH, settings.REPORT_HEARTBEAT_NAME, "SUCCEEDED")
    member_subsystem_data = read_in_json(settings.SUBSYSTEM_INFO_PATH, log_m)
    log_m.log_info('reports_subsystems_start', 'Gathered subsystems from riha.json')
    number_of_reports = len(member_subsystem_data)
    log_m.log_info('reports_subsystems_start', str(number_of_reports) + ' subsystems found from riha.json')

    # Getting the start and end dates from file
    start_date, end_date = get_start_and_end_time(settings.REPORT_DATES_PATH)
    log_m.log_info('reports_subsystems_finish', 'Total subsystems: {0}'.format(number_of_reports))

    # Initialize variables
    meta_services = settings.META_SERVICE_LIST
    html_template = settings.HTML_TEMPLATE_PATH
    css_files = settings.CSS_FILES
    report_path = settings.REPORTS_PATH
    ria_image_1 = settings.RIA_IMAGE_1.format(LANGUAGE=language)
    ria_image_2 = settings.RIA_IMAGE_2.format(LANGUAGE=language)
    ria_image_3 = settings.RIA_IMAGE_3.format(LANGUAGE=language)
    current_report = 0
    failed_report = 0

    # Generate reports
    log_m.log_info('reports_generation_start', 'Starting reports generation')
    for subsystem in member_subsystem_data:

        # Initialize variables
        current_report += 1
        x_road_instance = str(subsystem['x_road_instance'])
        member_class = str(subsystem['member_class'])
        member_code = str(subsystem['member_code'])
        subsystem_code = str(subsystem['subsystem_code'])
        e_mail_info = subsystem['email']

        log_m.log_info(
            'reports_generation_in_progress',
            "Generating report " + str(current_report) + "/" + str(number_of_reports) + " [" + x_road_instance + " / " +
            member_class + " / " + member_code + " / " + subsystem_code + " / " + start_date + " - " +
            end_date + "]")

        try:
            # Initialize Report Manager
            report_manager = ReportManager(
                x_road_instance, member_class, member_code, subsystem_code, start_date, end_date, member_subsystem_data,
                log_m, db_m, language, meta_services, translator, html_template, report_path, css_files, ria_image_1,
                ria_image_2, ria_image_3)
            # Generate report
            report_name = report_manager.generate_report()

            # Add e-mail notification(s) into the queue
            notification_manager.add_item_to_queue(member_code, subsystem_code, member_class, x_road_instance,
                                                   start_date, end_date, language, report_name, e_mail_info)

            # No need to heartbeat here, it might confuse application monitoring
            # log_m.log_heartbeat(
            #     "Generated report " + str(current_report) + "/" + str(number_of_reports) + "[" + x_road_instance + " / " +
            #     member_class + " / " + member_code + " / " + subsystem_code + " / " + start_date + " - " +
            #     end_date + "]", settings.HEARTBEAT_LOGGER_PATH, settings.REPORT_HEARTBEAT_NAME, "SUCCEEDED")

        except Exception as ex:
            failed_report += 1
            log_m.log_error('failed_report_generation',
                            "Exception: {0} {1}".format(repr(ex), traceback.format_exc()).replace("\n", ""))
            log_m.log_error(
                'failed_report_generation',
                "Failed generating report: " + str(current_report) + "/" + str(number_of_reports) + "[" + x_road_instance +
                " / " + member_class + " / " + member_code + " / " + subsystem_code + " / " + start_date + " - " +
                end_date + "]")
            # Keep heartbeat here to understand failure of report generation in application monitoring
            log_m.log_heartbeat(
                "Failed generating report " + str(current_report) + "/" + str(number_of_reports) + "[" + x_road_instance +
                " / " + member_class + " / " + member_code + " / " + subsystem_code + " / " + start_date + " - " +
                end_date + "] Error: {0}".format(ex), settings.HEARTBEAT_LOGGER_PATH, settings.REPORT_HEARTBEAT_NAME,
                "FAILED")

    # Log ending of the reports generation
    end_processing_time = time.time()
    total_time = time.strftime("%H:%M:%S", time.gmtime(end_processing_time - start_processing_time))
    log_m.log_info('reports_generation_finish',
                   'Generated {0} reports, failed {1} reports'.format(str(current_report), failed_report))
    log_m.log_info('reports_generation_time', 'Total generation time: {0}'.format(total_time))

    log_m.log_info('reports_generation_done', 'Finished reports generation')
    log_m.log_heartbeat(
        "Generated {0} reports, failed {1} reports".format(str(current_report), failed_report),
        settings.HEARTBEAT_LOGGER_PATH, settings.REPORT_HEARTBEAT_NAME, "SUCCEEDED" if failed_report == 0 else "FAILED")


if __name__ == '__main__':
    logger_m = LoggerManager(settings.LOGGER_NAME, 'reports_module')
    try:
        report_main(logger_m)
    except Exception as e:
        logger_m.log_error('running_report_main', '{0}'.format(repr(e)))
        logger_m.log_heartbeat("error", settings.HEARTBEAT_LOGGER_PATH, settings.REPORT_HEARTBEAT_NAME, "FAILED")
        raise e
