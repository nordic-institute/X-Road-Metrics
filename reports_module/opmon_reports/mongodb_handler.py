import pymongo


class MongoDBHandler:
    """ Reports MongoDB Handler
    """

    def __init__(self, mdb_suffix, mdb_user, mdb_pwd, mdb_server):
        self.mdb_user = mdb_user
        self.mdb_pwd = mdb_pwd
        self.mdb_server = mdb_server
        self.db_name = 'query_db_{0}'.format(mdb_suffix)
        self.db_reports_state_name = 'reports_state_{0}'.format(mdb_suffix)

    def get_query_db(self):
        uri = "mongodb://{0}:{1}@{2}/auth_db".format(self.mdb_user, self.mdb_pwd, self.mdb_server)
        client = pymongo.MongoClient(uri)
        db = client[self.db_name]
        return db

    def get_reports_state_db(self):
        uri = "mongodb://{0}:{1}@{2}/auth_db".format(self.mdb_user, self.mdb_pwd, self.mdb_server)
        client = pymongo.MongoClient(uri)
        db = client[self.db_reports_state_name]
        return db
