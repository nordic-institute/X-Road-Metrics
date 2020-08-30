
import time

import pymongo

from .ci_db_connector import DatabaseConnector


class MongoDBHandler:
    """ CI Database Handler for Reports
    """

    def __init__(self, mdb_user, mdb_pwd, mdb_server):
        self.mdb_user = mdb_user
        self.mdb_pwd = mdb_pwd
        self.mdb_server = mdb_server
        self.db_name = 'CI_query_db'
        self.db_reports_state_name = 'CI_reports_state'
        self.RAW_DATA_COLLECTION = 'raw_messages'
        self.CLEAN_DATA_COLLECTION = 'clean_data'

    def get_query_db(self):
        db_conn = DatabaseConnector()
        if not db_conn.has_connection():
            db_conn.start_connection(self)

        client = db_conn.get_connection()
        db = client[self.db_name]
        return db

    def get_reports_state_db(self):
        db_conn = DatabaseConnector()
        if not db_conn.has_connection():
            db_conn.start_connection(self)

        client = db_conn.get_connection()
        db = client[self.db_reports_state_name]
        return db

    def add_raw_documents(self, docs):
        db = self.get_query_db()
        collection = db[self.RAW_DATA_COLLECTION]
        for doc in docs:
            doc['insertTime'] = float(time.time())
            collection.insert(doc)

    def get_raw_documents(self):
        db = self.get_query_db()
        collection = db[self.RAW_DATA_COLLECTION]
        cur = collection.find()
        return list(cur)

    def add_clean_documents(self, docs):
        db = self.get_query_db()
        collection = db[self.CLEAN_DATA_COLLECTION]
        for doc in docs:
            collection.insert(doc)

    def add_clean_document(self, doc):
        db = self.get_query_db()
        collection = db[self.CLEAN_DATA_COLLECTION]
        collection.insert(doc)

    def get_clean_documents(self):
        db = self.get_query_db()
        collection = db[self.CLEAN_DATA_COLLECTION]
        cur = collection.find()
        return list(cur)

    def remove_raw_collection(self):
        db = self.get_query_db()
        collection = db[self.RAW_DATA_COLLECTION]
        collection.drop()

    def remove_clean_collection(self):
        db = self.get_query_db()
        collection = db[self.CLEAN_DATA_COLLECTION]
        collection.drop()

    def remove_all(self):
        self.remove_raw_collection()
        self.remove_clean_collection()

    def create_indexes(self):
        mdb_indexes = list()
        mdb_indexes.append(('clean_data', 'client.clientMemberCode'))
        mdb_indexes.append(('clean_data', 'client.clientSubsystemCode'))
        mdb_indexes.append(('clean_data', 'client.monitoringDataTs'))
        mdb_indexes.append(('clean_data', 'client.requestInTs'))
        mdb_indexes.append(('clean_data', 'client.serviceMemberCode'))
        mdb_indexes.append(('clean_data', 'client.serviceSubsystemCode'))
        mdb_indexes.append(('clean_data', 'clientHash'))
        mdb_indexes.append(('clean_data', 'correctorStatus'))
        mdb_indexes.append(('clean_data', 'correctorTime'))
        mdb_indexes.append(('clean_data', 'messageId'))
        mdb_indexes.append(('clean_data', 'producer.clientMemberCode'))
        mdb_indexes.append(('clean_data', 'producer.clientSubsystemCode'))
        mdb_indexes.append(('clean_data', 'producer.monitoringDataTs'))
        mdb_indexes.append(('clean_data', 'producer.requestInTs'))
        mdb_indexes.append(('clean_data', 'producer.serviceMemberCode'))
        mdb_indexes.append(('clean_data', 'producer.serviceSubsystemCode'))
        mdb_indexes.append(('clean_data', 'producerHash'))
        mdb_indexes.append(('clean_data', 'matchingType'))
        mdb_indexes.append(('raw_messages', 'messageId'))
        mdb_indexes.append(('raw_messages', 'insertTime'))
        mdb_indexes.append(('raw_messages', 'corrected'))

        db = self.get_query_db()
        for collection_name, index_reference in mdb_indexes:
            collection = db[collection_name]
            collection.create_index([(index_reference, pymongo.ASCENDING)], background=True)
