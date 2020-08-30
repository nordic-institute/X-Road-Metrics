import anonymizer.anonymizer as anonymizer
from anonymizer.anonymizer import Anonymizer
from anonymizer.iio.mongodb_manager import MongoDB_Manager
from anonymizer.iio.opendata_writer import OpenDataWriter
from datetime import datetime
from anonymizer.anonymizer_config import AnonymizerConfig
import os
from sys import argv
import traceback

from anonymizer.utils import logger_manager
import anonymizer.settings as settings

if len(argv) > 1:
    anonymization_limit = int(argv[1])
else:
    anonymization_limit = 0

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

logger_manager.setup_logger(logger_name='opendata-anonymizer', log_level=settings.log['level'],
                            log_path=settings.log['path'], max_file_size=settings.log['max_file_size'],
                            backup_count=settings.log['backup_count'])

logger = logger_manager.LoggerManager(logger_name='opendata-anonymizer', module_name='opendata', heartbeat_dir=settings.heartbeat['dir'])

start_time = datetime.now()

logger.log_info('anonymization_session_started', 'Started anonymization session')
logger.log_heartbeat('Started anonymization session', 'opendata-anonymizer', 'SUCCEEDED')

opendata_config_path = os.path.join(ROOT_DIR, 'settings.py')

try:
    try:
        config = AnonymizerConfig(opendata_config_path)
    except Exception:
        logger.log_heartbeat('Failed reading settings.py', 'opendata-anonymizer', 'FAILED')
        raise

    try:
        reader = MongoDB_Manager(config)
        is_mongodb_alive = reader.is_alive()
    except Exception:
        logger.log_heartbeat('Failed to initialize MongoDB connection.', 'opendata-anonymizer', 'FAILED')
        try:
            logger.log_error('mongodb_connection_failed',
                             'Failed to connect to MongoDB with connection string {0}'.format(
                                 reader.mongo_connection_string
                             ))
        except:
            logger.log_error('mongodb_connection_failed',
                             'Missing mongodb connection parameters in {0}'.format(
                                 os.path.abspath(opendata_config_path)
                             ))
            raise

        raise

    try:
        writer = OpenDataWriter(config)
        is_postgres_alive = writer._db_manager.is_alive()
    except Exception:
        logger.log_heartbeat('Failed to initialize PostgreSQL connection.', 'opendata-anonymizer', 'FAILED')
        logger.log_error('postgresql_connection_failed',
                         'Failed initializing postgresql database connector. ERROR: {0}'.format(
                             traceback.format_exc().replace('\n', '')
                         ))
        raise

    try:
        logger.log_info('anonymization_process_started', 'Started anonymizing logs.')
        logger.log_heartbeat('Started anonymizing logs.', 'opendata-anonymizer', 'SUCCEEDED')
        anonymizer_instance = Anonymizer(reader, writer, config, logger_manager=logger)
        if anonymization_limit:
            records = anonymizer_instance.anonymize_with_limit(anonymization_limit)
        else:
            records = anonymizer_instance.anonymize()
    except:
        logger.log_error('anonymization_process_failed',
                         'Failed to anonymize. ERROR: {0}'.format(
                             traceback.format_exc().replace('\n', '')
                         ))
        logger.log_heartbeat('Error occurred during log anonymization', 'opendata-anonymizer', 'FAILED')
        raise

    logger.log_heartbeat('Finished anonymization session', 'opendata-anonymizer', 'SUCCEEDED')

except:
    try:
        records
    except:
        records = 0

    logger.log_heartbeat('Anonymizaton session failed', 'opendata-anonymizer', 'FAILED')

end_time = datetime.now()
logger.log_info('anonymization_session_finished',
                "Finished anonymization session in {0}. Processed {1} entries from MongoDB".format(
                    str(end_time - start_time), records
                ))
