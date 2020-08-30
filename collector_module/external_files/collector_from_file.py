""" Collector: File to MongoDB

Usage example:

> python collector_from_file.py query_db_ee-dev root "temp_files/ee-dev.COM.*" --auth auth_db --host 127.0.0.1:27017

"""
import time
import getpass
import json
import hashlib
import collections
import glob
import argparse

import pymongo
from tqdm import tqdm


__version__ = '0.3'


def get_timestamp():
    return float(time.time())


def calculate_hash(_document):
    """ Hash JSON document

    :param _document: JSON document
    :return: the hashed JSON document
    """
    document = _document.copy()
    od = collections.OrderedDict(sorted(document.items()))
    od.pop('_id', None)         # Remove _id if present
    od.pop('insertTime', None)  # Remove insertTime if present
    json_str = str(od)
    doc_hash = hashlib.md5(json_str.encode('utf-8')).hexdigest()
    return "{0}_{1}".format(document['monitoringDataTs'], doc_hash)


def process_files(file_list, mdb_database, mdb_user, mdb_pwd, mdb_server, mdb_auth):
    """ Process list of files into MongoDB

    :param file_list: The list of log files with JSON queries
    :return: None
    """
    uri = "mongodb://{0}:{1}@{2}/{3}".format(mdb_user, mdb_pwd, mdb_server, mdb_auth)
    db_name = '{0}'.format(mdb_database)
    client = pymongo.MongoClient(uri)
    db = client[db_name]
    raw_msg = db['raw_messages']
    total_processed = 0
    total_queries = 0
    total_error = 0
    unique_queries_to_add = []
    queries_hash = set()

    for file_name in file_list:
        print('--> processing file: {0}'.format(file_name))
        with open(file_name) as f:
            lines = f.readlines()
            total_queries += len(lines)
            for i, line in enumerate(lines):
                try:
                    jsonn = json.loads(line)
                    jsonn['insertTime'] = get_timestamp()
                    doc_hash = calculate_hash(jsonn)
                    if doc_hash not in queries_hash:
                        unique_queries_to_add.append(jsonn)
                        queries_hash.add(doc_hash)
                    total_processed += 1
                except Exception as e:
                    print('ERROR: file {0} line {1} --- {2}'.format(file_name, i, e))
                    total_error += 1

    total_unique_queries = len(unique_queries_to_add)
    print('- Total processed: {0} from {1}'.format(total_processed, total_queries))
    print('- Total unique queries: {0} '.format(total_unique_queries))
    print('- Total errors: {0}'.format(total_error))
    print('- Adding queries to MongoDB')
    for jsonn in tqdm(unique_queries_to_add):
        raw_msg.insert_one(jsonn)


def main():

    # Get arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('MONGODB_DATABASE', metavar="MONGODB_DATABASE", type=str, help="MongoDB Database")
    parser.add_argument('MONGODB_USER', metavar="MONGODB_USER", type=str, help="MongoDB Database SUFFIX")
    parser.add_argument("FILE_PATTERN", help="FILE_PATTERN: string with file name or file pattern")
    parser.add_argument('--password', dest='mdb_pwd', help='MongoDB Password', default=None)
    parser.add_argument('--auth', dest='auth_db', help='Authorization Database', default='auth_db')
    parser.add_argument('--host', dest='mdb_host', help='MongoDB host (default: %(default)s)',
                        default='127.0.0.1:27017')
    parser.add_argument('--confirm', dest='confirmation', help='Skip confirmation step, if True', default="False")
    args = parser.parse_args()

    # Get user password to access MongoDB
    mdb_pwd = args.mdb_pwd
    if mdb_pwd is None:
        mdb_pwd = getpass.getpass('Password:')

    file_list = glob.glob(args.FILE_PATTERN)
    total_input_files = len(file_list)
    print('******************************************************************************')
    print('* Collector from file [version {0}]                                          *'.format(__version__))
    print('******************************************************************************')
    print('- The following files will be added to MongoDB (total {0} files)'.format(total_input_files))
    # If no files are added, return
    if total_input_files == 0:
        print('- Nothing to do... please check the input parameter: "{0}"'.format(args.file_pattern))
        return
    # List files to get user approval
    for f in file_list:
        print('> {0}'.format(f))
    print('- JSON queries will be added to MongoDB Database: {0}'.format(args.MONGODB_DATABASE))

    if args.confirmation.lower() == 'true':
        choice = 'y'
    else:
        choice = input('- Proceed ? [y/n]: ')

    mdb_database = args.MONGODB_DATABASE
    mdb_user = args.MONGODB_USER
    mdb_server = args.mdb_host
    mdb_auth = args.auth_db

    if choice.strip().lower() in {'y', 'yes'}:
        process_files(file_list, mdb_database, mdb_user, mdb_pwd, mdb_server, mdb_auth)
    else:
        print('- Canceling operation ...')
    print('- Done')


if __name__ == '__main__':
    main()
