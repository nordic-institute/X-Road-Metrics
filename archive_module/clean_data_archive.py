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
""" Archive Clean Data

Usage example:

> export xRoadInstance="sample"
> python clean_data_archive.py query_db_${xRoadInstance} root --auth admin --host 127.0.0.1:27017

"""

import locale
import time
from datetime import datetime
import getpass
import argparse
import pymongo
from bson.json_util import dumps
import gzip
import settings

locale.setlocale(locale.LC_ALL, '')  # Use '' for auto, or force e.g. to 'en_US.UTF-8'

def process_archive(total_to_archive, minimum_to_archive, mdb_database, mdb_user, mdb_pwd, mdb_server, mdb_auth):
    total_docs = 0
    count_from_file = count_from_db = False

    uri = "mongodb://{0}:{1}@{2}/{3}".format(mdb_user, mdb_pwd, mdb_server, mdb_auth)
    db_name = '{0}'.format(mdb_database)
    client = pymongo.MongoClient(uri)
    clean_data = client[db_name].clean_data

    days = settings.X_DAYS_AGO
    timestamp = int(time.time())
    x_days_ago = timestamp - days * 24 * 60 * 60

    db_str = dict()
    db_str["correctorStatus"] = "done"
    db_str["correctorTime"] = {"$lt": x_days_ago}

    countfile = '{}/count.txt'.format(settings.LOGGER_PATH)
    try:
        with open(countfile, 'r') as f:
            print('{}\t- Reading from file {}'.format(datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), countfile))
            total_docs = f.readlines()
            total_docs = int(total_docs[0])
            f.close()
            count_from_file = True
    except IOError:
        # print('No {} available at the moment'.format(countfile))
        pass

    if not count_from_file or total_docs < minimum_to_archive: 
        print('{}\t- Value from file {:n} less than minimum {:n}'.format(datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), total_docs, minimum_to_archive)) 
        # Read new value of total_docs from MongoDb
        print('{}\t- Connecting to database: {}, query db.clean_data.count({}), {} day(s) ago'.format(datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), db_name, db_str, days))
        total_docs = clean_data.count(db_str)
        count_from_file = False; count_from_db = True

    print('{}\t- Total documents ready to archive {:n}, {} day(s) ago (file: {}, db: {})'.format(datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), total_docs, days, count_from_file, count_from_db))

    if total_docs < minimum_to_archive:
        print('{}\t- The total of {:n} queries from database is smaller than the minimum {:n}'.format(datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), total_docs, minimum_to_archive))
        # if count_from_file = True:
        #     # delete countfile
        #     try:
        #         os.remove(countfile)
        #         # print('Countfile {} removed'.format(countfile))
        #     except OSError:
        #         # print('OSError to remove {}'.format(countfile))
        #         pass

        print('{}\t- Canceling operation ...'.format(datetime.now().strftime("%Y-%m-%dT%H:%M:%S")))
        return

    print('{}\t- Total of (MIN:{:n} MAX:{:n}) will be archived in this batch.'.format(datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), minimum_to_archive, total_to_archive))
    print('{}\t- Connecting to database: {}, query db.clean_data.find({}).limit({})'.format(datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), db_name, db_str, total_to_archive))
    cur = clean_data.find(db_str).limit(total_to_archive)
    docs = list(cur)

    output_dir = settings.CLEAN_DATA_ARCHIVE_DIR
    output_file = '{0}/clean_archive_{1}_{2}.json.gz'.format(output_dir, mdb_database, timestamp)
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
    # Remove saved documents from clean data
    print('{}\t- Remove saved documents from clean_data ...'.format(datetime.now().strftime("%Y-%m-%dT%H:%M:%S")))
    for d_id in to_removal:
        # pass
        clean_data.remove({"_id": d_id})

    # Calculate new count
    total_docs = total_docs - total_to_archive
    # print('New total docs: {:n}'.format(total_docs))
    # Save it
    f = open(countfile, 'w')
    f.write('{}'.format(total_docs))
    f.close()

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
    parser.add_argument('--total', dest='total', help='Total queries to be archived (default: %(default)s)',
                        default=150000)
    parser.add_argument('--minimum', dest='minimum', help='Minimum queries execute (default: %(default)s)',
                        default=100000)

    args = parser.parse_args()

    mdb_database = args.MONGODB_DATABASE
    mdb_user = args.MONGODB_USER
    mdb_server = args.mdb_host
    mdb_auth = args.auth_db

    # Get user password to access MongoDB
    mdb_pwd = args.mdb_pwd
    if mdb_pwd is None:
        mdb_pwd = getpass.getpass('Password:')

    total_to_archive = int(args.total)
    minimum_to_archive = int(args.minimum)

    # uri = "mongodb://{0}:{1}@{2}/{3}".format(mdb_user, mdb_pwd, mdb_server, mdb_auth)
    # db_name = '{0}'.format(mdb_database)

    # days = settings.X_DAYS_AGO
    # timestamp = int(time.time())
    # x_days_ago = timestamp - days * 24 * 60 * 60

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

