import subprocess

import pytest
import pymongo
import time


def get_parameter(parameter_name):
    command = f"opmon-collector settings get {parameter_name}".split(' ')
    proc = subprocess.run(command, capture_output=True)
    assert len(proc.stdout) > 0
    assert proc.stderr == b''
    assert proc.returncode == 0

    return proc.stdout.decode("utf-8").strip()


def get_mongo_collection(db_name, collection_name):
    user = get_parameter('mongodb.user')
    password = get_parameter('mongodb.password')
    mongo_host = get_parameter('mongodb.host')
    mongo_uri = f"mongodb://{user}:{password}@{mongo_host}/auth_db"

    return pymongo.MongoClient(mongo_uri)[db_name][collection_name]


def test_update_server_list():
    xroad = get_parameter('xroad.instance')
    mongo = get_mongo_collection(f"collector_state_{xroad}", "server_list")

    data = mongo.find({'collector_id': f"collector_{xroad}"})
    data = data.sort([('timestamp', -1)]).limit(1)[0]
    server_list_0, timestamp_0 = data['server_list'], data['timestamp']
    assert timestamp_0 < time.time()

    command = f"opmon-collector update".split(' ')
    proc = subprocess.run(command, capture_output=True)
    assert proc.stderr == b''
    assert proc.returncode == 0

    data = mongo.find({'collector_id': f"collector_{xroad}"})
    data = data.sort([('timestamp', -1)]).limit(1)[0]
    server_list_1, timestamp_1 = data['server_list'], data['timestamp']

    assert timestamp_1 > timestamp_0
    assert timestamp_1 == pytest.approx(time.time(), 1.0)

    server_codes = [server['serverCode'] for server in server_list_1]
    assert "SS1" in server_codes
    assert "RH1" in server_codes


def test_collect():
    xroad = get_parameter('xroad.instance')
    mongo = get_mongo_collection(f"query_db_{xroad}", "raw_messages")

    raw_message_count_0 = mongo.count_documents({})

    command = f"opmon-collector collect".split(' ')
    proc = subprocess.run(command, capture_output=True)
    assert proc.stderr == b''
    assert proc.returncode == 0

    raw_message_count_1 = mongo.count_documents({})
    assert raw_message_count_1 > raw_message_count_0
