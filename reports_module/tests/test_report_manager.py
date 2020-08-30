import unittest

from reports_module.reportslib.report_manager import ReportManager
from reports_module.reportslib.report_row import ReportRow


class TestReportManager(unittest.TestCase):
    def test_is_producer_document(self):
        report_manager = ReportManager(None, None, None, None, "2017-01-01", "2017-01-01", None, None, None, None, None,
                                       None, None, None, None, None, None, None)
        document = dict()
        subsystem_code = "subsystem_code"
        member_code = "member_code"
        member_class = None
        x_road_instance = ""
        document["serviceSubsystemCode"] = subsystem_code
        document["serviceMemberCode"] = member_code
        document["serviceMemberClass"] = member_class
        document["serviceXRoadInstance"] = x_road_instance
        self.assertTrue(
            report_manager.is_producer_document(document, subsystem_code, member_code, member_class, x_road_instance))
        self.assertFalse(
            report_manager.is_producer_document(document, subsystem_code, subsystem_code, member_class,
                                                x_road_instance))
        self.assertFalse(
            report_manager.is_producer_document(document, subsystem_code, member_code, member_code, x_road_instance))
        self.assertFalse(
            report_manager.is_producer_document(document, subsystem_code, member_code, member_class, member_class))
        self.assertFalse(
            report_manager.is_producer_document(document, x_road_instance, member_code, member_class, x_road_instance))

    def test_is_client_document(self):
        report_manager = ReportManager(None, None, None, None, "2017-01-01", "2017-01-01", None, None, None, None, None,
                                       None, None, None, None, None, None, None)
        document = dict()
        subsystem_code = "subsystem_code"
        member_code = "member_code"
        member_class = None
        x_road_instance = ""
        document["clientSubsystemCode"] = subsystem_code
        document["clientMemberCode"] = member_code
        document["clientMemberClass"] = member_class
        document["clientXRoadInstance"] = x_road_instance
        self.assertTrue(
            report_manager.is_client_document(document, subsystem_code, member_code, member_class, x_road_instance))
        self.assertFalse(
            report_manager.is_client_document(document, subsystem_code, subsystem_code, member_class,
                                              x_road_instance))
        self.assertFalse(
            report_manager.is_client_document(document, subsystem_code, member_code, member_code, x_road_instance))
        self.assertFalse(
            report_manager.is_client_document(document, subsystem_code, member_code, member_class, member_class))
        self.assertFalse(
            report_manager.is_client_document(document, x_road_instance, member_code, member_class, x_road_instance))

    def test_reduce_to_plain_json(self):
        report_manager = ReportManager(None, None, None, None, "2017-01-01", "2017-01-01", None, None, None, None, None,
                                       None, None, None, None, None, None, None)
        subsystem_code = "subsystem_code"
        member_code = "member_code"
        member_class = None
        x_road_instance = ""

        inner_document = dict()
        inner_document["serviceSubsystemCode"] = subsystem_code
        inner_document["serviceMemberCode"] = member_code
        inner_document["serviceMemberClass"] = member_class
        inner_document["serviceXRoadInstance"] = x_road_instance
        inner_document["clientSubsystemCode"] = subsystem_code
        inner_document["clientMemberCode"] = member_code
        inner_document["clientMemberClass"] = member_class
        inner_document["clientXRoadInstance"] = x_road_instance

        document = dict()
        document['client'] = inner_document.copy()
        document['producer'] = inner_document.copy()
        doc = report_manager.reduce_to_plain_json(document)
        self.assertEqual(inner_document, doc)

        document = dict()
        document['client'] = None
        document['producer'] = inner_document.copy()
        doc = report_manager.reduce_to_plain_json(document)
        for key in list(inner_document.keys()):
            self.assertTrue(doc[key] == inner_document[key])

        document = dict()
        document['client'] = inner_document.copy()
        document['producer'] = None
        doc = report_manager.reduce_to_plain_json(document)
        for key in list(inner_document.keys()):
            self.assertTrue(doc[key] == inner_document[key])

        document = dict()
        document['client'] = None
        document['producer'] = None
        with self.assertRaises(TypeError):
            report_manager.reduce_to_plain_json(document)

    def test_get_service_type(self):
        report_manager_producer = ReportManager(
            "", None, "member_code", "subsystem_code", "2017-01-01", "2017-01-01", None, None, None, None, [], None,
            None, None, None, None, None, None)

        report_manager_producer_meta = ReportManager(
            "", None, "member_code", "subsystem_code", "2017-01-01", "2017-01-01", None, None, None, None, ["meta"],
            None, None, None, None, None, None, None)

        subsystem_code = "subsystem_code"
        member_code = "member_code"
        member_class = None
        x_road_instance = ""

        inner_document = dict()
        inner_document["serviceSubsystemCode"] = subsystem_code
        inner_document["serviceMemberCode"] = member_code
        inner_document["serviceMemberClass"] = member_class
        inner_document["serviceXRoadInstance"] = x_road_instance
        inner_document["clientSubsystemCode"] = "not_producer"
        inner_document["clientMemberCode"] = member_code
        inner_document["clientMemberClass"] = member_class
        inner_document["clientXRoadInstance"] = x_road_instance
        inner_document["serviceCode"] = "meta"

        service_type = report_manager_producer.get_service_type(inner_document)
        self.assertEqual(service_type, "ps")
        service_type = report_manager_producer_meta.get_service_type(inner_document)
        self.assertEqual(service_type, "pms")

        inner_document["serviceMemberCode"] = "not_client"
        inner_document["clientSubsystemCode"] = subsystem_code

        service_type = report_manager_producer.get_service_type(inner_document)
        self.assertEqual(service_type, "cs")
        service_type = report_manager_producer_meta.get_service_type(inner_document)
        self.assertEqual(service_type, "cms")

    def test_merge_document_fields(self):
        report_manager = ReportManager(None, None, None, None, "2017-01-01", "2017-01-01", None, None, None, None, None,
                                       None, None, None, None, None, None, None)

        subsystem_code = "subsystem_code"
        member_code = "member_code"
        member_class = None
        x_road_instance = ""
        service_version = "1.0"

        inner_document = dict()
        inner_document["serviceSubsystemCode"] = subsystem_code
        inner_document["serviceMemberCode"] = member_code
        inner_document["serviceMemberClass"] = member_class
        inner_document["serviceXRoadInstance"] = x_road_instance
        inner_document["serviceVersion"] = service_version

        merged_field = report_manager.merge_document_fields(
            inner_document, ["serviceSubsystemCode", "serviceMemberCode", "serviceMemberClass", "serviceXRoadInstance",
                             "serviceVersion"], "new_field", ".")
        self.assertEqual(merged_field, "subsystem_code.member_code.1.0")

    def test_get_min_mean_max(self):
        report_manager = ReportManager(None, None, None, None, "2017-01-01", "2017-01-01", None, None, None, None, None,
                                       None, None, None, None, None, None, None)
        self.assertEqual(report_manager.get_min_mean_max(5, (11, 2), 5), "5 / 6 / 5")
        self.assertEqual(report_manager.get_min_mean_max(-5, (-11, 2), -5), "-5 / -6 / -5")
        self.assertEqual(report_manager.get_min_mean_max(5.44235, (11.12412, 3.1253), 5.415123), "5 / 4 / 5")
        self.assertEqual(report_manager.get_min_mean_max(5.6, (11, 4), 5.6), "6 / 3 / 6")
        self.assertEqual(report_manager.get_min_mean_max(None, (11, 2), 5), "None / 6 / 5")
        self.assertEqual(report_manager.get_min_mean_max(None, (None, None), None), "None / None / None")

    def test_get_name_and_count(self):
        report_manager = ReportManager(None, None, None, "ss", "2017-01-01", "2017-01-01", None, None, None, None,
                                       None, None, None, None, None, None, None, None)
        key = "ee-dev"
        report_row = ReportRow(None)
        suc_queries = 10
        report_row.succeeded_queries = suc_queries
        produced_service = True
        service_name = "service"

        self.assertEqual(report_manager.get_name_and_count(key, report_row, produced_service, service_name),
                         ("ss: ee-dev", suc_queries))
        produced_service = False
        self.assertEqual(report_manager.get_name_and_count(key, report_row, produced_service, service_name),
                         ("ee-dev: service", suc_queries))

    def test_get_succeeded_top(self):
        report_manager = ReportManager(None, None, None, "ss", "2017-01-01", "2017-01-01", None, None, None, None,
                                       None, None, None, None, None, None, None, None)
        report_row = ReportRow(None)
        report_row.succeeded_queries = 10
        report_row_2 = ReportRow(None)
        report_row_2.succeeded_queries = 15
        report_row_3 = ReportRow(None)
        report_row_3.succeeded_queries = 7
        report_row_4 = ReportRow(None)
        report_row_4.succeeded_queries = 12
        report_row_5 = ReportRow(None)
        report_row_5.succeeded_queries = 13
        report_row_6 = ReportRow(None)
        report_row_6.succeeded_queries = 8
        report_row_7 = ReportRow(None)
        report_row_7.succeeded_queries = 11
        report_row_8 = ReportRow(None)
        report_row_8.succeeded_queries = 14
        report_row_9 = ReportRow(None)
        report_row_9.succeeded_queries = 9
        test_data = {
            "service_1": {
                "ee-dev": report_row,
                "ee-dev_2": report_row_2,
                "ee-dev_3": report_row_3
            },
            "service_2": {
                "ee-dev_4": report_row_7,
                "ee-dev_5": report_row_8,
                "ee-dev_6": report_row_9
            },
            "service_3": {
                "ee-dev_7": report_row_4,
                "ee-dev_8": report_row_5,
                "ee-dev_9": report_row_6
            },

        }

        self.assertEqual(report_manager.get_succeeded_top(test_data, True),
                         [("ss: service_3", 13), ("ss: service_2", 14), ("ss: service_1", 15)])
        self.assertEqual(report_manager.get_succeeded_top(test_data, False),
                         [("service_2: ee-dev_4", 11), ("service_3: ee-dev_7", 12), ("service_3: ee-dev_8", 13),
                          ("service_2: ee-dev_5", 14), ("service_1: ee-dev_2", 15)])

    def test_get_name_and_average(self):
        report_manager = ReportManager(None, None, None, "ss", "2017-01-01", "2017-01-01", None, None, None, None,
                                       None, None, None, None, None, None, None, None)
        key = "ee-dev"
        report_row = ReportRow(None)
        report_row.duration_avg = (5123.123, 15)
        produced_service = True
        service_name = "service"

        self.assertEqual(report_manager.get_name_and_average(key, report_row, produced_service, service_name),
                         ("ss: ee-dev", round(report_row.duration_avg[0] / (report_row.duration_avg[1]))))
        produced_service = False
        self.assertEqual(report_manager.get_name_and_average(key, report_row, produced_service, service_name),
                         ("ee-dev: service", round(report_row.duration_avg[0] / (report_row.duration_avg[1]))))
        report_row.duration_avg = (None, None)
        self.assertEqual(report_manager.get_name_and_average(key, report_row, produced_service, service_name),
                         ("ee-dev: service", None))

    def test_get_duration_top(self):
        report_manager = ReportManager(None, None, None, "ss", "2017-01-01", "2017-01-01", None, None, None, None,
                                       None, None, None, None, None, None, None, None)
        report_row = ReportRow(None)
        report_row.duration_avg = (100, 10)
        report_row_2 = ReportRow(None)
        report_row_2.duration_avg = (1000, 10)
        report_row_3 = ReportRow(None)
        report_row_3.duration_avg = (200, 10)
        report_row_4 = ReportRow(None)
        report_row_4.duration_avg = (109, 10)
        report_row_5 = ReportRow(None)
        report_row_5.duration_avg = (1100, 10)
        report_row_6 = ReportRow(None)
        report_row_6.duration_avg = (209, 10)
        report_row_7 = ReportRow(None)
        report_row_7.duration_avg = (90, 10)
        report_row_8 = ReportRow(None)
        report_row_8.duration_avg = (900, 10)
        report_row_9 = ReportRow(None)
        report_row_9.duration_avg = (190, 10)
        test_data = {
            "service_1": {
                "ee-dev": report_row,
                "ee-dev_2": report_row_2,
                "ee-dev_3": report_row_3
            },
            "service_2": {
                "ee-dev_4": report_row_7,
                "ee-dev_5": report_row_8,
                "ee-dev_6": report_row_9
            },
            "service_3": {
                "ee-dev_7": report_row_4,
                "ee-dev_8": report_row_5,
                "ee-dev_9": report_row_6
            },

        }

        self.assertEqual(report_manager.get_duration_top(test_data, True),
                         [("ss: service_2", 90), ("ss: service_1", 100), ("ss: service_3", 110)])
        self.assertEqual(report_manager.get_duration_top(test_data, False),
                         [("service_1: ee-dev_3", 20), ("service_3: ee-dev_9", 21), ("service_2: ee-dev_5", 90),
                          ("service_1: ee-dev_2", 100), ("service_3: ee-dev_8", 110)])

    def test_get_member_name(self):
        report_manager = ReportManager(None, None, None, None, "2017-01-01", "2017-01-01", None, None, None, None,
                                       None, None, None, None, None, None, None, None)
        member_code = "MemberCodeA"
        subsystem_code = "SubsystemCodeA"
        member_class = "MemberClassA"
        x_road_instance = "CI-REPORTS"
        member_name_dict = [
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

        member_name = report_manager.get_member_name(member_code, subsystem_code, member_class, x_road_instance,
                                                     member_name_dict)
        self.assertEqual(member_name, "Member Name")
        member_name_dict = None
        member_name = report_manager.get_member_name(member_code, subsystem_code, member_class, x_road_instance,
                                                     member_name_dict)
        self.assertEqual(member_name, "")

    def test_get_subsystem_name(self):
        report_manager = ReportManager(None, None, None, None, "2017-01-01", "2017-01-01", None, None, None, None,
                                       None, None, None, None, None, None, None, None)
        member_code = "MemberCodeA"
        subsystem_code = "SubsystemCodeA"
        member_class = "MemberClassA"
        x_road_instance = "CI-REPORTS"
        language = "et"
        member_name_dict = [
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

        member_name = report_manager.get_subsystem_name(member_code, subsystem_code, member_class, x_road_instance,
                                                        language, member_name_dict)
        self.assertEqual(member_name, "Subsystem Name ET")

        language = "en"
        member_name = report_manager.get_subsystem_name(member_code, subsystem_code, member_class, x_road_instance,
                                                        language, member_name_dict)
        self.assertEqual(member_name, "Subsystem Name EN")

        member_name_dict = None
        member_name = report_manager.get_subsystem_name(member_code, subsystem_code, member_class, x_road_instance,
                                                        language, member_name_dict)
        self.assertEqual(member_name, "")
