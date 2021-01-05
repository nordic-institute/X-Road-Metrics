import json
import time

from .database_manager import DatabaseManager
from .logger_manager import LoggerManager
from .mongodb_handler import MongoDBHandler
from .report_manager import ReportManager
from .translator import Translator
from .reports_arguments import OpmonReportsArguments
from . import constants


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


def create_report_manager(args, logger_m):
    settings = args.settings

    db_handler = MongoDBHandler(settings['mongodb'], args.xroad_instance)
    db_m = DatabaseManager(db_handler, logger_m)

    # Initialize translator
    with open(settings.TRANSLATION_FILES.format(LANGUAGE=args.language), 'rb') as language_file:
        language_template = json.loads(language_file.read().decode("utf-8"))
    translator = Translator(language_template)

    # Initialize variables
    riha_json = read_in_json(settings.SUBSYSTEM_INFO_PATH, logger_m)

    # Generate a report manager
    return ReportManager(args, riha_json, logger_m, db_m, translator)


def main():
    args = OpmonReportsArguments()
    logger_m = LoggerManager(args.settings['logger'], args.xroad_instance)

    try:
        start_processing_time = time.time()

        report_manager = create_report_manager(args, logger_m)
        logger_m.log_info('report_worker', 'report_worker_start')

        report_manager.generate_report()

        end_processing_time = time.time()
        total_time = time.strftime("%H:%M:%S", time.gmtime(end_processing_time - start_processing_time))
        logger_m.log_info('report_worker', 'report_worker_end')
        logger_m.log_info('report_worker', 'Total generation time: {0}'.format(total_time))
    except Exception as e:
        logger_m.log_error('reports', f'{repr(e)}')
        logger_m.log_heartbeat("error", "FAILED")
        raise e


if __name__ == '__main__':
    main()
