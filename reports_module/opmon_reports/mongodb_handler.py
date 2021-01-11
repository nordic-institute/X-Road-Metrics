import pymongo


class MongoDBHandler:
    """ Reports MongoDB Handler
    """

    def __init__(self, mongo_settings, xroad_instance):
        self.db_name = f'query_db_{xroad_instance}'
        self.db_reports_state_name = f'reports_state_{xroad_instance}'

        self.user = mongo_settings['user']
        pwd = mongo_settings['password']
        server = mongo_settings['host']
        self.uri = f"mongodb://{self.user}:{pwd}@{server}/auth_db"

    def get_query_db(self):
        client = pymongo.MongoClient(self.uri)
        db = client[self.db_name]
        return db

    def get_reports_state_db(self):
        client = pymongo.MongoClient(self.uri)
        db = client[self.db_reports_state_name]
        return db
