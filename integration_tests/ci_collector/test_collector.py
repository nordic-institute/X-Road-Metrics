import os
import signal
import subprocess
import time

import pytest
import pymongo


def test_update_server_list():
    xroad = get_parameter('xroad.instance')
    mongo = get_mongo_collection(f"collector_state_{xroad}", "server_list")

    data = mongo.find({'collector_id': f"collector_{xroad}"})
    data = data.sort([('timestamp', -1)]).limit(1)[0]
    _, timestamp_0 = data['server_list'], data['timestamp']
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

    start_time = time.time()

    command = f"opmon-collector collect".split(' ')
    proc = subprocess.run(command, capture_output=True)
    assert proc.stderr == b''
    assert proc.returncode == 0

    time_filter = {"insertTime": {"$gte": start_time}}
    new_message_ips = mongo.distinct('securityServerInternalIp', time_filter)
    assert len(new_message_ips) == 2

    new_messages = list(mongo.find(time_filter).limit(500))
    assert len(new_messages) > 2

    required_keys = {
        "securityServerInternalIp",
        "securityServerType",
        "requestInTs",
        "responseOutTs",
        "succeeded",
        "insertTime"
    }

    for msg in new_messages:
        missing_keys = required_keys - set(msg.keys())
        assert missing_keys == set()


def test_execution_is_blocked_by_pid_file():
    xroad = get_parameter('xroad.instance')
    pid_dir = get_parameter('collector.pid-directory')
    pid_file = f'{pid_dir}/opmon_collector_{xroad}.pid'
    assert not os.path.isfile(pid_file)

    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))  # write test-executor's pid to collector pidfile

    command = f"opmon-collector update".split(' ')
    proc = subprocess.run(command, capture_output=True)

    message_to_find = "Another opmon-collector instance is already running."

    assert proc.stderr.decode('utf-8').find(message_to_find) > 0
    assert proc.returncode == 1

    command = f"opmon-collector collect".split(' ')
    proc = subprocess.run(command, capture_output=True)

    assert proc.stderr.decode('utf-8').find(message_to_find) > 0
    assert proc.returncode == 1

    os.remove(pid_file)


def test_pid_file_creation_and_deletion():
    assert_action_creates_and_deletes_pid_file(f"opmon-collector collect".split(' '))
    assert_action_creates_and_deletes_pid_file(f"opmon-collector update".split(' '))


def assert_action_creates_and_deletes_pid_file(command):
    xroad = get_parameter('xroad.instance')
    pid_dir = get_parameter('collector.pid-directory')
    pid_file = f'{pid_dir}/opmon_collector_{xroad}.pid'

    assert not os.path.isfile(pid_file)

    start_time = time.time()
    proc = subprocess.Popen(command)

    pid_from_file = None

    while proc.poll() is None and time.time() - start_time < 1000:
        if os.path.isfile(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    pid_from_file = int(f.readline())
                    break
            except Exception:
                pass

    assert pid_from_file == proc.pid

    proc.send_signal(signal.SIGINT)
    proc.wait()
    assert not os.path.isfile(pid_file)


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
