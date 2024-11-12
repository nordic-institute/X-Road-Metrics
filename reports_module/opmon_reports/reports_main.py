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

import json
import time
import os
import traceback

from .notification_manager import NotificationManager
from .database_manager import DatabaseManager
from .logger_manager import LoggerManager
from .report_manager import ReportManager
from .translator import Translator
from .reports_arguments import OpmonReportsArguments
from .xroad_descriptor import OpmonXroadDescriptor
from . import __version__


def create_translator(args, logger_m):
    logger_m.log_info('create_translator', 'Prepare translations.')
    lang_path = os.path.join(
        args.settings['reports']['translation-path'],
        f'{args.language}_lang.json'
    )
    with open(lang_path, 'rb') as language_file:
        language_template = json.loads(language_file.read().decode("utf-8"))
    return Translator(language_template)


def log_report_error(e, subsystem_index, subsystem_count, logger_m, target):
    logger_m.log_error(
        'failed_report_generation',
        f'Exception: {repr(e)} {traceback.format_exc()}'.replace("\n", "")
    )

    subsystem_string = f"{target.xroad_instance}:{target.member_class}:{target.member_code}:{target.subsystem_code}"
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
    database_m = DatabaseManager(args, logger_m)
    notification_m = NotificationManager(args.settings['reports']['email'], database_m, logger_m)
    xroad_descriptor = OpmonXroadDescriptor(args, database_m, logger_m)
    translator = create_translator(args, logger_m)
    fail_count = 0

    for index, target_subsystem in enumerate(xroad_descriptor, start=1):
        try:
            report_manager = ReportManager(args, target_subsystem, logger_m, database_m, translator)
            report_name = report_manager.generate_report()
            emails = target_subsystem.get_emails()
            if emails:
                notification_m.add_item_to_queue(target_subsystem, report_name, emails)
        except Exception as e:
            fail_count += 1
            log_report_error(e, index, len(xroad_descriptor), logger_m, target_subsystem)

    log_report_generation_finish(len(xroad_descriptor), fail_count, logger_m)


def report_main(args: OpmonReportsArguments):
    logger_m = LoggerManager(args.settings['logger'], args.xroad_instance, __version__)

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
