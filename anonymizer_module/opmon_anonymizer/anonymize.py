from .anonymizer import Anonymizer
from .iio.mongodbmanager import MongoDbManager
from .iio.opendata_writer import OpenDataWriter
from datetime import datetime
import sys
import os
from sys import argv
import traceback
from .settings_parser import OpmonSettingsManager
from opmon_anonymizer.utils import logger_manager

settings = OpmonSettingsManager().settings

if len(argv) > 1:
    anonymization_limit = int(argv[1])
else:
    anonymization_limit = None

ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

logger = logger_manager.LoggerManager(settings['logger'], settings['xroad']['instance'])

start_time = datetime.now()
records = 0

logger.log_info('anonymization_session_started', 'Started anonymization session')
logger.log_heartbeat('Started anonymization session', 'SUCCEEDED')

try:
    reader = MongoDbManager(settings)
    is_mongodb_alive = reader.is_alive()
except Exception:
    logger.log_heartbeat('Failed to initialize MongoDB connection.', 'FAILED')
    logger.log_error('mongodb_connection_failed',
                     f"Failed connecting to MongoDB at {settings['mongodb']['host']}:{settings['mongodb']['port']}")
    sys.exit(1)


try:
    writer = OpenDataWriter(settings, logger_manager)
    is_postgres_alive = writer.db_manager.is_alive()
except Exception:
    logger.log_heartbeat('Failed to initialize PostgreSQL connection.', 'FAILED')

    trace = traceback.format_exc().replace('\n', '')
    logger.log_error('postgresql_connection_failed',
                     f'Failed initializing postgresql database connector. ERROR: {trace}')
    sys.exit(1)

try:
    logger.log_info('anonymization_process_started', 'Started anonymizing logs.')
    logger.log_heartbeat('Started anonymizing logs.', 'SUCCEEDED')
    anonymizer_instance = Anonymizer(reader, writer, settings, logger)
    records = anonymizer_instance.anonymize(anonymization_limit)

except Exception:
    trace = traceback.format_exc().replace('\n', '')
    logger.log_error('anonymization_process_failed', f'Failed to anonymize. ERROR: {trace}')
    logger.log_heartbeat('Error occurred during log anonymization', 'FAILED')
    sys.exit(1)

logger.log_heartbeat('Finished anonymization session', 'SUCCEEDED')
elapsed = str(datetime.now() - start_time)
logger.log_info('anonymization_session_finished',
                f"Finished anonymization session in {elapsed} seconds. Processed {records} entries from MongoDB")
