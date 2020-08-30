from reports_module import settings
from reportslib import unique_subsystems
from reportslib.database_manager import DatabaseManager
from reportslib.logger_manager import LoggerManager

if __name__ == '__main__':
    """
    Generates a list of all the unique xRoadInstance/memberClass/memberCode/subsystemCode combinations based on DB.
    """
    logger_m = LoggerManager(settings.LOGGER_NAME, 'reports_module')
    logger_m.log_info('unique_subsystems_generation', 'Getting all the unique subsystems from DB')

    try:
        db_m = DatabaseManager(settings.MONGODB_SUFFIX, settings.MONGODB_SERVER, settings.MONGODB_USER,
                               settings.MONGODB_PWD, logger_m)
        member_subsystem_pairs = unique_subsystems.get_unique_pairs(db_m)
        for current_pair in member_subsystem_pairs:
            print(current_pair)

    except Exception as e:
        logger_m.log_error('running_report_main', '{0}'.format(repr(e)))
        raise e

    logger_m.log_info('unique_subsystems_generation', 'Finished getting all the unique subsystems from DB')
