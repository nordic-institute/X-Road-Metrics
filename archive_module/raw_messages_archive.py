""" Archive Raw Messages

Usage example:

> export xRoadInstance="sample"
> python raw_messages_archive.py query_db_${xRoadInstance} root --auth admin --host 127.0.0.1:27017

"""

import time
import locale
from datetime import datetime
import getpass
import argparse
import pymongo
from bson.json_util import dumps
import gzip
import settings

locale.setlocale(locale.LC_ALL, '')  # Use '' for auto, or force e.g. to 'en_US.UTF-8'

def process_archive(total_to_archive, minimum_to_archive, mdb_database, mdb_user, mdb_pwd, mdb_server, mdb_auth):
    uri = "mongodb://{0}:{1}@{2}/{3}".format(mdb_user, mdb_pwd, mdb_server, mdb_auth)
    db_name = '{0}'.format(mdb_database)
    print('{}\t- Connecting to database: {}'.format(datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), db_name))
    client = pymongo.MongoClient(uri)
    raw_messages = client[db_name].raw_messages

    total_docs = raw_messages.find({'corrected': True}).count()
    print('{}\t- Total documents ready to archive: {:n}'.format(datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), total_docs))

    if total_docs < minimum_to_archive:
        print('{}\t- The total of {:n} documents is smaller than the minimum of {:n}'.format(datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), total_docs, minimum_to_archive))
        print('{}\t- Canceling operation ...'.format(datetime.now().strftime("%Y-%m-%dT%H:%M:%S")))
        return

    cur = raw_messages.find({'corrected': True}).limit(total_to_archive)
    docs = list(cur)

    timestamp = int(time.time())
    output_dir = settings.RAW_MESSAGES_ARCHIVE_DIR
    output_file = '{0}/raw_archive_{1}_{2}.json.gz'.format(output_dir, mdb_database, timestamp)
    print('{}\t- Archiving {:n} queries to {} ...'.format(datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), min(total_docs, total_to_archive), output_file))
    
    lines = []
    to_removal = set()
    for d in docs:
        ds = '{0}\n'.format(dumps(d))
        lines.append(ds.encode('utf-8'))
        to_removal.add(d['_id'])

    # Save documents to GZIP file
    print('{}\t- Save documents to GZIP file ...'.format(datetime.now().strftime("%Y-%m-%dT%H:%M:%S")))
    with gzip.open(output_file, 'wb') as f:
        f.writelines(lines)

    # Remove saved documents from raw data
    print('{}\t- Remove saved documents from raw_messages ...'.format(datetime.now().strftime("%Y-%m-%dT%H:%M:%S")))
    for d_id in to_removal:
        # pass
        raw_messages.remove({"_id": d_id})

def main():
    # Get arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('MONGODB_DATABASE', metavar="MONGODB_DATABASE", type=str, help="MongoDB Database")
    parser.add_argument('MONGODB_USER', metavar="MONGODB_USER", type=str, help="MongoDB User")
    parser.add_argument('--password', dest='mdb_pwd', help='MongoDB Password', default=None)
    parser.add_argument('--auth', dest='auth_db', help='Authorization Database', default='admin')
    parser.add_argument('--host', dest='mdb_host', help='MongoDB host (default: %(default)s)',
                        default='127.0.0.1:27017')
    parser.add_argument('--confirm', dest='confirmation', help='Skip confirmation step, if True', default="False")
    parser.add_argument('--minimum', dest='minimum', help='Minimum queries execute (default: %(default)s)',
                        default=100000)
    parser.add_argument('--total', dest='total', help='Total queries to be archived (default: %(default)s)',
                        default=150000)

    args = parser.parse_args()
    # Get user password to access MongoDB
    mdb_pwd = args.mdb_pwd
    if mdb_pwd is None:
        mdb_pwd = getpass.getpass('Password:')

    total_to_archive = int(args.total)
    minimum_to_archive = int(args.minimum)

    mdb_database = args.MONGODB_DATABASE
    mdb_user = args.MONGODB_USER
    mdb_server = args.mdb_host
    mdb_auth = args.auth_db
    # uri = "mongodb://{0}:{1}@{2}/{3}".format(mdb_user, mdb_pwd, mdb_server, mdb_auth)
    # db_name = '{0}'.format(mdb_database)

    # print('{}\t- Connecting to database: {}'.format(datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), db_name))
    # client = pymongo.MongoClient(uri)
    # db = client[db_name]

    if args.confirmation.lower() == 'true':
        choice = 'y'
    else:
        choice = input('- Proceed ? [y/n]: ')

    if choice.strip().lower() in {'y', 'yes'}:
        process_archive(total_to_archive, minimum_to_archive,
                        mdb_database, mdb_user, mdb_pwd, mdb_server, mdb_auth)
    else:
        print('{}\t- Canceling operation ...'.format(datetime.now().strftime("%Y-%m-%dT%H:%M:%S")))
    print('{}\t- Done'.format(datetime.now().strftime("%Y-%m-%dT%H:%M:%S")))


if __name__ == '__main__':
    main()
