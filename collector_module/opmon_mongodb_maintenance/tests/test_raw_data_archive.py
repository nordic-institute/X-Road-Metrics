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

"""
Unit tests for raw_data_archive.py
"""
import mongomock
from opmon_mongodb_maintenance.raw_data_archive import process_archive
from opmon_mongodb_maintenance.raw_data_archive import parse_args
import opmon_mongodb_maintenance

mdb_database="test_database"
mdb_user="test_user"
mdb_pwd="test_pwd"
mdb_server="test_server"
mdb_auth="test_auth"
test_time = 1605000000


def fake_mongo_client_factory():
    def fake_mongo_client(uri, *args, **kwargs):
        expected_uri = (
            f"mongodb://{mdb_user}:{mdb_pwd}"
            f"@{mdb_server}/{mdb_auth}"
        )
        if uri != expected_uri:
            print("Expected: " + expected_uri)
            print("Actual: " + uri)
            raise Exception("Authentication failed. Invalid uri")

        client = mongomock.MongoClient()

        return client

    return fake_mongo_client

def test_process_archive_correct_uri(monkeypatch):
    fake_mongo_client = fake_mongo_client_factory()
    monkeypatch.setattr(opmon_mongodb_maintenance.raw_data_archive.pymongo, "MongoClient",fake_mongo_client)

    process_archive(1, 1, mdb_database, mdb_user, mdb_pwd, mdb_server, mdb_auth)

def test_process_archive_fail_higher_minimum(monkeypatch, capsys):
    total_to_archive = 5
    minimum_to_archive = 5

    fake_mongo_client = fake_mongo_client_factory()
    uri = "mongodb://" + mdb_user + ":" + mdb_pwd + "@" + mdb_server + "/" + mdb_auth
    mock_client = fake_mongo_client(uri)

    # insert test documents
    db = mock_client[mdb_database]
    collection = db["raw_messages"]
    collection.insert_many([
        {"id": 1, "insertTime": test_time, "corrected": True},
        {"id": 2, "insertTime": test_time + 200, "corrected": True},
        {"id": 3, "insertTime": test_time + 300, "corrected": False},
        {"id": 4, "insertTime": test_time + 500, "corrected": True},
        {"id": 5, "insertTime": test_time + 400, "corrected": True},
    ])
    assert collection.count_documents({}) == 5

    monkeypatch.setattr(opmon_mongodb_maintenance.raw_data_archive.pymongo, "MongoClient", lambda *a, **k: mock_client)

    process_archive(total_to_archive, minimum_to_archive, mdb_database, mdb_user, mdb_pwd, mdb_server, mdb_auth)

    # assert no data removed
    assert collection.count_documents({}) == 5

def test_process_archive_keep_maximum_amount_and_sort_time(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    total_to_archive=3
    minimum_to_archive=1

    fake_mongo_client = fake_mongo_client_factory()
    uri = "mongodb://"+ mdb_user + ":" + mdb_pwd + "@" + mdb_server + "/" + mdb_auth
    mock_client = fake_mongo_client(uri)

    # insert test documents
    db = mock_client[mdb_database]
    collection = db["raw_messages"]
    collection.insert_many([
        {"id": 1, "insertTime": test_time, "corrected": True},
        {"id": 2, "insertTime": test_time + 200, "corrected": True},
        {"id": 3, "insertTime": test_time + 300, "corrected": False},
        {"id": 4, "insertTime": test_time + 500, "corrected": True},
        {"id": 5, "insertTime": test_time + 400, "corrected": True},
    ])
    assert collection.count_documents({}) == 5

    # assert no gzip exists
    gz_files = list(tmp_path.glob("*.json.gz"))
    assert len(gz_files) == 0

    monkeypatch.setattr(opmon_mongodb_maintenance.raw_data_archive.pymongo, "MongoClient", lambda *a, **k: mock_client)

    process_archive(total_to_archive, minimum_to_archive, mdb_database, mdb_user, mdb_pwd, mdb_server, mdb_auth)

    #assert correct data removed
    assert collection.count_documents({}) == 2
    assert collection.find_one({"id": 3}) is not None
    assert collection.find_one({"id": 4}) is not None

    # assert gzip is created
    gz_files = list(tmp_path.glob("*.json.gz"))
    assert len(gz_files) == 1

def test_raw_data_archive_parse_args_defaults(mocker):
    mocker.patch('sys.argv', ["test_programm", "TEST", "TEST2"])
    args = parse_args()

    assert args.MONGODB_DATABASE == "TEST"
    assert args.MONGODB_USER == "TEST2"
    assert args.mdb_pwd is None
    assert args.auth_db == "admin"
    assert args.mdb_host == '127.0.0.1:27017'
    assert args.confirmation == "False"
    assert args.total == 50000
    assert args.minimum == 10000

def test_raw_data_archive_parse_args(mocker):
    mocker.patch('sys.argv', ["test_programm", "TEST", "TEST2",
                              "--password", "secret", "--auth", "test_user", "--host", "testhost:1234", "--confirm", "True", "--total", "2", "--minimum", "1"])
    args = parse_args()
    args = parse_args()

    assert args.MONGODB_DATABASE == "TEST"
    assert args.MONGODB_USER == "TEST2"
    assert args.mdb_pwd == "secret"
    assert args.auth_db == "test_user"
    assert args.mdb_host == 'testhost:1234'
    assert args.confirmation == "True"
    assert args.total == "2"
    assert args.minimum == "1"


