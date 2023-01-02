""" Database Manager - Corrector Module
"""

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

import time
from datetime import datetime
import urllib.parse
import pymongo

from .logger_manager import LoggerManager
from . import __version__

RAW_DATA_COLLECTION = 'raw_messages'
CLEAN_DATA_COLLECTION = 'clean_data'


def json_serial(obj):
    """
    JSON serializer for objects not serializable by default json code.
    :param obj: The input object.
    :return: Returns the serialized object.
    """

    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError('Type not serializable')


def get_timestamp():
    """
    Returns current timestamp.
    :return: Returns current timestamp.
    """
    return float(time.time())


class DatabaseManager:

    def __init__(self, settings):
        self.settings = settings
        xroad = settings['xroad']['instance']
        self.logger_m = LoggerManager(settings['logger'], xroad, __version__)
        connect_args = {
            'tls': bool(settings['mongodb'].get('tls')),
            'tlsCAFile': settings['mongodb'].get('tls-ca-file'),
        }
        self.client = pymongo.MongoClient(
            self.get_mongo_uri(settings),
            **connect_args
        )
        self.mdb_database = f'query_db_{xroad}'

    @staticmethod
    def get_mongo_uri(settings):
        user = settings['mongodb']['user']
        password = urllib.parse.quote(settings['mongodb']['password'], safe='')
        host = settings['mongodb']['host']
        return f'mongodb://{user}:{password}@{host}/auth_db'

    def get_query_db(self):
        """
        Gets the specific (XRoadInstance) query database .
        :return: Returns the specific query database.
        """
        db = self.client[self.mdb_database]
        return db

    def mark_as_corrected(self, document):
        """
        Marks a specific document's "corrected" status to "True".
        :param document: The input document.
        :return: None
        """
        doc_id = document['_id']
        db = self.get_query_db()
        raw_data = db[RAW_DATA_COLLECTION]
        raw_data.update_one({'_id': doc_id}, {'$set': {'corrected': True}})

    def get_faulty_raw_documents(self, limit=1000):
        """
        Gets number of documents specified by the limit that have not been corrected and has no xRequestId
        Sorted by "requestInTs".
        :param limit: Number of documents to return.
        :return: Returns documents sorted by "requestInTs". Number is specified by the limit.
        """
        try:
            db = self.get_query_db()
            raw_data = db[RAW_DATA_COLLECTION]
            q = {
                'corrected': None,
                'xRequestId': None,
                'requestInTs': {'$ne': None},
                'securityServerType': {'$ne': None}
            }
            cursor = raw_data.find(q).sort('requestInTs', 1).limit(limit)
            return list(cursor)
        except Exception as e:
            self.logger_m.log_error('DatabaseManager.get_faulty_raw_documents', '{0}'.format(repr(e)))
            raise e

    def get_raw_documents(self, limit=1000):
        """
        Gets number of documents specified by the limit that have not been corrected.
        Sorted by "requestInTs".
        :param limit: Number of documents to return.
        :return: Returns documents sorted by "requestInTs". Number is specified by the limit.
        """
        try:
            db = self.get_query_db()
            raw_data = db[RAW_DATA_COLLECTION]
            q = {'corrected': None}
            cursor = raw_data.find(q).sort('requestInTs', 1).limit(limit)
            return list(cursor)
        except Exception as e:
            self.logger_m.log_error('DatabaseManager.get_raw_documents', '{0}'.format(repr(e)))
            raise e

    def get_processing_document(self, current_doc):
        """
        Gets single processing document.
        :param current_doc: The input document.
        :return: Returns document".
        """
        q = {
            'correctorStatus': 'processing',
            'xRequestId': current_doc['xRequestId'],
        }
        try:
            db = self.get_query_db()
            clean_data = db[CLEAN_DATA_COLLECTION]
            document = clean_data.find_one(q)
            return document
        except Exception as e:
            self.logger_m.log_error('DatabaseManager.get_processing_documents', '{0}'.format(repr(e)))
            raise e

    def get_timeout_documents_client(self, timeout_days, limit=1000):
        """
        Gets the documents from Client that have been processing more than timeout_days.
        :param timeout_days: The timeout days.
        :param limit: Number of documents to return.
        :return: Returns the documents that have been processing more than timeout_days.
        """
        try:
            db = self.get_query_db()
            clean_data = db[CLEAN_DATA_COLLECTION]
            ref_time = 1000 * (get_timestamp() - (timeout_days * 24 * 60 * 60))
            q = {
                'correctorStatus': 'processing',
                'client.requestInTs': {'$lt': ref_time},
                'client.xRequestId': {'$ne': None}
            }
            cursor = clean_data.find(q).limit(limit)
            return list(cursor)
        except Exception as e:
            self.logger_m.log_error('DatabaseManager.get_timeout_documents_client', '{0}'.format(repr(e)))
            raise e

    def get_timeout_documents_producer(self, timeout_days, limit=1000):
        """
        Gets the documents from Producer that have been processing more than timeout_days.
        :param timeout_days: The timeout days.
        :param limit: Number of documents to return.
        :return: Returns the documents that have been processing more than timeout_days.
        """
        try:
            db = self.get_query_db()
            clean_data = db[CLEAN_DATA_COLLECTION]
            ref_time = 1000 * (get_timestamp() - (timeout_days * 24 * 60 * 60))
            q = {
                'correctorStatus': 'processing',
                'client.requestInTs': {'$exists': False},
                'producer.requestInTs': {'$lt': ref_time},
                'producer.xRequestId': {'$ne': None}
            }
            cursor = clean_data.find(q).limit(limit)
            return list(cursor)
        except Exception as e:
            self.logger_m.log_error('DatabaseManager.get_timeout_documents_producer', '{0}'.format(repr(e)))
            raise e

    def add_to_clean_data(self, document):
        """
        Inserts a single document into the clean_data.
        :param document: The input document.
        :return: None
        """
        try:
            db = self.get_query_db()
            clean_data = db[CLEAN_DATA_COLLECTION]
            clean_data.insert_one(document)
        except Exception as e:
            self.logger_m.log_error('DatabaseManager.add_to_clean_data', '{0}'.format(repr(e)))
            raise e

    def update_document_clean_data(self, document):
        """
        Updates a document in the clean_data that has the input document's messageId with the content that the input
        document has.
        :param document: The input document.
        :return: None.
        """
        try:
            db = self.get_query_db()
            clean_data = db[CLEAN_DATA_COLLECTION]
            clean_data.update({'_id': document['_id']}, document)
        except Exception as e:
            self.logger_m.log_error('DatabaseManager.update_form_clean_data', '{0}'.format(repr(e)))
            raise e

    def update_old_to_done(self, list_of_docs):
        """
        Updates then correctorStatus to "done" for the given list of documents. Also updates the correctorTime.
        :param list_of_docs: The input list of documents to be updated.
        :return: Number of documents updated.
        """
        number_of_updated_docs = 0
        try:
            db = self.get_query_db()
            clean_data = db[CLEAN_DATA_COLLECTION]
            for doc in list_of_docs:
                clean_data.update({'_id': doc['_id']},
                                  {'$set': {'correctorStatus': 'done', 'correctorTime': get_timestamp()}})
                number_of_updated_docs += 1

        except Exception as e:
            self.logger_m.log_error('DatabaseManager.update_old_to_done', '{0}'.format(repr(e)))
            raise e

        return number_of_updated_docs

    def check_clean_document_exists(self, x_request_id, document):
        """
        Checks if given document exists in clean_data or not
        :param x_request_id: The input document xRequestId
        :param document: The input document
        :return: Returns true if document exists and false if not.
        """
        db = self.get_query_db()
        clean_data = db[CLEAN_DATA_COLLECTION]
        # client or producer
        party = document['securityServerType'].lower()
        result = clean_data.find(
            {
                f'{party}.securityServerType': document['securityServerType'],
                'xRequestId': x_request_id,
            }
        )
        if len(list(result)) > 0:
            return True
        return False

    def remove_duplicate_from_raw(self, message_id):
        """
        Removes the duplicated document from "raw_messages".
        :param message_id: The document ID. NB: This is not "messageId"!
        :return: None
        """
        try:
            db = self.get_query_db()
            raw_messages = db[RAW_DATA_COLLECTION]
            raw_messages.remove({'_id': message_id})
        except Exception as e:
            self.logger_m.log_error('DatabaseManager.remove_duplicate_from_raw', '{0}'.format(repr(e)))
            raise e
