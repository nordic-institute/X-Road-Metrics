import json
import time

from .database_manager import DatabaseManager
from .logger_manager import LoggerManager
from .mongodb_handler import MongoDBHandler
from .report_manager import ReportManager
from .translator import Translator
from .reports_arguments import OpmonReportsArguments


def read_in_json(file_name, logger_manager):
    """
    Reads in the given .json file.
    :param logger_manager: The LoggerManager object.
    :param file_name: Path to the .json file.
    :return: Returns the data that is in the file.
    """
    data = None
    try:
        with open(file_name, 'r') as f:
            json_data = f.read()
        data = json.loads(json_data)
    except FileNotFoundError:
        logger_manager.log_warning("reading_in_json", "The riha.json does not exist, will run without it.")

    return data


def main(logger_manager):
    """
    The main method.
    :param logger_manager: The LoggerManager object.
    :return:
    """
    # Start timer
    start_processing_time = time.time()

    args = OpmonReportsArguments()
    settings = args.settings

    # Initialize handlers
    mdb_suffix = settings.MONGODB_SUFFIX
    mdb_user = settings.MONGODB_USER
    mdb_pwd = settings.MONGODB_PWD
    mdb_server = settings.MONGODB_SERVER
    db_handler = MongoDBHandler(mdb_suffix, mdb_user, mdb_pwd, mdb_server)
    db_m = DatabaseManager(db_handler, logger_manager)

    # Initialize translator
    with open(settings.TRANSLATION_FILES.format(LANGUAGE=language), 'rb') as language_file:
        language_template = json.loads(language_file.read().decode("utf-8"))
    translator = Translator(language_template)

    # Initialize variables
    riha_json = read_in_json(settings.SUBSYSTEM_INFO_PATH, logger_manager)
    meta_services = settings.META_SERVICE_LIST
    html_template = settings.HTML_TEMPLATE_PATH
    css_files = settings.CSS_FILES
    report_path = settings.REPORTS_PATH
    ria_image_1 = settings.RIA_IMAGE_1.format(LANGUAGE=language)
    ria_image_2 = settings.RIA_IMAGE_2.format(LANGUAGE=language)
    ria_image_3 = settings.RIA_IMAGE_3.format(LANGUAGE=language)

    # Generate a report manager
    report_manager = ReportManager(args,
                                   riha_json, logger_manager, db_m, meta_services, translator, html_template,
                                   report_path, css_files, ria_image_1, ria_image_2, ria_image_3)

    # Log starting
    logger_manager.log_info('report_worker', 'report_worker_start')
    # No need to heartbeat here, it might confuse application monitoring
    # logger_manager.log_heartbeat(
    #     "report_worker start", settings.HEARTBEAT_LOGGER_PATH, settings.REPORT_HEARTBEAT_NAME, "SUCCEEDED")

    # Generate report
    report_manager.generate_report()

    # Log ending of the reports generation
    end_processing_time = time.time()
    total_time = time.strftime("%H:%M:%S", time.gmtime(end_processing_time - start_processing_time))
    logger_manager.log_info('report_worker', 'report_worker_end')
    logger_manager.log_info('report_worker', 'Total generation time: {0}'.format(total_time))

    # No need to heartbeat here, it might confuse application monitoring
    # logger_manager.log_heartbeat(
    #     "report_worker end", settings.HEARTBEAT_LOGGER_PATH, settings.REPORT_HEARTBEAT_NAME, "SUCCEEDED")


if __name__ == '__main__':
    logger_m = LoggerManager(settings.LOGGER_NAME, 'report_worker')
    try:
        main(logger_m)
    except Exception as e:
        logger_m.log_error('reports', '{0}'.format(repr(e)))
        logger_m.log_heartbeat("error", settings.HEARTBEAT_LOGGER_PATH, settings.REPORT_HEARTBEAT_NAME, "FAILED")
        raise e
