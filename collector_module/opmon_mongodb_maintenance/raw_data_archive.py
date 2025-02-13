#
# The MIT License 
# Copyright (c) 2021- Nordic Institute for Interoperability Solutions (NIIS)
# Copyright (c) 2017-2020 Estonian Information System Authority (RIA)
#  
# Permission is hereby granted, free of charge, to any person obtaining a copy 
# of this software and associated documentation files (the "Software"), to deal 
# in the Software without restriction, including without limitation the rights 
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions: 
#  
# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software. 
#  
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN 
# THE SOFTWARE.
#
""" Archive Raw Data

Usage example:

> python raw_data_archive.py query_db_sample root --auth admin --host 127.0.0.1:27017

"""

import time
import getpass
import argparse
import pymongo
from bson.json_util import dumps
import gzip


def process_archive(total_to_archive, minimum_to_archive, mdb_database, mdb_user, mdb_pwd, mdb_server, mdb_auth):
    uri = "mongodb://{0}:{1}@{2}/{3}".format(mdb_user, mdb_pwd, mdb_server, mdb_auth)
    db_name = '{0}'.format(mdb_database)
    client = pymongo.MongoClient(uri)
    raw_messages = client[db_name].raw_messages

    cur = raw_messages.find({'corrected': True}).sort("insertTime", 1).limit(total_to_archive)
    docs = list(cur)

    total_docs = len(docs)
    if total_docs < minimum_to_archive:
        print('The total of {0} queries is smaller than the minimum of {1}'.format(total_docs, minimum_to_archive))
        print('- Canceling operation ...')
        return

    timestamp = int(time.time())
    output_file = 'raw_archive_{0}_{1}.json.gz'.format(mdb_database, timestamp)
    print('- Archiving {0} queries to {1} ...'.format(total_docs, output_file))
    
    lines = []
    to_removal = set()
    for d in docs:
        ds = '{0}\n'.format(dumps(d))
        lines.append(ds.encode('utf-8'))
        to_removal.add(d['_id'])

    # Save documents to GZIP file
    with gzip.open(output_file, 'wb') as f:
        f.writelines(lines)
    # Remove saved documents from raw data
    for d_id in to_removal:
        raw_messages.remove({"_id": d_id})


def main():
    # Get arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('MONGODB_DATABASE', metavar="MONGODB_DATABASE", type=str, help="MongoDB Database")
    parser.add_argument('MONGODB_USER', metavar="MONGODB_USER", type=str, help="MongoDB Database SUFFIX")
    parser.add_argument('--password', dest='mdb_pwd', help='MongoDB Password', default=None)
    parser.add_argument('--auth', dest='auth_db', help='Authorization Database', default='admin')
    parser.add_argument('--host', dest='mdb_host', help='MongoDB host (default: %(default)s)',
                        default='127.0.0.1:27017')
    parser.add_argument('--confirm', dest='confirmation', help='Skip confirmation step, if True', default="False")
    parser.add_argument('--total', dest='total', help='Total queries to be archived (default: %(default)s)',
                        default=50000)
    parser.add_argument('--minimum', dest='minimum', help='Minimum queries execute (default: %(default)s)',
                        default=10000)

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
    uri = "mongodb://{0}:{1}@{2}/{3}".format(mdb_user, mdb_pwd, mdb_server, mdb_auth)
    db_name = '{0}'.format(mdb_database)

    print('- Connecting to database: {0}'.format(db_name))
    client = pymongo.MongoClient(uri)
    db = client[db_name]
    total_raw_docs = db.raw_messages.count()
    total_processed_docs = db.raw_messages.find({'corrected': True}).count()
    print('- Total documents from raw collection: {0}'.format(total_raw_docs))
    print('- Total documents ready to archive: {0}'.format(total_processed_docs))
    print('- Total of (MAX:{0} MIN:{1}) will be archived in this batch.'.format(total_to_archive, minimum_to_archive))

    if args.confirmation.lower() == 'true':
        choice = 'y'
    else:
        choice = input('- Proceed ? [y/n]: ')

    if choice.strip().lower() in {'y', 'yes'}:
        process_archive(total_to_archive, minimum_to_archive,
                        mdb_database, mdb_user, mdb_pwd, mdb_server, mdb_auth)
    else:
        print('- Canceling operation ...')
    print('- Done')


if __name__ == '__main__':
    main()
