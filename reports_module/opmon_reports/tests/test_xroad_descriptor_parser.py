import pytest

from opmon_reports.xroad_descriptor_parser import OpmonXroadDescriptor, OpmonXroadSubsystemDescriptor
import os


@pytest.fixture
def basic_args(mocker):
    args = mocker.Mock()
    args.settings = {
        "xroad": {"descriptor-path": ""}
    }

    args.subsystem = None

    return args


def get_resource_path(resource_file_name):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "resources",
        resource_file_name
    )


def test_xroad_descriptor_parsing_valid1(mocker, basic_args):
    basic_args.settings['xroad']['descriptor-path'] = get_resource_path("xroad_descriptor_valid1.json")
    xroad_descriptor = OpmonXroadDescriptor(basic_args, mocker.Mock())
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


def test_xroad_descriptor_parsing_valid2(mocker, basic_args):
    basic_args.settings['xroad']['descriptor-path'] = get_resource_path("xroad_descriptor_valid2.json")
    xroad_descriptor = OpmonXroadDescriptor(basic_args, mocker.Mock())

    xroad_descriptor.logger.log_warning.assert_not_called()
    xroad_descriptor.logger.log_error.assert_not_called()
    assert xroad_descriptor._data == []


def test_xroad_descriptor_parsing_not_json(mocker, basic_args):
    basic_args.settings['xroad']['descriptor-path'] = get_resource_path("xroad_descriptor_not_json.json")
    xroad_descriptor = OpmonXroadDescriptor(basic_args, mocker.Mock())

    xroad_descriptor.logger.log_warning.assert_called_once()
    assert "parsing failed" in xroad_descriptor.logger.log_warning.call_args.args[1]
    xroad_descriptor.logger.log_error.assert_not_called()
    assert xroad_descriptor._data == []


def test_xroad_descriptor_parsing_schema_fail(mocker, basic_args):
    basic_args.settings['xroad']['descriptor-path'] = get_resource_path("xroad_descriptor_schema_fail.json")
    xroad_descriptor = OpmonXroadDescriptor(basic_args, mocker.Mock())

    xroad_descriptor.logger.log_warning.assert_called_once()
    assert "parsing failed" in xroad_descriptor.logger.log_warning.call_args.args[1]
    xroad_descriptor.logger.log_error.assert_not_called()

    assert xroad_descriptor._data == []


def test_xroad_descriptor_parsing_file_not_found(mocker, basic_args):
    basic_args.settings['xroad']['descriptor-path'] = "/not/found.json"
    xroad_descriptor = OpmonXroadDescriptor(basic_args, mocker.Mock())

    xroad_descriptor.logger.log_warning.assert_called_once()
    assert "not found" in xroad_descriptor.logger.log_warning.call_args.args[1]
    xroad_descriptor.logger.log_error.assert_not_called()

    assert xroad_descriptor._data == []


def test_iteration(mocker, basic_args):
    basic_args.settings['xroad']['descriptor-path'] = get_resource_path("xroad_descriptor_valid1.json")
    xroad_descriptor = OpmonXroadDescriptor(basic_args, mocker.Mock())

    for subsystem_descriptor in xroad_descriptor:
        assert isinstance(subsystem_descriptor, OpmonXroadSubsystemDescriptor)
        assert subsystem_descriptor._data in xroad_descriptor._data


def test_subsystem_descriptor_getters(mocker, basic_args):
    basic_args.settings['xroad']['descriptor-path'] = get_resource_path("xroad_descriptor_valid1.json")
    xroad_descriptor = OpmonXroadDescriptor(basic_args, mocker.Mock())

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
    xroad_descriptor = OpmonXroadDescriptor(basic_args, mocker.Mock())

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
    xroad_descriptor = OpmonXroadDescriptor(basic_args, mocker.Mock())

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
    xroad_descriptor = OpmonXroadDescriptor(basic_args, mocker.Mock())

    assert len(xroad_descriptor) == 1
    assert xroad_descriptor[0].get_subsystem_name('en') == "SUB4"
