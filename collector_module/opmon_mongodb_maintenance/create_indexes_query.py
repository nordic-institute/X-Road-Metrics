""" MongoDB script - Query Database

Usage example:

> python create_indexes_query.py query_db_sample root --auth admin --host 127.0.0.1:27017

"""

import argparse
import getpass
import pymongo
from tqdm import tqdm


def add_index(db, collection_name, index_list):
    # See also: https://docs.mongodb.com/manual/core/index-creation/#index-creation-background
    collection = db[collection_name]
    r = collection.create_index(index_list, background=True)
    return r


def main():
    parser = argparse.ArgumentParser(description='MongoDB script - Query Database')
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
    print('- Total documents raw collection: {0}'.format(db.raw_messages.count()))
    print('- Total documents clean collection: {0}'.format(db.clean_data.count()))

    #
    # Single indexes
    #
    mdb_indexes = list()
    #
    # Indexes for 'raw_messages' collection
    #
    # mdb_indexes.append(('raw_messages', [('messageId', 1)]))
    # mdb_indexes.append(('raw_messages', [('insertTime', 1)]))
    # mdb_indexes.append(('raw_messages', [('requestInTs', 1)]))
    # mdb_indexes.append(('raw_messages', [('corrected', 1)]))
    mdb_indexes.append(('raw_messages', [('corrected', 1), ('requestInTs', 1)]))
    #
    # Indexes for 'clean_data' collection
    #
    # mdb_indexes.append(('clean_data', [('messageId', 1)]))
    mdb_indexes.append(('clean_data', [('clientHash', 1)]))
    mdb_indexes.append(('clean_data', [('producerHash', 1)]))
    mdb_indexes.append(('clean_data', [('correctorTime', 1)]))
    # mdb_indexes.append(('clean_data', [('correctorStatus', 1)]))
    # mdb_indexes.append(('clean_data', [('matchingType', 1)]))
    # Needed for anonymizer? Probably not! It is enough to have just / only correctorTime
    # mdb_indexes.append(('clean_data', [('correctorStatus', 1), ('correctorTime', 1)]))
    mdb_indexes.append(('clean_data', [('correctorStatus', 1), ('client.requestInTs', 1)]))
    mdb_indexes.append(('clean_data', [('correctorStatus', 1), ('producer.requestInTs', 1)]))
    mdb_indexes.append(('clean_data', [('messageId', 1), ('client.requestInTs', 1)]))
    mdb_indexes.append(('clean_data', [('messageId', 1), ('producer.requestInTs', 1)]))
    #
    # Indexes for 'clean_data' collection, client object
    #
    # mdb_indexes.append(('clean_data', [('client.monitoringDataTs', 1)]))
    # mdb_indexes.append(('clean_data', [('client.clientXRoadInstance', 1)]))
    # mdb_indexes.append(('clean_data', [('client.clientMemberClass', 1)]))
    # mdb_indexes.append(('clean_data', [('client.clientMemberCode', 1)]))
    # mdb_indexes.append(('clean_data', [('client.clientSubsystemCode', 1)]))
    # mdb_indexes.append(('clean_data', [('client.clientSecurityServerAddress', 1)]))
    mdb_indexes.append(('clean_data', [('client.requestInTs', 1)]))
    # mdb_indexes.append(('clean_data', [('client.serviceXRoadInstance', 1)]))
    # mdb_indexes.append(('clean_data', [('client.serviceMemberClass', 1)]))
    # mdb_indexes.append(('clean_data', [('client.serviceMemberCode', 1)]))
    # mdb_indexes.append(('clean_data', [('client.serviceSubsystemCode', 1)]))
    # mdb_indexes.append(('clean_data', [('client.serviceSecurityServerAddress', 1)]))
    mdb_indexes.append(('clean_data', [('client.serviceCode', 1)]))
    # mdb_indexes.append(('clean_data', [('client.serviceVersion', 1)]))
    # mdb_indexes.append(('clean_data', [('client.succeeded', 1)]))
    #
    # Indexes for 'clean_data' collection, producer object
    #
    # mdb_indexes.append(('clean_data', [('producer.monitoringDataTs', 1)]))
    # mdb_indexes.append(('clean_data', [('producer.clientXRoadInstance', 1)]))
    # mdb_indexes.append(('clean_data', [('producer.clientMemberClass', 1)]))
    # mdb_indexes.append(('clean_data', [('producer.clientMemberCode', 1)]))
    # mdb_indexes.append(('clean_data', [('producer.clientSubsystemCode', 1)]))
    # mdb_indexes.append(('clean_data', [('producer.clientSecurityServerAddress', 1)]))
    mdb_indexes.append(('clean_data', [('producer.requestInTs', 1)]))
    # mdb_indexes.append(('clean_data', [('producer.serviceXRoadInstance', 1)]))
    # mdb_indexes.append(('clean_data', [('producer.serviceMemberClass', 1)]))
    # mdb_indexes.append(('clean_data', [('producer.serviceMemberCode', 1)]))
    # mdb_indexes.append(('clean_data', [('producer.serviceSubsystemCode', 1)]))
    # mdb_indexes.append(('clean_data', [('producer.serviceSecurityServerAddress', 1)]))
    mdb_indexes.append(('clean_data', [('producer.serviceCode', 1)]))
    # mdb_indexes.append(('clean_data', [('producer.serviceVersion', 1)]))
    # mdb_indexes.append(('clean_data', [('producer.succeeded', 1)]))
    #
    # Indexes for 'clean_data' collection, client and producer object. Reduces time spent for reports
    #
    mdb_indexes.append(('clean_data', [('client.clientMemberCode', 1), ('client.clientSubsystemCode', 1), ('client.requestInTs', 1)]))
    mdb_indexes.append(('clean_data', [('client.serviceMemberCode', 1), ('client.serviceSubsystemCode', 1), ('client.requestInTs', 1)]))
    mdb_indexes.append(('clean_data', [('producer.clientMemberCode', 1), ('producer.clientSubsystemCode', 1), ('producer.requestInTs', 1)]))
    mdb_indexes.append(('clean_data', [('producer.serviceMemberCode', 1), ('producer.serviceSubsystemCode', 1), ('producer.requestInTs', 1)]))
    # namespace name generated from index name "..."  is too long (127 byte max)
	# Probably these indexes are not required, please review speed of reports
    # mdb_indexes.append(('clean_data', [('client.clientMemberCode', 1), ('producer.serviceMemberCode', 1), ('client.clientSubsystemCode', 1), ('producer.serviceSubsystemCode', 1), ('client.requestInTs', 1), ('producer.requestInTs', 1)]))
    # mdb_indexes.append(('clean_data', [('client.serviceMemberCode', 1), ('producer.clientMemberCode', 1), ('client.serviceSubsystemCode', 1), ('producer.clientSubsystemCode', 1), ('client.requestInTs', 1), ('producer.requestInTs', 1)]))
	
    print('* Creating Query MongoDB indexes:')
    i_list = []
    for db_ind in tqdm(mdb_indexes):
        i_list.append(add_index(db, db_ind[0], db_ind[1]))

    print('-- Total of {0} indexes created.'.format(len(i_list)))
    print('-- Index list: {0}'.format(i_list))


if __name__ == '__main__':
    main()