import logging
import os
import traceback
from anonymizer.utils import logger_manager


class AnonymizerConfig(object):
    """Instantiated version of the opendata's global configuration file ready for pickling.
    """

    def __init__(self, opendata_config_module_path):
        logger = logger_manager.LoggerManager(logger_name='opendata-anonymizer', module_name='opendata')

        absolute_config_path = os.path.abspath(opendata_config_module_path)
        config = self._load_module(absolute_config_path, logger)

        try:
            self.anonymizer = config.anonymizer
        except Exception:
            logger.log_error('anonymizer_configuration_reading_failed',
                             "Config file at {0} doesn't have attribute `anonymizer`.".format(absolute_config_path))
            raise

        try:
            self.mongo_db = config.mongo_db
        except Exception:
            logger.log_error('anonymizer_configuration_reading_failed',
                             "Config file at {0} doesn't have attribute `mongo_db`.".format(absolute_config_path))
            raise

        try:
            self.postgres = config.postgres
        except Exception:
            logger.log_error('anonymizer_configuration_reading_failed',
                             "Config file at {0} doesn't have attribute `postgres`.".format(absolute_config_path))
            raise

        try:
            self.hiding_rules = config.hiding_rules
        except Exception:
            logger.log_error('anonymizer_configuration_reading_failed',
                             "Config file at {0} doesn't have attribute `hiding_rules`.".format(absolute_config_path))
            raise

        try:
            self.substitution_rules = config.substitution_rules
        except Exception:
            logger.log_error('anonymizer_configuration_reading_failed',
                             "Config file at {0} doesn't have attribute `substitution_rules`.".format(absolute_config_path))
            raise

        try:
            self.field_data_file = config.field_data_file
        except Exception:
            logger.log_error('anonymizer_configuration_reading_failed',
                             "Config file at {0} doesn't have attribute `field_data_file`.".format(
                                 absolute_config_path))
            raise

    def _load_module(self, opendata_config_module_path, logger):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("opendata_config", opendata_config_module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            return module
        except Exception:
            error_msg = """Failed to load config file from the location {0}.
            Consider providing the file or fix the `opendata_config_path` value in anonymize.py. ERROR: """.format(
                opendata_config_module_path, traceback.format_exc().replace('\n', ''))
            logger.log_error('anonymizer_configuration_reading_failed',
                             error_msg)
            logger.error(error_msg, exc_info=True)
            raise
