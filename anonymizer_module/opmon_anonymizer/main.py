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

import argparse
from datetime import datetime
from typing import Optional, Union

from opmon_anonymizer import __version__
from opmon_anonymizer.anonymizer import Anonymizer
from opmon_anonymizer.iio.mongodbmanager import (MongoDbManager,
                                                 MongoDbOpenDataManager)
from opmon_anonymizer.iio.opendata_writer import OpenDataWriter
from opmon_anonymizer.opendata_anonymizer import OpenDataAnonymizer
from opmon_anonymizer.settings_parser import OpmonSettingsManager
from opmon_anonymizer.utils import logger_manager


def anonymize(settings: dict, logger: logger_manager.LoggerManager,
              limit: int, only_opendata: bool = False) -> None:

    opendata = 'opendata_' if only_opendata else ''

    try:
        start_time = datetime.now()
        record_count = run_opendata_anonymizer(settings, logger, limit) if only_opendata else run_anonymizer(settings, logger, limit)
        elapsed = str(datetime.now() - start_time)
        logger.log_info(f'{opendata}anonymization_session_finished',
                        f'Anonymization finished in {elapsed} seconds. Processed {record_count} entries from MongoDB.')
    except Exception as e:
        logger.log_exception(f'{opendata}anonymization_process_failed',
                             f'Failed to anonymize. ERROR: {str(e)}')
        raise


def main():
    args = parse_args()
    settings = OpmonSettingsManager(args.profile).settings
    logger = logger_manager.LoggerManager(settings['logger'], settings['xroad']['instance'], __version__)

    if args.only_opendata:
        anonymize(settings, logger, args.limit, only_opendata=True)
    else:
        anonymize(settings, logger, args.limit)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--profile',
        metavar='PROFILE',
        default=None,
        help="""
            Optional settings file profile.
            For example with '--profile PROD' settings_PROD.yaml will be used as settings file.
            If no profile is defined, settings.yaml will be used by default.
            Settings file is searched from current working directory and /etc/xroad-metrics/anonymizer/
        """
    )

    parser.add_argument(
        '--limit',
        default=None,
        help="""
            Maximum number of records to anonymize during this run. If this argument is not provided all records
            available in MongoDb are processed.
        """
    )
    parser.add_argument('--only_opendata', action='store_true', help='Should Anonymizer process only OpenData')

    args = parser.parse_args()
    return args


def setup_opendata_reader(settings: dict, logger: logger_manager.LoggerManager) -> MongoDbOpenDataManager:
    try:
        reader = MongoDbOpenDataManager(settings, logger)
        assert reader.is_alive()
        return reader
    except Exception as e:
        logger.log_heartbeat('Failed to initialize MongoDB connection.', 'FAILED')
        logger.log_exception('mongodb_connection_failed',
                             f"Failed connecting to MongoDB at {settings['mongodb']}"
                             f'ERROR: {str(e)}')

        raise


def setup_reader(settings, logger):
    try:
        reader = MongoDbManager(settings, logger)
        assert reader.is_alive()
        return reader
    except Exception as e:
        logger.log_heartbeat('Failed to initialize MongoDB connection.', 'FAILED')
        logger.log_exception('mongodb_connection_failed',
                             f"Failed connecting to MongoDB at {settings['mongodb']}"
                             f'ERROR: {str(e)}')

        raise


def setup_writer(settings, logger):
    try:
        writer = OpenDataWriter(settings, logger)
        assert writer.db_manager.is_alive()
        return writer
    except Exception as e:
        logger.log_heartbeat('Failed to initialize PostgreSQL connection.', 'FAILED')
        logger.log_exception('postgresql_connection_failed',
                             f'Failed initializing postgresql database connector. ERROR: {str(e)}')
        raise


def run_anonymizer(settings, logger: logger_manager.LoggerManager, anonymization_limit):
    logger.log_info('anonymization_session_started', 'Started anonymization session')
    logger.log_heartbeat('Started anonymization session', 'SUCCEEDED')

    reader = setup_reader(settings, logger)
    writer = setup_writer(settings, logger)

    try:
        logger.log_info('anonymization_process_started', 'Started anonymizing logs.')
        logger.log_heartbeat('Started anonymizing logs.', 'SUCCEEDED')
        anonymizer_instance = Anonymizer(reader, writer, settings, logger)
        records = anonymizer_instance.anonymize(anonymization_limit)
        logger.log_heartbeat('Finished anonymization session', 'SUCCEEDED')
        return records

    except Exception as e:
        logger.log_exception('anonymization_process_failed', f'Failed to anonymize. ERROR: {str(e)}')
        save_reader_state_on_error(reader, logger)
        logger.log_heartbeat('Error occurred during log anonymization', 'FAILED')


def run_opendata_anonymizer(settings: dict, logger: logger_manager.LoggerManager, anonymization_limit: int) -> Optional[int]:
    logger.log_info('opendata_anonymization_session_started', 'Started anonymization session')
    logger.log_heartbeat('Started opendata anonymization session', 'SUCCEEDED')

    reader = setup_opendata_reader(settings, logger)
    writer = setup_writer(settings, logger)
    try:
        logger.log_info('opendata_anonymization_process_started', 'Started anonymizing opendata logs.')
        logger.log_heartbeat('Started anonymizing opendata logs.', 'SUCCEEDED')
        anonymizer_instance = OpenDataAnonymizer(reader, writer, settings, logger)
        records = anonymizer_instance.anonymize(anonymization_limit)
        logger.log_heartbeat('Finished opendata anonymization session', 'SUCCEEDED')
        return records

    except Exception as e:
        logger.log_exception('opendata_anonymization_process_failed', f'Failed to anonymize. ERROR: {str(e)}')
        save_reader_state_on_error(reader, logger)
        logger.log_heartbeat('Error occurred during opendata log anonymization', 'FAILED')
        return None


def save_reader_state_on_error(reader: Union[MongoDbManager, MongoDbOpenDataManager], logger):
    try:
        reader.set_last_processed_timestamp()
        logger.log_info('anonymization_process_failed', 'Reader state saved successfully after error.')
    except Exception as e:
        logger.log_exception('anonymization_process_failed',
                             f'Failed to save reader state after error. ERROR: {str(e)}')


if __name__ == '__main__':
    main()
