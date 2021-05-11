from .anonymizer import Anonymizer
from .iio.mongodbmanager import MongoDbManager
from .iio.opendata_writer import OpenDataWriter
from datetime import datetime
import argparse
import traceback
from .settings_parser import OpmonSettingsManager
from opmon_anonymizer.utils import logger_manager


def main():
    args = parse_args()
    settings = OpmonSettingsManager(args.profile).settings
    logger = logger_manager.LoggerManager(settings['logger'], settings['xroad']['instance'])

    try:
        start_time = datetime.now()
        record_count = run_anonymizer(settings, logger, args.limit)
        elapsed = str(datetime.now() - start_time)
        logger.log_info('anonymization_session_finished',
                        f"Anonymization finished in {elapsed} seconds. Processed {record_count} entries from MongoDB.")
    except Exception:
        raise


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--profile",
        metavar="PROFILE",
        default=None,
        help="""
            Optional settings file profile.
            For example with '--profile PROD' settings_PROD.yaml will be used as settings file.
            If no profile is defined, settings.yaml will be used by default.
            Settings file is searched from current working directory and /etc/xroad-metrics/anonymizer/
        """
    )

    parser.add_argument(
        "--limit",
        default=None,
        help="""
            Maximum number of records to anonymize during this run. If this argument is not provided all records
            available in MongoDb are processed.
        """
    )

    args = parser.parse_args()
    return args


def setup_reader(settings, logger):
    try:
        reader = MongoDbManager(settings, logger)
        assert reader.is_alive()
        return reader
    except Exception:
        logger.log_heartbeat('Failed to initialize MongoDB connection.', 'FAILED')
        logger.log_error('mongodb_connection_failed',
                         f"Failed connecting to MongoDB at {settings['mongodb']}")

        raise


def setup_writer(settings, logger):
    try:
        writer = OpenDataWriter(settings, logger)
        assert writer.db_manager.is_alive()
        return writer
    except Exception:
        logger.log_heartbeat('Failed to initialize PostgreSQL connection.', 'FAILED')

        trace = traceback.format_exc().replace('\n', '')
        logger.log_error('postgresql_connection_failed',
                         f'Failed initializing postgresql database connector. ERROR: {trace}')
        raise


def run_anonymizer(settings, logger, anonymization_limit):
    logger.log_info('anonymization_session_started', 'Started anonymization session')
    logger.log_heartbeat('Started anonymization session', 'SUCCEEDED')

    reader = setup_reader(settings, logger)
    writer = setup_writer(settings, logger)

    try:
        logger.log_info('anonymization_process_started', 'Started anonymizing logs.')
        logger.log_heartbeat('Started anonymizing logs.', 'SUCCEEDED')
        anonymizer_instance = Anonymizer(reader, writer, settings, logger)
        records = anonymizer_instance.anonymize(anonymization_limit)

    except Exception:
        trace = traceback.format_exc().replace('\n', '')
        logger.log_error('anonymization_process_failed', f'Failed to anonymize. ERROR: {trace}')
        save_reader_state_on_error(reader, logger)
        logger.log_heartbeat('Error occurred during log anonymization', 'FAILED')
        raise

    logger.log_heartbeat('Finished anonymization session', 'SUCCEEDED')
    return records


def save_reader_state_on_error(reader: MongoDbManager, logger):
    try:
        reader.set_last_processed_timestamp()
        logger.log_info('anonymization_process_failed', 'Reader state saved successfully after error.')
    except Exception:
        logger.log_warn('anonymization_process_failed', 'Failed to save reader state after error.')


if __name__ == "__main__":
    main()
