from logging import Logger
from pprint import pformat

from metrics_statistics.mongodb_manager import DatabaseManager


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
    requests_counts = database_manager.get_requests_counts()
    if output_only:
        logger.info('Metrics statistical data:\n\n%s', pformat(requests_counts, indent=2, width=2))
    else:
        database_manager.update_statistics(requests_counts)
        logger.info('Metrics statistics data: saved to database successfully. '
                    f"Total requests counted: {requests_counts['total_request_count']}")
