import os

import pytest
from copy import copy
import tempfile

from opmon_reports.report_manager import ReportManager
from opmon_reports.report_manager import ReportRow


@pytest.fixture()
def basic_args(mocker):
    args = mocker.Mock()
    args.start_date = "2017-01-01"
    args.end_date = "2017-01-01"

    args.subsystem_code = "TEST_SUB"
    args.member_code = "TEST_MEMBER"
    args.member_class = "TEST_CLASS"
    args.xroad_instance = "TEST_INSTANCE"
    args.language = "en"

    return args


@pytest.fixture()
def basic_document(basic_args):
    document = dict()

    document["serviceSubsystemCode"] = basic_args.subsystem_code
    document["serviceMemberCode"] = basic_args.member_code
    document["serviceMemberClass"] = basic_args.member_class
    document["serviceXRoadInstance"] = basic_args.xroad_instance

    document["clientSubsystemCode"] = basic_args.subsystem_code
    document["clientMemberCode"] = basic_args.member_code
    document["clientMemberClass"] = basic_args.member_class
    document["clientXRoadInstance"] = basic_args.xroad_instance

    return document


@pytest.fixture()
def member_names():
    return [
        {
            "x_road_instance": "CI-REPORTS",
            "subsystem_name": {
                "et": "Subsystem Name ET",
                "en": "Subsystem Name EN"
            },
            "member_class": "MemberClassA",
            "email": [],
            "subsystem_code": "SubsystemCodeA",
            "member_code": "MemberCodeA",
            "member_name": "Member Name"
        }
    ]


def map_rows_to_test_services(rows):
    return {
        "service_1": {
            "ee-dev_0": rows[0],
            "ee-dev_1": rows[1],
            "ee-dev_2": rows[2]
        },
        "service_2": {
            "ee-dev_3": rows[6],
            "ee-dev_4": rows[7],
            "ee-dev_5": rows[8]
        },
        "service_3": {
            "ee-dev_6": rows[3],
            "ee-dev_7": rows[4],
            "ee-dev_8": rows[5]
        },
    }


def test_is_producer_document(mocker, basic_args, basic_document):
    report_manager = ReportManager(basic_args, mocker.Mock(), mocker.Mock(), mocker.Mock(), mocker.Mock())

    assert report_manager.is_producer_document(basic_document)

    for key in ["serviceSubsystemCode", "serviceMemberCode", "serviceMemberClass", "serviceXRoadInstance"]:
        invalid_document = copy(basic_document)
        invalid_document[key] = "foo"
        assert not report_manager.is_producer_document(invalid_document)


def test_is_client_document(mocker, basic_args, basic_document):
    report_manager = ReportManager(basic_args, mocker.Mock(), mocker.Mock(), mocker.Mock(), mocker.Mock())

    assert report_manager.is_client_document(basic_document)

    for key in ["clientSubsystemCode", "clientMemberCode", "clientMemberClass", "clientXRoadInstance"]:
        invalid_document = copy(basic_document)
        invalid_document[key] = "foo"
        assert not report_manager.is_client_document(invalid_document)


def test_reduce_to_plain_json(mocker, basic_args, basic_document):
    report_manager = ReportManager(basic_args, mocker.Mock(), mocker.Mock(), mocker.Mock(), mocker.Mock())

    document = dict()
    document['client'] = basic_document.copy()
    document['producer'] = basic_document.copy()

    reduced_document = report_manager.reduce_to_plain_json(document)
    assert basic_document == reduced_document

    document = dict()
    document['client'] = None
    document['producer'] = basic_document.copy()
    reduced_document = report_manager.reduce_to_plain_json(document)
    for key in list(basic_document.keys()):
        assert reduced_document[key] == basic_document[key]

    document = dict()
    document['client'] = basic_document.copy()
    document['producer'] = None
    reduced_document = report_manager.reduce_to_plain_json(document)
    for key in list(basic_document.keys()):
        assert reduced_document[key] == basic_document[key]

    document = dict()
    document['client'] = None
    document['producer'] = None
    with pytest.raises(TypeError):
        report_manager.reduce_to_plain_json(document)


def test_get_service_type(mocker, basic_args, basic_document):
    report_manager = ReportManager(basic_args, mocker.Mock(), mocker.Mock(), mocker.Mock(), mocker.Mock())

    basic_document["clientSubsystemCode"] = "not_producer"
    basic_document["serviceCode"] = "getWsdl"
    assert report_manager.get_service_type(basic_document) == "pms"

    basic_document["serviceCode"] = "FOOBAR"
    assert report_manager.get_service_type(basic_document) == "ps"

    basic_document["clientSubsystemCode"] = basic_args.subsystem_code
    basic_document["serviceSubsystemCode"] = "not_client"
    basic_document["serviceCode"] = "getWsdl"
    assert report_manager.get_service_type(basic_document) == "cms"

    basic_document["serviceCode"] = "FOOBAR"
    assert report_manager.get_service_type(basic_document) == "cs"


def test_merge_document_fields(mocker, basic_args, basic_document):
    report_manager = ReportManager(basic_args, mocker.Mock(), mocker.Mock(), mocker.Mock(), mocker.Mock())

    basic_document["serviceVersion"] = "1.0"
    basic_document["serviceMemberClass"] = ""
    basic_document["serviceXRoadInstance"] = None

    fields_to_merge = [
        "serviceSubsystemCode",
        "serviceMemberCode",
        "serviceMemberClass",
        "serviceXRoadInstance",
        "serviceVersion"
    ]

    merged_field = report_manager.merge_document_fields(basic_document, fields_to_merge, "new_field", ".")
    assert merged_field == "TEST_SUB.TEST_MEMBER.1.0"


def test_get_min_mean_max():
    assert ReportManager.get_min_mean_max(5, (11, 2), 5) == "5 / 6 / 5"
    assert ReportManager.get_min_mean_max(-5, (-11, 2), -5) == "-5 / -6 / -5"
    assert ReportManager.get_min_mean_max(5.44235, (11.12412, 3.1253), 5.415123) == "5 / 4 / 5"
    assert ReportManager.get_min_mean_max(5.6, (11, 4), 5.6) == "6 / 3 / 6"
    assert ReportManager.get_min_mean_max(None, (11, 2), 5) == "None / 6 / 5"
    assert ReportManager.get_min_mean_max(None, (None, None), None) == "None / None / None"


def test_get_name_and_count(mocker, basic_args):
    report_manager = ReportManager(basic_args, mocker.Mock(), mocker.Mock(), mocker.Mock(), mocker.Mock())

    key = "ee-dev"
    report_row = ReportRow(None)
    suc_queries = 10
    report_row.succeeded_queries = suc_queries
    produced_service = True
    service_name = "service"

    name_and_count = report_manager.get_name_and_count(key, report_row, produced_service, service_name)
    assert name_and_count == ("TEST_SUB: ee-dev", suc_queries)

    produced_service = False
    name_and_count = report_manager.get_name_and_count(key, report_row, produced_service, service_name)
    assert name_and_count == ("ee-dev: service", suc_queries)


def test_get_succeeded_top(mocker, basic_args):
    report_manager = ReportManager(basic_args, mocker.Mock(), mocker.Mock(), mocker.Mock(), mocker.Mock())

    rows = [ReportRow(None) for _ in range(9)]
    success_counts = [10, 15, 7, 12, 13, 8, 11, 14, 9]

    for row, success_count in zip(rows, success_counts):
        row.succeeded_queries = success_count

    test_data = map_rows_to_test_services(rows)

    succeeded_top = report_manager.get_succeeded_top(test_data, produced_service=True)
    assert succeeded_top == [
        ("TEST_SUB: service_3", 13),
        ("TEST_SUB: service_2", 14),
        ("TEST_SUB: service_1", 15)
    ]

    succeeded_top = report_manager.get_succeeded_top(test_data, produced_service=False)
    assert succeeded_top == [
        ("service_2: ee-dev_3", 11),
        ("service_3: ee-dev_6", 12),
        ("service_3: ee-dev_7", 13),
        ("service_2: ee-dev_4", 14),
        ("service_1: ee-dev_1", 15)
    ]


def test_get_name_and_average(mocker, basic_args):
    report_manager = ReportManager(basic_args, mocker.Mock(), mocker.Mock(), mocker.Mock(), mocker.Mock())
    key = "ee-dev"
    report_row = ReportRow(None)
    report_row.duration_avg = (5123.123, 15)
    produced_service = True
    service_name = "service"

    name_and_average = report_manager.get_name_and_average(key, report_row, produced_service, service_name)
    assert name_and_average == ("TEST_SUB: ee-dev", round(report_row.duration_avg[0] / (report_row.duration_avg[1])))

    produced_service = False
    name_and_average = report_manager.get_name_and_average(key, report_row, produced_service, service_name)
    assert name_and_average == ("ee-dev: service", round(report_row.duration_avg[0] / (report_row.duration_avg[1])))

    report_row.duration_avg = (None, None)
    name_and_average = report_manager.get_name_and_average(key, report_row, produced_service, service_name)
    assert name_and_average == ("ee-dev: service", None)


def test_get_duration(mocker, basic_args):
    report_manager = ReportManager(basic_args, mocker.Mock(), mocker.Mock(), mocker.Mock(), mocker.Mock())

    rows = [ReportRow(None) for _ in range(9)]
    duration_avgs = [
        (100, 10),
        (1000, 10),
        (200, 10),
        (109, 10),
        (1100, 10),
        (209, 10),
        (90, 10),
        (900, 10),
        (190, 10)
    ]

    for row, duration_avg in zip(rows, duration_avgs):
        row.duration_avg = duration_avg

    test_data = map_rows_to_test_services(rows)

    duration_top = report_manager.get_duration_top(test_data, produced_service=True)
    assert duration_top == [("TEST_SUB: service_2", 90), ("TEST_SUB: service_1", 100), ("TEST_SUB: service_3", 110)]

    duration_top = report_manager.get_duration_top(test_data, produced_service=False)
    assert duration_top == [
        ("service_1: ee-dev_2", 20),
        ("service_3: ee-dev_8", 21),
        ("service_2: ee-dev_4", 90),
        ("service_1: ee-dev_1", 100),
        ("service_3: ee-dev_7", 110)
    ]


def test_get_member_name(mocker, basic_args, member_names):
    report_manager = ReportManager(basic_args, mocker.Mock(), mocker.Mock(), mocker.Mock(), mocker.Mock())

    basic_args.member_code = "MemberCodeA"
    basic_args.subsystem_code = "SubsystemCodeA"
    basic_args.member_class = "MemberClassA"
    basic_args.xroad_instance = "CI-REPORTS"

    member_name = report_manager.get_member_name(member_names)
    assert member_name == "Member Name"

    member_names = []
    member_name = report_manager.get_member_name(member_names)
    assert member_name == ""

    member_names = None
    member_name = report_manager.get_member_name(member_names)
    assert member_name == ""


def test_get_subsystem_name(mocker, basic_args, member_names):
    report_manager = ReportManager(basic_args, mocker.Mock(), mocker.Mock(), mocker.Mock(), mocker.Mock())

    basic_args.member_code = "MemberCodeA"
    basic_args.subsystem_code = "SubsystemCodeA"
    basic_args.member_class = "MemberClassA"
    basic_args.xroad_instance = "CI-REPORTS"

    member_name = report_manager.get_subsystem_name(member_names)
    assert member_name == "Subsystem Name EN"

    basic_args.language = "et"
    member_name = report_manager.get_subsystem_name(member_names)
    assert member_name == "Subsystem Name ET"

    member_names = []
    member_name = report_manager.get_subsystem_name(member_names)
    assert member_name == ""

    member_names = None
    member_name = report_manager.get_subsystem_name(member_names)
    assert member_name == ""


def test_generate_report_tempfolder(mocker, basic_args):
    report_manager = ReportManager(basic_args, mocker.Mock(), mocker.Mock(), mocker.Mock(), mocker.Mock())

    mocker.patch('opmon_reports.report_manager.ReportManager.get_documents', return_value={})
    mocker.patch('opmon_reports.report_manager.ReportManager.create_data_frames', return_value=[])
    mocker.patch('opmon_reports.report_manager.ReportManager.create_plots', return_value=(None, None, None, None))
    mocker.patch('opmon_reports.report_manager.ReportManager.prepare_template', return_value=mocker.Mock())
    mocker.patch('opmon_reports.report_manager.ReportManager.save_pdf_to_file', return_value="test report")

    tempdir_spy = mocker.spy(tempfile, "TemporaryDirectory")

    assert report_manager.generate_report() == "test report"
    tempdir_spy.assert_called_once()

    tempdir = tempdir_spy.spy_return.name

    assert "opmon-reports" in tempdir
    assert not os.path.exists(tempdir)
