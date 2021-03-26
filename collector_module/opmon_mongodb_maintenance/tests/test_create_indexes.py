from mongomock import MongoClient

from opmon_mongodb_maintenance.create_indexes import create_indexes


def test_create_indexes():
    client = MongoClient('defaultmongodb')
    create_indexes('TEST', client)

    assert len(client.query_db_TEST.raw_messages.index_information()) == 3
    assert len(client.query_db_TEST.clean_data.index_information()) == 16

