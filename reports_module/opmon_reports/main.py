import json
import time
import os
import traceback

from opmon_reports.notification_manager import NotificationManager
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


def create_database_manager(args, logger_m):
    logger_m.log_info('create_database_manager', 'Prepare database manager.')
    return DatabaseManager(
        MongoDBHandler(args.settings['mongodb'], args.xroad_instance),
        logger_m
    )


def create_translator(args, logger_m):
    logger_m.log_info('create_translator', 'Prepare translations.')
    lang_path = os.path.join(
        args.settings['reports']['translation-path'],
        f'{args.language}_lang.json'
    )
    with open(lang_path, 'rb') as language_file:
        language_template = json.loads(language_file.read().decode("utf-8"))
    return Translator(language_template)


def create_notification_manager(args, database_m, logger_m):
    logger_m.log_info('create_notification_manager', 'Prepare notification manager.')
    return NotificationManager(database_m, logger_m, args.settings['reports']['email'])


def parse_riha_json(args, logger_m):
    logger_m.log_info('parse_riha_json', 'Gather subsystems from riha.json.')
    return read_in_json(args.settings['reports']['subsystem-info-path'], logger_m)


def create_report_manager(args, riha_json, logger_m, database_m, translator):
    logger_m.log_info('create_reports_manager', f'Prepare reports manager for subsystem "{args.subsystem_code}"')
    return ReportManager(args, riha_json, logger_m, database_m, translator)


def log_report_error(e, subsystem_index, subsystem_count, logger_m, args):
    logger_m.log_error(
        'failed_report_generation',
        f'Exception: {repr(e)} {traceback.format_exc()}'.replace("\n", "")
    )

    subsystem_string = f"{args.xroad_instance}:{args.member_class}:{args.member_code}:{args.subsystem_code}"
    logger_m.log_error(
        'failed_report_generation',
        f'Failed generating report {subsystem_index}/{subsystem_count} for subsystem {subsystem_string}'
    )
    logger_m.log_heartbeat(f"Error: {e}", "FAILED")


def log_report_generation_finish(subsystem_count, fail_count, logger_m):
    success_count = subsystem_count - fail_count
    log_msg = f'{success_count}/{subsystem_count} reports generated successfully. failed {fail_count} reports'
    logger_m.log_info('reports_generation_finish', log_msg)
    logger_m.log_heartbeat(log_msg, "SUCCEEDED" if fail_count == 0 else "FAILED")


def generate_reports(args, logger_m):
    database_m = create_database_manager(args, logger_m)
    # notification_m = create_notification_manager(args, database_m, logger_m)
    riha_json = parse_riha_json(args, logger_m)
    translator = create_translator(args, logger_m)

    # If no subsystem was defined as command line argument create a report for all subsystems in riha.json
    subsystems = riha_json if args.subsystem is None else [args.subsystem]
    fail_count = 0

    for index, subsystem in enumerate(subsystems, start=1):
        try:
            args.subsystem = subsystem
            report_manager = create_report_manager(args, riha_json, logger_m, database_m, translator)
            report_name = report_manager.generate_report()
            # if subsystem.get('email'):
            #    notification_m.add_item_to_queue(args, report_name, subsystem['email']
        except Exception as e:
            fail_count += 1
            log_report_error(e, index, len(subsystems), logger_m, args)

    log_report_generation_finish(len(subsystems), fail_count, logger_m)


def main():
    args = OpmonReportsArguments()
    logger_m = LoggerManager(args.settings['logger'], args.xroad_instance)

    try:
        start_processing_time = time.time()
        logger_m.log_info('reports_start', 'Starting reports generation')

        generate_reports(args, logger_m)

        end_processing_time = time.time()
        total_time = time.strftime("%H:%M:%S", time.gmtime(end_processing_time - start_processing_time))
        logger_m.log_info('report_worker', 'report_worker_end')
        logger_m.log_info('report_worker', f'Total generation time: {total_time}')

    except Exception as e:
        logger_m.log_error('reports', f'{repr(e)}')
        logger_m.log_heartbeat("error", "FAILED")
        raise e


if __name__ == '__main__':
    main()
