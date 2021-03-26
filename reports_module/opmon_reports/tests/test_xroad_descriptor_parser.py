from opmon_reports.xroad_descriptor_parser import OpmonXroadDescriptor
import os


def get_resource_path(resource_file_name):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        "resources",
        resource_file_name
    )


def test_xroad_descriptor_parsing_valid1(mocker):
    json_path = get_resource_path("xroad_descriptor_valid1.json")
    xroad_descriptor = OpmonXroadDescriptor(json_path, mocker.Mock())
    assert len(xroad_descriptor) == 6
    assert xroad_descriptor[0]['x_road_instance'] == "LTT"
    assert xroad_descriptor[0]['subsystem_name']['fi'] == "Testialijärjestelmä"
    assert xroad_descriptor[0]['email'][0]['name'] == "Seppo Sorsa"
    assert xroad_descriptor[0]['email'][1]['email'] == "teppo@testi.com"

    assert xroad_descriptor[1]['email'] == []
    assert xroad_descriptor[1].get('subsystem_name') is None

    assert xroad_descriptor[2].get('email') is None
    assert xroad_descriptor[2].get('subsystem_name') is None

    assert xroad_descriptor[5]['email'][0]['name'] == "Out of Place"

    xroad_descriptor.logger.log_warning.assert_not_called()
    xroad_descriptor.logger.log_error.assert_not_called()


def test_xroad_descriptor_parsing_valid2(mocker):
    json_path = get_resource_path("xroad_descriptor_valid2.json")
    xroad_descriptor = OpmonXroadDescriptor(json_path, mocker.Mock())

    xroad_descriptor.logger.log_warning.assert_not_called()
    xroad_descriptor.logger.log_error.assert_not_called()
    assert xroad_descriptor._data == []


def test_xroad_descriptor_parsing_not_json(mocker):
    json_path = get_resource_path("xroad_descriptor_not_json.json")
    xroad_descriptor = OpmonXroadDescriptor(json_path, mocker.Mock())

    xroad_descriptor.logger.log_warning.assert_called_once()
    assert "parsing failed" in xroad_descriptor.logger.log_warning.call_args.args[1]
    xroad_descriptor.logger.log_error.assert_not_called()
    assert xroad_descriptor._data == []


def test_xroad_descriptor_parsing_schema_fail(mocker):
    json_path = get_resource_path("xroad_descriptor_schema_fail.json")
    xroad_descriptor = OpmonXroadDescriptor(json_path, mocker.Mock())

    xroad_descriptor.logger.log_warning.assert_called_once()
    assert "parsing failed" in xroad_descriptor.logger.log_warning.call_args.args[1]
    xroad_descriptor.logger.log_error.assert_not_called()

    assert xroad_descriptor._data == []


def test_xroad_descriptor_parsing_file_not_found(mocker):
    xroad_descriptor = OpmonXroadDescriptor("/not/found.json", mocker.Mock())

    xroad_descriptor.logger.log_warning.assert_called_once()
    assert "not found" in xroad_descriptor.logger.log_warning.call_args.args[1]
    xroad_descriptor.logger.log_error.assert_not_called()

    assert xroad_descriptor._data == []


def test_iteration(mocker):
    json_path = get_resource_path("xroad_descriptor_valid1.json")
    xroad_descriptor = OpmonXroadDescriptor(json_path, mocker.Mock())

    for subsystem_descriptor in xroad_descriptor:
        assert subsystem_descriptor in xroad_descriptor._data


def test_getters(mocker):
    json_path = get_resource_path("xroad_descriptor_valid1.json")
    xroad_descriptor = OpmonXroadDescriptor(json_path, mocker.Mock())

    args = mocker.Mock()
    args.xroad_instance = "LTT"
    args.member_class = "TESTCLASS"
    args.member_code = "TESTMEMBER"
    args.subsystem_code = "TESTSUB"

    args.language = "fi"
    assert xroad_descriptor.get_subsystem_name(args) == "Testialijärjestelmä"

    args.language = "sv"
    assert xroad_descriptor.get_subsystem_name(args) == "Test Delsystem"

    args.language = "foobar"
    assert xroad_descriptor.get_subsystem_name(args) == "TESTSUB"

    emails = xroad_descriptor.get_emails(args)
    assert len(emails) == 2
    assert emails == [
        {'name': 'Seppo Sorsa', 'email': 'seppo.sorsa@gofore.com'},
        {'name': 'Teppo Testi', 'email': 'teppo@testi.com'}
    ]

    assert xroad_descriptor.get_member_name(args) == "Test Member Name"

    xroad_descriptor.logger.log_warning.assert_not_called()
    xroad_descriptor.logger.log_error.assert_not_called()


def test_getters_with_missing_fields(mocker):
    json_path = get_resource_path("xroad_descriptor_valid1.json")
    xroad_descriptor = OpmonXroadDescriptor(json_path, mocker.Mock())

    args = mocker.Mock()
    args.xroad_instance = "FOO"
    args.member_class = "TESTCLASS"
    args.member_code = "TESTMEMBER"
    args.subsystem_code = "MINIMALSUB"
    args.language = "foobar"

    assert xroad_descriptor.get_subsystem_name(args) == "MINIMALSUB"

    emails = xroad_descriptor.get_emails(args)
    assert emails == []

    assert xroad_descriptor.get_member_name(args) == "TESTMEMBER"

    xroad_descriptor.logger.log_warning.assert_not_called()
    xroad_descriptor.logger.log_error.assert_not_called()


def test_getters_with_missing_subsystem(mocker):
    json_path = get_resource_path("xroad_descriptor_valid1.json")
    xroad_descriptor = OpmonXroadDescriptor(json_path, mocker.Mock())

    args = mocker.Mock()
    args.xroad_instance = "FOO"
    args.member_class = "TESTCLASS"
    args.member_code = "TESTMEMBER"
    args.subsystem_code = "TESTSUB"
    args.language = "foobar"

    assert xroad_descriptor.get_subsystem_name(args) == "TESTSUB"

    emails = xroad_descriptor.get_emails(args)
    assert emails == []

    assert xroad_descriptor.get_member_name(args) == "TESTMEMBER"

    xroad_descriptor.logger.log_warning.assert_not_called()
    xroad_descriptor.logger.log_error.assert_not_called()
