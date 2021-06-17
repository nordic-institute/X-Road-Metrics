from json.decoder import JSONDecodeError

import mongomock
import os
import pymongo
import pytest

from opmon_reports.database_manager import DatabaseManager
from opmon_reports.xroad_descriptor import OpmonXroadDescriptor, OpmonXroadSubsystemDescriptor


@pytest.fixture
def basic_args(mocker):
    args = mocker.Mock()
    args.xroad_instance = "TEST"
    args.settings = {
        "xroad": {"descriptor-path": ""},
        "mongodb": {"host": "testmongo", "user": "foo", "password": "bar"}
    }
    args.subsystem = None
    args.start_time_milliseconds = 1609459200000  # 2021-01-01T00:00:00Z
    args.end_time_milliseconds = 1609545600000  # 2021-01-02T00:00:00Z

    return args


@pytest.fixture
def dummy_database(mocker):
    db = mocker.Mock()
    db.get_unique_subsystems = lambda x, y: []
    return db


def get_resource_path(resource_file_name):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "resources",
        resource_file_name
    )


def test_xroad_descriptor_parsing_valid1(mocker, basic_args):
    basic_args.settings['xroad']['descriptor-path'] = get_resource_path("xroad_descriptor_valid1.json")
    xroad_descriptor = OpmonXroadDescriptor(basic_args, mocker.Mock(), mocker.Mock())
    assert len(xroad_descriptor) == 6
    assert xroad_descriptor[0].xroad_instance == "LTT"
    assert xroad_descriptor[0].get_subsystem_name('fi') == "Testialijärjestelmä"
    assert xroad_descriptor[0].get_emails()[0]['name'] == "Seppo Sorsa"
    assert xroad_descriptor[0].get_emails()[1]['email'] == "teppo@testi.com"

    assert xroad_descriptor[1]._data['email'] == []
    assert xroad_descriptor[1]._data.get('subsystem_name') is None

    assert xroad_descriptor[2]._data.get('email') is None
    assert xroad_descriptor[2]._data.get('subsystem_name') is None

    assert xroad_descriptor[5]._data['email'][0]['name'] == "Out of Place"

    xroad_descriptor.logger.log_warning.assert_not_called()
    xroad_descriptor.logger.log_error.assert_not_called()


def test_xroad_descriptor_parsing_valid2(mocker, basic_args, dummy_database):
    basic_args.settings['xroad']['descriptor-path'] = get_resource_path("xroad_descriptor_valid2.json")
    xroad_descriptor = OpmonXroadDescriptor(basic_args, dummy_database, mocker.Mock())

    xroad_descriptor.logger.log_warning.assert_not_called()
    xroad_descriptor.logger.log_error.assert_not_called()
    assert xroad_descriptor._data == []


def test_xroad_descriptor_parsing_not_json(mocker, basic_args, dummy_database):
    basic_args.settings['xroad']['descriptor-path'] = get_resource_path("xroad_descriptor_not_json.json")
    logger = mocker.Mock()

    with pytest.raises(JSONDecodeError):
        OpmonXroadDescriptor(basic_args, dummy_database, logger)

    logger.log_warning.assert_not_called()
    logger.log_error.assert_called_once()
    assert "parsing failed" in logger.log_error.call_args.args[1]


def test_xroad_descriptor_parsing_schema_fail(mocker, basic_args, dummy_database):
    basic_args.settings['xroad']['descriptor-path'] = get_resource_path("xroad_descriptor_schema_fail.json")
    logger = mocker.Mock()

    with pytest.raises(JSONDecodeError):
        OpmonXroadDescriptor(basic_args, dummy_database, logger)

    logger.log_warning.assert_not_called()
    logger.log_error.assert_called_once()
    assert "parsing failed" in logger.log_error.call_args.args[1]


def test_xroad_descriptor_parsing_file_not_found(mocker, basic_args, dummy_database):
    basic_args.settings['xroad']['descriptor-path'] = "/not/found.json"
    logger = mocker.Mock()

    with pytest.raises(FileNotFoundError):
        OpmonXroadDescriptor(basic_args, dummy_database, logger)

    logger.log_warning.assert_not_called()
    logger.log_error.assert_called_once()
    assert "not found" in logger.log_error.call_args.args[1]


def test_iteration(mocker, basic_args):
    basic_args.settings['xroad']['descriptor-path'] = get_resource_path("xroad_descriptor_valid1.json")
    xroad_descriptor = OpmonXroadDescriptor(basic_args, mocker.Mock(), mocker.Mock())

    for subsystem_descriptor in xroad_descriptor:
        assert isinstance(subsystem_descriptor, OpmonXroadSubsystemDescriptor)
        assert subsystem_descriptor._data in xroad_descriptor._data


def test_subsystem_descriptor_getters(mocker, basic_args):
    basic_args.settings['xroad']['descriptor-path'] = get_resource_path("xroad_descriptor_valid1.json")
    xroad_descriptor = OpmonXroadDescriptor(basic_args, mocker.Mock(), mocker.Mock())

    subsystem_descriptor = xroad_descriptor[0]

    assert subsystem_descriptor.xroad_instance == "LTT"
    assert subsystem_descriptor.member_class == "TESTCLASS"
    assert subsystem_descriptor.member_code == "TESTMEMBER"
    assert subsystem_descriptor.subsystem_code == "TESTSUB"

    assert subsystem_descriptor.get_subsystem_name('fi') == "Testialijärjestelmä"
    assert subsystem_descriptor.get_subsystem_name('sv') == "Test Delsystem"
    assert subsystem_descriptor.get_subsystem_name('foobar') == "TESTSUB"

    emails = subsystem_descriptor.get_emails()
    assert len(emails) == 2
    assert emails == [
        {'name': 'Seppo Sorsa', 'email': 'seppo.sorsa@gofore.com'},
        {'name': 'Teppo Testi', 'email': 'teppo@testi.com'}
    ]

    assert subsystem_descriptor.get_member_name() == "Test Member Name"

    xroad_descriptor.logger.log_warning.assert_not_called()
    xroad_descriptor.logger.log_error.assert_not_called()


def test_subsystem_descriptor_getters_with_missing_fields(mocker, basic_args):
    basic_args.settings['xroad']['descriptor-path'] = get_resource_path("xroad_descriptor_valid1.json")
    xroad_descriptor = OpmonXroadDescriptor(basic_args, mocker.Mock(), mocker.Mock())

    subsystem_descriptor = xroad_descriptor[2]

    assert subsystem_descriptor.xroad_instance == "LTT"
    assert subsystem_descriptor.member_class == "TESTCLASS"
    assert subsystem_descriptor.member_code == "TESTMEMBER"
    assert subsystem_descriptor.subsystem_code == "MINIMALSUB"

    assert subsystem_descriptor.get_subsystem_name('fi') == "MINIMALSUB"
    assert subsystem_descriptor.get_subsystem_name('sv') == "MINIMALSUB"
    assert subsystem_descriptor.get_subsystem_name('foo') == "MINIMALSUB"
    assert subsystem_descriptor.get_emails() == []

    assert subsystem_descriptor.get_member_name() == "TESTMEMBER"

    xroad_descriptor.logger.log_warning.assert_not_called()
    xroad_descriptor.logger.log_error.assert_not_called()


def test_subsystem_commandline_argument_with_valid_json(mocker, basic_args):
    basic_args.settings['xroad']['descriptor-path'] = get_resource_path("xroad_descriptor_valid1.json")
    basic_args.subsystem = {
        "x_road_instance": "LTT",
        "member_class": "TEST",
        "member_code": "TEST2",
        "subsystem_code": "SUB4"
    }
    xroad_descriptor = OpmonXroadDescriptor(basic_args, mocker.Mock(), mocker.Mock())

    assert len(xroad_descriptor) == 1
    assert xroad_descriptor[0].get_subsystem_name('en') == "RH Test Sub4"


def test_subsystem_commandline_argument_with_invalid_json(mocker, basic_args):
    basic_args.settings['xroad']['descriptor-path'] = get_resource_path("xroad_descriptor_not_json.json")
    basic_args.subsystem = {
        "x_road_instance": "LTT",
        "member_class": "TEST",
        "member_code": "TEST2",
        "subsystem_code": "SUB4"
    }
    xroad_descriptor = OpmonXroadDescriptor(basic_args, mocker.Mock(), mocker.Mock())

    assert len(xroad_descriptor) == 1
    assert xroad_descriptor[0].get_subsystem_name('en') == "SUB4"


@mongomock.patch(servers=(('testmongo', 27017),))
def test_get_subsystems_from_database(mocker, basic_args):
    basic_args.settings['xroad']['descriptor-path'] = ""
    database_manager = DatabaseManager(basic_args, mocker.Mock())

    test_docs = get_test_documents()

    client = pymongo.MongoClient('testmongo')
    for doc in test_docs:
        client['query_db_TEST']['clean_data'].insert_one(doc)

    xroad_descriptor = OpmonXroadDescriptor(basic_args, database_manager, mocker.Mock())
    assert xroad_descriptor._data == [
        {
            'x_road_instance': 'TEST',
            'member_class': 'TESTCLASS',
            'member_code': 'TESTMEMBER',
            'subsystem_code': 'SUB1'
        },
        {
            'x_road_instance': 'TEST',
            'member_class': 'TESTCLASS',
            'member_code': 'TESTMEMBER2',
            'subsystem_code': 'SUBA'
        },
        {
            'x_road_instance': 'TEST',
            'member_class': 'TESTCLASS2',
            'member_code': 'TESTMEMBER3',
            'subsystem_code': 'TESTSUB'
        }
    ]


@mongomock.patch(servers=(('emptymongo', 27017),))
def test_get_subsystems_from_database_with_empty_response(mocker, basic_args):
    basic_args.settings['xroad']['descriptor-path'] = ""
    basic_args.settings["mongodb"]["host"] = "emptymongo"

    basic_args.start_time_milliseconds = 2009459200000  # 2021-01-01T00:00:00Z
    basic_args.end_time_milliseconds = 2009545600000  # 2021-01-02T00:00:00Z

    database_manager = DatabaseManager(basic_args, mocker.Mock())

    xroad_descriptor = OpmonXroadDescriptor(basic_args, database_manager, mocker.Mock())
    assert xroad_descriptor._data == []


def get_test_documents():
    valid_timestamp = 1609502400000  # 2021-01-01T12:00:00Z
    old_timestamp = 1600000000000

    return [
        {
            'client': {
                'clientXRoadInstance': 'TEST',
                'clientMemberClass': 'TESTCLASS',
                'clientMemberCode': 'TESTMEMBER',
                'clientSubsystemCode': 'SUB1',
                'requestInTs': valid_timestamp
            }
        },
        {
            'client': {
                'clientXRoadInstance': 'TEST',
                'clientMemberClass': 'TESTCLASS',
                'clientMemberCode': 'TESTMEMBER2',
                'clientSubsystemCode': 'SUBA',
                'requestInTs': valid_timestamp
            }
        },
        {
            'client': {
                'serviceXRoadInstance': 'TEST',
                'serviceMemberClass': 'TESTCLASS2',
                'serviceMemberCode': 'TESTMEMBER3',
                'serviceSubsystemCode': 'TESTSUB',
                'requestInTs': valid_timestamp
            }
        },
        {
            'client': {
                # The timestamp for this query is not within the default arguments range
                'clientXRoadInstance': 'TEST',
                'clientMemberClass': 'TESTCLASS',
                'clientMemberCode': 'TESTMEMBER2',
                'clientSubsystemCode': 'OUTDATED',
                'requestInTs': old_timestamp
            }
        },
        {
            'client': {
                # This service subsystem is identical to a client subsystem above
                'serviceXRoadInstance': 'TEST',
                'serviceMemberClass': 'TESTCLASS',
                'serviceMemberCode': 'TESTMEMBER2',
                'serviceSubsystemCode': 'SUBA',
                'requestInTs': valid_timestamp
            },
        },
        {
            'client': {
                # Missing fields
                'serviceXRoadInstance': 'TEST',
                'serviceMemberClass': 'TESTCLASS3',
                'serviceMemberCode': 'TESTMEMBER3',
                'serviceSubsystemCode': None,
                'requestInTs': valid_timestamp
            },
        },
        {
            'client': {
                # Missing fields
                'serviceXRoadInstance': 'TEST',
                'serviceSubsystemCode': 'SUBD',
                'requestInTs': valid_timestamp
            },
        },
        # Empty document
        {}
    ]
