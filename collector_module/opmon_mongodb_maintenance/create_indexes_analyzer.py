""" MongoDB script - Analyzer

Usage example:

> python create_indexes_analyzer.py analyzer_database_sample root --auth admin --host 127.0.0.1:27017

"""

import argparse
import getpass
import pymongo
from tqdm import tqdm


def add_index(db, collection_name, index_list):
    collection = db[collection_name]
    r = collection.create_index(index_list, background=True)
    return r


def main():
    parser = argparse.ArgumentParser(description='MongoDB script - Analyzer')
    parser.add_argument('MONGODB_DATABASE', metavar="MONGODB_DATABASE", type=str, help="MongoDB Database")
    parser.add_argument('MONGODB_USER', metavar="MONGODB_USER", type=str, help="MongoDB Database user")
    parser.add_argument('--password', dest='mdb_pwd', help='MongoDB Password', default=None)
    parser.add_argument('--auth', dest='auth_db', help='Authorization Database', default='admin')
    parser.add_argument('--host', dest='mdb_host', help='MongoDB host (default: %(default)s)',
                        default='127.0.0.1:27017')

    args = parser.parse_args()
    # Get user password to access MongoDB
    mdb_pwd = args.mdb_pwd
    if mdb_pwd is None:
        mdb_pwd = getpass.getpass('Password:')

    # Connection URI
    uri = "mongodb://{0}:{1}@{2}/{3}".format(args.MONGODB_USER, mdb_pwd, args.mdb_host, args.auth_db)
    db_name = '{0}'.format(args.MONGODB_DATABASE)

    print('- Connecting to database: {0}'.format(db_name))
    client = pymongo.MongoClient(uri)
    db = client[db_name]

    mdb_indexes = list()
    mdb_indexes.append(('incident', [('incident_status', 1), ('incident_creation_timestamp', 1)]))

    print('* Creating analyzer_database.incident MongoDB indexes:')
    i_list = []
    for db_ind in tqdm(mdb_indexes):
        i_list.append(add_index(db, db_ind[0], db_ind[1]))

    print('-- Total of {0} indexes created.'.format(len(i_list)))
    print('-- Index list: {0}'.format(i_list))


if __name__ == '__main__':
    main()
