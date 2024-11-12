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
        'member_count': json.dumps(member_counts),
        'service_count': len(services),
        'service_request_count': json.dumps(services_counts)
    }
    if output_only:
        logger.info('Metrics statistical data:\n\n%s', pformat(statistics, indent=2, width=2))
    else:
        pg_statistics_manager.add_statistics(statistics)
        logger.info('Metrics statistics data: saved to database successfully. '
                    f"Total requests counted: {requests_counts['total_request_count']}")
