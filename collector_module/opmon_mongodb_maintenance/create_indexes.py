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

from pymongo import IndexModel, ASCENDING as ASC
from pymongo import MongoClient
from typing import List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__file__)

class IndexRequest:
    def __init__(self, db: str, collection: str, indexes: List[IndexModel]):
        self.db = db
        self.collection = collection
        self.indexes = indexes

    def get_db(self) -> str:
        return self.db

    def get_collection(self) -> str:
        return self.collection

    def get_indexes(self) -> List[IndexModel]:
        return self.indexes

indexRequests = [
    IndexRequest('query_db',
                 'raw_messages',
                 [
                     IndexModel([('requestInTs', ASC)]),
                     IndexModel([('corrected', ASC), ('requestInTs', ASC)])
                 ]),

    IndexRequest('query_db',
                 'clean_data',
                 [
                     IndexModel([('xRequestId', ASC)]),
                     IndexModel([('correctorTime', ASC)]),
                     IndexModel([('correctorStatus', ASC), ('client.requestInTs', ASC)]),
                     IndexModel([('correctorStatus', ASC), ('producer.requestInTs', ASC)]),
                     IndexModel([('correctorStatus', ASC), ('xRequestId', ASC)]),
                     IndexModel([('client.xRequestId', ASC)]),
                     IndexModel([('client.requestInTs', ASC)]),
                     IndexModel([('client.serviceCode', ASC)]),
                     IndexModel([('producer.requestInTs', ASC)]),
                     IndexModel([('producer.serviceCode', ASC)]),
                     IndexModel([('producer.xRequestId', ASC)]),
                     IndexModel([('client.clientMemberCode', ASC), ('client.clientSubsystemCode', ASC),
                                 ('client.requestInTs', ASC)]),
                     IndexModel([('client.serviceMemberCode', ASC), ('client.serviceSubsystemCode', ASC),
                                 ('client.requestInTs', ASC)]),
                     IndexModel([('producer.clientMemberCode', ASC), ('producer.clientSubsystemCode', ASC),
                                 ('producer.requestInTs', ASC)]),
                     IndexModel([('producer.serviceMemberCode', ASC), ('producer.serviceSubsystemCode', ASC),
                                 ('producer.requestInTs', ASC)])
                 ]),

    IndexRequest('collector_state',
                 'server_list',
                 [
                     IndexModel([('timestamp', ASC)])
                 ]),

    IndexRequest('reports_state',
                 'notification_queue',
                 [
                     IndexModel([('status', ASC), ('user_id', ASC)])
                 ]),

    IndexRequest('analyzer_database',
                 'incident',
                 [
                     IndexModel([('incident_status', ASC), ('incident_creation_timestamp', ASC)])
                 ]),
]


def create_indexes(xroad_instance: str, client: MongoClient):
    count = 0
    for request in indexRequests:
        db = f"{request.get_db()}_{xroad_instance}"
        collection = request.get_collection()

        for index in request.get_indexes():
            try:
                indexes = [index]
                cdb = client[db]
                cdb[collection].create_indexes(indexes)
                count += 1
            except Exception as e:
                logger.exception('Failed to create index', str(e))

    logger.info(f'Created {count} indexes.')
