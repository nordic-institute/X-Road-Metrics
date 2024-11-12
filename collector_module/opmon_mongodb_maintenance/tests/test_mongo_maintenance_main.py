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

from argparse import Namespace
from opmon_mongodb_maintenance import main


def test_mongo_client_creation_no_auth(mocker):
    args = Namespace(host='testhost:1234', user=None)

    mocker.patch('opmon_mongodb_maintenance.main.MongoClient')
    main._connect_mongo(args)
    main.MongoClient.assert_called_once_with(args.host)


def test_mongo_client_creation_username_only(mocker):
    args = Namespace(host='testhost:1234', user='testuser', password=None, auth='admin')

    mocker.patch('opmon_mongodb_maintenance.main.MongoClient')
    mocker.patch('opmon_mongodb_maintenance.main.getpass.getpass', return_value='testpass')
    main._connect_mongo(args)

    main.MongoClient.assert_called_once_with(args.host, username=args.user, password='testpass', authSource=args.auth)
    main.getpass.getpass.assert_called_once()


def test_mongo_client_creation_full_auth(mocker):
    args = Namespace(host='testhost:1234', user='testuser', password='pass', auth='admin')

    mocker.patch('opmon_mongodb_maintenance.main.MongoClient')
    mocker.patch('opmon_mongodb_maintenance.main.getpass.getpass', return_value='wrongpass')
    main._connect_mongo(args)

    main.MongoClient.assert_called_once_with(args.host, username=args.user, password=args.password,
                                             authSource=args.auth)
    main.getpass.getpass.assert_not_called()
