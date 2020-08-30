
import pymongo


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class DatabaseConnector(metaclass=Singleton):

    def __init__(self):
        self.client = None

    def start_connection(self, handler):
        uri = "mongodb://{0}:{1}@{2}/auth_db".format(handler.mdb_user, handler.mdb_pwd, handler.mdb_server)
        self.client = pymongo.MongoClient(uri)

    def get_connection(self):
        return self.client

    def has_connection(self):
        return self.client is not None
