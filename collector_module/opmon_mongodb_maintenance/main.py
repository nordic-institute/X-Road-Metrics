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

import argparse
import getpass
from pymongo import MongoClient

from .create_users import create_users
from .create_indexes import create_indexes


def main():
    args = _parse_args()
    client = _connect_mongo(args)

    try:
        create_users(args, client)
    except Exception as e:
        print(f"Failed to create users: {e}")

    try:
        create_indexes(args.xroad, client)
    except Exception as e:
        print(f"Failed  to create indexes: {e}")


def _connect_mongo(args):
    if args.user is None:
        return MongoClient(args.host)

    password = args.password or getpass.getpass()
    return MongoClient(
        args.host,
        username=args.user,
        password=password,
        authSource=args.auth
    )


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("xroad", metavar="X-ROAD-INSTANCE", help="X-Road instance name.")
    parser.add_argument("--host", metavar="HOST:PORT", default="localhost:27017",
                        help="MongoDb host:port. Default is localhost:27017")
    parser.add_argument("--user", help='MongoDb username', default=None)
    parser.add_argument("--password", help='MongoDb password', default=None)
    parser.add_argument('--auth', help='Authorization Database', default='admin')
    parser.add_argument("--dummy-passwords", action="store_true",
                        help="Skip generation of secure passwords for users. Password will be same as username.")
    parser.add_argument("--generate-admins", action="store_true", help="Also generate admin users.")
    args = parser.parse_args()

    return args


if __name__ == "__main__":
    main()
