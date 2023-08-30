import json
from logging import Logger
from pprint import pformat

from metrics_statistics.central_server_client import CentralServerClient
from metrics_statistics.mongodb_manager import DatabaseManager
from metrics_statistics.postgresql_manager import (
    PostgreSQL_LogManager, PostgreSQL_StatisticsManager, StatisticalData)


def collect_statistics(settings: dict, logger: Logger, output_only: bool = False) -> None:
    """
    Collects and updates statistics data based on requests counts.

    Parameters:
        settings (dict): A dictionary containing the necessary settings for collecting statistics.
        logger: An instance of a logger object used for logging messages.
        output_only (bool): If True, only outputs the statistical metrics data without updating the database.

    Returns:
        None

    """
    logger.info('Metrics statistics data: starting aggregate')

    database_manager = DatabaseManager(settings['mongodb'], settings['xroad']['instance'], logger)
    pg_statistics_manager = PostgreSQL_StatisticsManager(settings['postgres'], logger)
    pg_log_manager = PostgreSQL_LogManager(settings['postgres'], logger)
    cs_client = CentralServerClient(settings['xroad'], logger)

    members_in_config = cs_client.get_members_in_config()
    member_counts = cs_client.get_member_count(members_in_config)
    requests_counts = database_manager.get_requests_counts()
    services = pg_log_manager.get_services()
    max_services_by_requests = settings.get('metrics-statistics', {}).get('num-max-services-requests', 5)
    services_counts = database_manager.get_services_counts(services, max_services_by_requests)

    statistics: StatisticalData = {
        **requests_counts,
        **{'member_count': json.dumps(member_counts)},
        **{'service_count': len(services)},
        **{'service_request_count': json.dumps(services_counts)}
    }
    if output_only:
        logger.info('Metrics statistical data:\n\n%s', pformat(statistics, indent=2, width=2))
    else:
        pg_statistics_manager.add_statistics(statistics)
        logger.info('Metrics statistics data: saved to database successfully. '
                    f"Total requests counted: {requests_counts['total_request_count']}")
