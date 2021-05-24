""" Hash check speed in MongoDB Clean Data

Usage example:

> python hash_speed_test.py query_db_sample root --auth admin --host 127.0.0.1:27017

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
import getpass
import argparse
import pymongo
from tqdm import tqdm


def hash_speed_test(db, collection_name):
    collection = db[collection_name]
    col_docs = collection.count()
    max_docs = min(100, col_docs)
    min_docs = 10
    if max_docs < min_docs:
        print("--- A minimum of {0} is required. The {1} collection has only {2} docs.".format(min_docs, collection_name, col_docs))
        return
    repeat_time = 10
    print('--- Running Hash check test for {0} documents, {1} times.'.format(max_docs, repeat_time))
    check_speed = []
    all_checked = True
    for i in tqdm(range(repeat_time)):
        # Get documents
        cur = collection.find().limit(max_docs)
        _temp_hashes = []
        for d in cur:
            doc_hash = d.get('producerHash', None) if d.get('producerHash', None) else d.get('clientHash', None)
            _temp_hashes.append(doc_hash)
        # Check doc_hash
        tick = time.time()
        for doc_hash in _temp_hashes:
            p = collection.find({'producerHash': doc_hash}).limit(1)
            c = collection.find({'clientHash': doc_hash}).limit(1)
            has_p = len(list(p)) > 0
            has_c = len(list(c)) > 0
            all_checked = all_checked and (has_p or has_c)
        tack = time.time()
        check_per_sec = max_docs / (tack - tick)
        check_speed.append(check_per_sec)
    check_avg = sum(check_speed) / len(check_speed)
    print('--- Avg. Hash check speed for {0} : {1:.2f} docs/sec'.format(collection_name, check_avg))


def main():
    parser = argparse.ArgumentParser(description='MongoDB script')
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

    uri = "mongodb://{0}:{1}@{2}/{3}".format(args.MONGODB_USER, mdb_pwd, args.mdb_host, args.auth_db)
    db_name = '{0}'.format(args.MONGODB_DATABASE)

    print('- Connecting to database: {0}'.format(db_name))
    client = pymongo.MongoClient(uri)
    db = client[db_name]
    print('- Total documents raw collection: {0}'.format(db.raw_messages.count()))
    print('- Total documents clean collection: {0}'.format(db.clean_data.count()))

    print('* Hash Check Speed from Clean Data:')
    hash_speed_test(db, 'clean_data')


if __name__ == '__main__':
    main()
