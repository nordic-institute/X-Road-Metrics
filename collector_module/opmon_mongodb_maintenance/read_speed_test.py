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
""" Read speed in MongoDB Raw and Clean Data

Usage example:

> python read_speed_test.py query_db_sample root --auth admin --host 127.0.0.1:27017

"""

import time
import getpass
import argparse
import pymongo
import json
from tqdm import tqdm


def speed_test(db, collection_name, q):
    collection = db[collection_name]
    tick = time.time()
    col_docs = collection.find(q).count()
    tack = time.time()
    print('--- Total documents in {0}: {1} [count time: {2:.2f} sec.]'.format(collection_name, col_docs, tack - tick))
    max_docs = min(10000, col_docs)
    min_docs = 1000
    if max_docs < min_docs:
        print("--- A minimum of {0} is required. The {1} collection has only {2} docs.".format(min_docs, collection_name, col_docs))
        return
    repeat_time = 10
    print('--- Running read test for {0} documents, {1} times.'.format(max_docs, repeat_time))
    read_speed = []
    for i in tqdm(range(repeat_time)):
        tick = time.time()
        cur = collection.find(q).limit(max_docs)
        _temp = list(cur)
        tack = time.time()
        doc_per_sec = len(_temp) / (tack - tick)
        read_speed.append(doc_per_sec)
    speed_avg = sum(read_speed) / len(read_speed)
    print('--- Avg. read speed for {0} : {1:.2f} docs/sec'.format(collection_name, speed_avg))


def main():
    parser = argparse.ArgumentParser(description='MongoDB script')
    parser.add_argument('MONGODB_DATABASE', metavar="MONGODB_DATABASE", type=str, help="MongoDB Database")
    parser.add_argument('MONGODB_USER', metavar="MONGODB_USER", type=str, help="MongoDB Database user")
    parser.add_argument('--password', dest='mdb_pwd', help='MongoDB Password', default=None)
    parser.add_argument('--auth', dest='auth_db', help='Authorization Database', default='admin')
    parser.add_argument('--raw_query', dest='raw_query', help='Filter query to be used in read raw test', default='{}')
    parser.add_argument('--clean_query', dest='clean_query', help='Filter query to be used in read clean test', default='{}')
    parser.add_argument('--host', dest='mdb_host', help='MongoDB host (default: %(default)s)',
                        default='127.0.0.1:27017')

    args = parser.parse_args()
    # Get user password to access MongoDB
    mdb_pwd = args.mdb_pwd
    if mdb_pwd is None:
        mdb_pwd = getpass.getpass('Password:')

    uri = "mongodb://{0}:{1}@{2}/{3}".format(args.MONGODB_USER, mdb_pwd, args.mdb_host, args.auth_db)
    db_name = '{0}'.format(args.MONGODB_DATABASE)
    db_raw_query = json.loads(args.raw_query)
    db_clean_query = json.loads(args.clean_query)

    print('- Connecting to database: {0}'.format(db_name))
    print('- Reference query - Raw: {0} Clean: {1}'.format(db_raw_query, db_clean_query))

    client = pymongo.MongoClient(uri)
    db = client[db_name]
    print('- Total documents raw collection: {0}'.format(db.raw_messages.count()))
    print('- Total documents clean collection: {0}'.format(db.clean_data.count()))
    print('* Read Speed from Raw Data:')
    speed_test(db, 'raw_messages', db_raw_query)

    print('* Read Speed from Clean Data:')
    speed_test(db, 'clean_data', db_clean_query)


if __name__ == '__main__':
    main()
