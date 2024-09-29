import os

import pytest
from copy import copy
import tempfile

from opmon_reports.report_manager import ReportManager
from opmon_reports.report_manager import ReportRow
from opmon_reports.report_row import AverageValue
from opmon_reports.xroad_descriptor import OpmonXroadSubsystemDescriptor


@pytest.fixture()
def basic_args(mocker):
    args = mocker.Mock()
    args.start_date = "2017-01-01"
    args.end_date = "2017-01-01"
    args.language = "en"
    args.settings = {
        'reports': {
        }
    }

    return args


@pytest.fixture()
def target_subsystem():
    return OpmonXroadSubsystemDescriptor({
        'subsystem_code': "TEST_SUB",
        'member_code': "TEST_MEMBER",
        'member_class': "TEST_CLASS",
        'x_road_instance': "TEST_INSTANCE"
    })


@pytest.fixture()
def basic_document(target_subsystem):
    return {
        "serviceSubsystemCode": target_subsystem.subsystem_code,
        "serviceMemberCode": target_subsystem.member_code,
        "serviceMemberClass": target_subsystem.member_class,
        "serviceXRoadInstance": target_subsystem.xroad_instance,

        "clientSubsystemCode": target_subsystem.subsystem_code,
        "clientMemberCode": target_subsystem.member_code,
        "clientMemberClass": target_subsystem.member_class,
        "clientXRoadInstance": target_subsystem.xroad_instance,
    }


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


class UnitTestAverageValue(AverageValue):
    def __init__(self, sum, count):
        super().__init__()
        self.sum = sum
        self.count = count


def map_rows_to_producer_services(rows):
    return {
        "service_1": {
            "SUB1": rows[0],
            "SUB2": rows[1],
            "SUB3": rows[2]
        },
        "service_2": {
            "SUB1": rows[6],
            "SUB2": rows[7],
            "SUB3": rows[8]
        },
        "service_3": {
            "SUB1": rows[3],
            "SUB2": rows[4],
            "SUB3": rows[5]
        },
    }


def map_rows_to_consumer_services(rows):
    return {
        "SUB1": {
            "service1": rows[0],
            "service2": rows[1],
            "service3": rows[2]
        },
        "SUB2": {
            "service1": rows[6],
            "service2": rows[7],
            "service3": rows[8]
        },
        "SUB3": {
            "service1": rows[3],
            "service2": rows[4],
            "service3": rows[5]
        },
    }


def test_is_producer_document(mocker, basic_args, target_subsystem, basic_document):
    report_manager = ReportManager(basic_args, target_subsystem, mocker.Mock(), mocker.Mock(), mocker.Mock())

    assert report_manager.is_producer_document(basic_document)

    for key in ["serviceSubsystemCode", "serviceMemberCode", "serviceMemberClass", "serviceXRoadInstance"]:
        invalid_document = copy(basic_document)
        invalid_document[key] = "foo"
        assert not report_manager.is_producer_document(invalid_document)


def test_is_client_document(mocker, basic_args, target_subsystem, basic_document):
    report_manager = ReportManager(basic_args, target_subsystem, mocker.Mock(), mocker.Mock(), mocker.Mock())

    assert report_manager.is_client_document(basic_document)

    for key in ["clientSubsystemCode", "clientMemberCode", "clientMemberClass", "clientXRoadInstance"]:
        invalid_document = copy(basic_document)
        invalid_document[key] = "foo"
        assert not report_manager.is_client_document(invalid_document)


def test_reduce_to_plain_json(mocker, basic_args, target_subsystem, basic_document):
    report_manager = ReportManager(basic_args, target_subsystem, mocker.Mock(), mocker.Mock(), mocker.Mock())

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


def test_get_service_type(mocker, basic_args, target_subsystem, basic_document):
    report_manager = ReportManager(basic_args, target_subsystem, mocker.Mock(), mocker.Mock(), mocker.Mock())

    basic_document["clientSubsystemCode"] = "not_producer"
    basic_document["serviceCode"] = "getWsdl"
    assert report_manager.get_service_type(basic_document) == "pms"

    basic_document["serviceCode"] = "FOOBAR"
    assert report_manager.get_service_type(basic_document) == "ps"

    basic_document["clientSubsystemCode"] = target_subsystem.subsystem_code
    basic_document["serviceSubsystemCode"] = "not_client"
    basic_document["serviceCode"] = "getWsdl"
    assert report_manager.get_service_type(basic_document) == "cms"

    basic_document["serviceCode"] = "FOOBAR"
    assert report_manager.get_service_type(basic_document) == "cs"


def test_merge_document_fields(mocker, basic_args, target_subsystem, basic_document):
    report_manager = ReportManager(basic_args, target_subsystem, mocker.Mock(), mocker.Mock(), mocker.Mock())

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
    assert ReportManager.get_min_mean_max(5, UnitTestAverageValue(11, 2), 5) == "5 / 6 / 5"
    assert ReportManager.get_min_mean_max(-5, UnitTestAverageValue(-11, 2), -5) == "-5 / -6 / -5"
    assert ReportManager.get_min_mean_max(5.44235, UnitTestAverageValue(11.12412, 3.1253), 5.415123) == "5 / 4 / 5"
    assert ReportManager.get_min_mean_max(5.6, UnitTestAverageValue(11, 4), 5.6) == "6 / 3 / 6"
    assert ReportManager.get_min_mean_max(None, UnitTestAverageValue(11, 2), 5) == "None / 6 / 5"
    assert ReportManager.get_min_mean_max(None, AverageValue(), None) == "None / None / None"


def test_get_succeeded_top(mocker, basic_args, target_subsystem):
    report_manager = ReportManager(basic_args, target_subsystem, mocker.Mock(), mocker.Mock(), mocker.Mock())

    rows = [ReportRow(None) for _ in range(9)]
    success_counts = [10, 15, 7, 14, 13, 8, 11, 12, 9]

    for row, success_count in zip(rows, success_counts):
        row.succeeded_queries = success_count

    test_data = map_rows_to_producer_services(rows)
    succeeded_top = report_manager.get_succeeded_top(test_data, produced_service=True)
    assert succeeded_top == [
        ('TEST_SUB: service_2', 12),
        ('TEST_SUB: service_3', 14),
        ('TEST_SUB: service_1', 15)
    ]

    test_data = map_rows_to_consumer_services(rows)
    succeeded_top = report_manager.get_succeeded_top(test_data, produced_service=False)
    assert succeeded_top == [
        ('SUB2: service1', 11),
        ('SUB2: service2', 12),
        ('SUB3: service2', 13),
        ('SUB3: service1', 14),
        ('SUB1: service2', 15)
    ]


def test_get_duration(mocker, basic_args, target_subsystem):
    report_manager = ReportManager(basic_args, target_subsystem, mocker.Mock(), mocker.Mock(), mocker.Mock())

    rows = [ReportRow(None) for _ in range(9)]
    duration_avgs = [
        UnitTestAverageValue(100, 10),
        UnitTestAverageValue(1000, 10),
        UnitTestAverageValue(200, 10),
        UnitTestAverageValue(109, 10),
        UnitTestAverageValue(1100, 10),
        UnitTestAverageValue(209, 10),
        UnitTestAverageValue(90, 10),
        UnitTestAverageValue(900, 10),
        UnitTestAverageValue(190, 10)
    ]

    for row, duration_avg in zip(rows, duration_avgs):
        row.duration_avg = duration_avg

    test_data = map_rows_to_producer_services(rows)
    duration_top = report_manager.get_duration_top(test_data, produced_service=True)
    assert duration_top == [
        ('TEST_SUB: service_2', 90),
        ('TEST_SUB: service_1', 100),
        ('TEST_SUB: service_3', 110)
    ]

    test_data = map_rows_to_consumer_services(rows)
    duration_top = report_manager.get_duration_top(test_data, produced_service=False)
    assert duration_top == [
        ('SUB1: service3', 20),
        ('SUB3: service3', 21),
        ('SUB2: service2', 90),
        ('SUB1: service2', 100),
        ('SUB3: service2', 110)
    ]


def test_generate_report_tempfolder(mocker, basic_args, target_subsystem):
    report_manager = ReportManager(basic_args, target_subsystem, mocker.Mock(), mocker.Mock(), mocker.Mock())

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
