#  The MIT License
#  Copyright (c) 2021- Nordic Institute for Interoperability Solutions (NIIS)
#  Copyright (c) 2017-2020 Estonian Information System Authority (RIA)
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

import logging

from pymongo import ASCENDING as ASC
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__file__)

indexRequests = [
    {
        'db': 'query_db',
        'collection': 'raw_messages',
        'indexes': [
            [('requestInTs', ASC)],
            [('corrected', ASC), ('requestInTs', ASC)]
        ]
    },

    {
        'db': 'query_db',
        'collection': 'clean_data',
        'indexes': [
            [('xRequestId', ASC)],
            [('correctorTime', ASC)],
            [('correctorStatus', ASC), ('client.requestInTs', ASC)],
            [('correctorStatus', ASC), ('producer.requestInTs', ASC)],
            [('correctorStatus', ASC), ('xRequestId', ASC)],
            [('client.xRequestId', ASC)],
            [('client.requestInTs', ASC)],
            [('client.serviceCode', ASC)],
            [('producer.requestInTs', ASC)],
            [('producer.serviceCode', ASC)],
            [('producer.xRequestId', ASC)],
            [('client.clientMemberCode', ASC), ('client.clientSubsystemCode', ASC), ('client.requestInTs', ASC)],
            [('client.serviceMemberCode', ASC), ('client.serviceSubsystemCode', ASC), ('client.requestInTs', ASC)],
            [('producer.clientMemberCode', ASC), ('producer.clientSubsystemCode', ASC), ('producer.requestInTs', ASC)],
            [('producer.serviceMemberCode', ASC), ('producer.serviceSubsystemCode', ASC), ('producer.requestInTs', ASC)]
        ]
    },

    {
        'db': 'collector_state',
        'collection': 'server_list',
        'indexes': [[('timestamp', ASC)]]
    },

    {
        'db': 'reports_state',
        'collection': 'notification_queue',
        'indexes': [
            [('status', ASC), ('user_id', ASC)]
        ]
    },

    {
        'db': 'analyzer_database',
        'collection': 'incident',
        'indexes': [
            [('incident_status', ASC), ('incident_creation_timestamp', ASC)]
        ]
    },
]


def create_indexes(xroad_instance: str, client: MongoClient):
    count = 0
    for request in indexRequests:
        db = f"{request['db']}_{xroad_instance}"
        collection = request['collection']

        for index in request['indexes']:
            try:
                client[db][collection].create_index(index)
                count += 1
            except Exception as e:
                logger.exception('Failed to create index', str(e))

    logger.info(f'Created {count} indexes.')
