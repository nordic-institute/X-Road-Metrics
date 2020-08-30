
import time
import pymongo


class MongoAnalyzerDBHandler:
    """ CI Database Handler for Analyzer
    """

    def __init__(self, mdb_user, mdb_pwd, mdb_server):
        self.mdb_user = mdb_user
        self.mdb_pwd = mdb_pwd
        self.mdb_server = mdb_server
        self.db_name = 'CI_analyzer_database'
        self.INCIDENT_COLLECTION = 'incident'
        self.INCIDENT_MODEL_COLLECTION = 'incident_model'
        self.INCIDENT_TIMESTAMPS_COLLECTION = 'incident_timestamps'
        self.SERVICE_CALL_FIRST_TIMESTAMPS_COLLECTION = 'service_call_first_timestamps'

    def get_analyzer_db(self):
        uri = "mongodb://{0}:{1}@{2}/auth_db".format(self.mdb_user, self.mdb_pwd, self.mdb_server)
        client = pymongo.MongoClient(uri)
        db = client[self.db_name]
        return db

    def add_incidents(self, docs):
        db = self.get_analyzer_db()
        collection = db[self.INCIDENT_COLLECTION]
        for doc in docs:
            collection.insert(doc)

    def add_incident_model(self, model):
        db = self.get_analyzer_db()
        collection = db[self.INCIDENT_MODEL_COLLECTION]
        collection.insert(model)
        
    def add_incident_timestamps(self, docs):
        db = self.get_analyzer_db()
        collection = db[self.INCIDENT_TIMESTAMPS_COLLECTION]
        for doc in docs:
            collection.insert(doc)
            
    def add_service_call_first_timestamps(self, docs):
        db = self.get_analyzer_db()
        collection = db[self.SERVICE_CALL_FIRST_TIMESTAMPS_COLLECTION]
        for doc in docs:
            collection.insert(doc)

    def remove_incident_collection(self):
        db = self.get_analyzer_db()
        collection = db[self.INCIDENT_COLLECTION]
        collection.drop()

    def remove_incident_model_collection(self):
        db = self.get_analyzer_db()
        collection = db[self.INCIDENT_MODEL_COLLECTION]
        collection.drop()
        
    def remove_incident_timestamps_collection(self):
        db = self.get_analyzer_db()
        collection = db[self.INCIDENT_TIMESTAMPS_COLLECTION]
        collection.drop()
        
    def remove_service_call_first_timestamps_collection(self):
        db = self.get_analyzer_db()
        collection = db[self.SERVICE_CALL_FIRST_TIMESTAMPS_COLLECTION]
        collection.drop()

    def remove_all(self):
        self.remove_incident_collection()
        self.remove_incident_model_collection()
        self.remove_incident_timestamps_collection()
        self.remove_service_call_first_timestamps_collection()
