import json
import random
import unittest
from unittest.mock import MagicMock

from integration_tests.ci_reports.ci_reports_settings import Settings
from integration_tests.helpers import ci_helper
from integration_tests.helpers.cl_db_handler import MongoDBHandler
from reports_module.reportslib.database_manager import DatabaseManager
from reports_module.reportslib.report_manager import ReportManager
from reports_module.reportslib.time_date_tools import date_to_timestamp_milliseconds
from reports_module.reportslib.time_date_tools import string_to_date
from reports_module.reportslib.translator import Translator

random.seed(42)


class TestReportWorkerCI(unittest.TestCase):
    # @unittest.skip("demonstrating skipping")
    def test_get_matching_documents(self):
        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_get_matching_documents')
        mongodb_h = MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()

        log_manager = MagicMock()
        db_manager = DatabaseManager(mongodb_h, log_manager)

        start_time = "2017-06-01"
        end_time = "2017-07-01"
        start_timestamp = date_to_timestamp_milliseconds(string_to_date(start_time))
        end_timestamp = date_to_timestamp_milliseconds(string_to_date(end_time), start_date=False)

        total_random_count = 100
        total_ref_count = 20

        docs = []
        for i in range(total_random_count):
            doc_random_machine = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                                 end_request_in_ts=end_timestamp,
                                                                 force_random_machine=True)
            docs.append(doc_random_machine)

        # Test machine code to be used as producer
        test_machine = ("CI-CORRECTOR", "MemberClassA", "MemberCodeA", "SubsystemCodeA")

        for i in range(total_ref_count):
            doc_test_machine = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                               end_request_in_ts=end_timestamp,
                                                               specify_producer_machine=test_machine)
            docs.append(doc_test_machine)

        mongodb_h.add_clean_documents(docs)

        matching_docs = []
        # member_code, subsystem_code, member_class, x_road_instance, start_time_timestamp, end_time_timestamp
        for doc in db_manager.get_matching_documents(test_machine[2], test_machine[3], test_machine[1],
                                                     test_machine[0], start_timestamp, end_timestamp):
            matching_docs.append(doc)
        self.assertEqual(len(matching_docs), 20)

        # Clean before exit
        mongodb_h.remove_all()

    # @unittest.skip("demonstrating skipping")
    def test_get_matching_documents_different_cases(self):
        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_get_matching_documents_different_cases')
        mongodb_h = MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()

        log_manager = MagicMock()
        db_manager = DatabaseManager(mongodb_h, log_manager)

        start_time = "2017-06-01"
        end_time = "2017-07-01"
        start_timestamp = date_to_timestamp_milliseconds(string_to_date(start_time))
        end_timestamp = date_to_timestamp_milliseconds(string_to_date(end_time), start_date=False)

        total_random_count = 50
        docs = []
        for i in range(total_random_count):
            doc_random_machine = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                                 end_request_in_ts=end_timestamp,
                                                                 force_random_machine=True)
            docs.append(doc_random_machine)

        # Case Producer
        docs = []
        total_ref_count = 10
        test_machine = ("CI-CORRECTOR", "MemberClassA", "MemberCodeA", "SubsystemCodeA")
        for i in range(total_ref_count):
            doc_test_machine = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                               end_request_in_ts=end_timestamp,
                                                               specify_producer_machine=test_machine)
            docs.append(doc_test_machine)
        mongodb_h.add_clean_documents(docs)
        # member_code, subsystem_code, member_class, x_road_instance, start_time_timestamp, end_time_timestamp
        matching_docs = []
        for doc in db_manager.get_matching_documents(test_machine[2], test_machine[3], test_machine[1],
                                                     test_machine[0], start_timestamp, end_timestamp):
            matching_docs.append(doc)
        self.assertEqual(len(matching_docs), total_ref_count)

        # Case Producer without producer
        docs = []
        total_ref_count = 15
        test_machine = ("CI-CORRECTOR", "MemberClassA", "MemberCodeA", "SubsystemCodeB")
        for i in range(total_ref_count):
            doc_test_machine = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                               end_request_in_ts=end_timestamp,
                                                               specify_producer_machine=test_machine)
            doc_test_machine['producer'] = None
            docs.append(doc_test_machine)
        mongodb_h.add_clean_documents(docs)
        # member_code, subsystem_code, member_class, x_road_instance, start_time_timestamp, end_time_timestamp
        matching_docs = []
        for doc in db_manager.get_matching_documents(test_machine[2], test_machine[3], test_machine[1],
                                                     test_machine[0], start_timestamp, end_timestamp):
            matching_docs.append(doc)
        self.assertEqual(len(matching_docs), total_ref_count)

        # Case Client
        docs = []
        total_ref_count = 20
        test_machine = ("CI-CORRECTOR", "MemberClassA", "MemberCodeA", "SubsystemCodeC")
        for i in range(total_ref_count):
            doc_test_machine = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                               end_request_in_ts=end_timestamp,
                                                               specify_client_machine=test_machine)
            docs.append(doc_test_machine)
        mongodb_h.add_clean_documents(docs)
        # member_code, subsystem_code, member_class, x_road_instance, start_time_timestamp, end_time_timestamp
        matching_docs = []
        for doc in db_manager.get_matching_documents(test_machine[2], test_machine[3], test_machine[1],
                                                     test_machine[0], start_timestamp, end_timestamp):
            matching_docs.append(doc)
        self.assertEqual(len(matching_docs), total_ref_count)

        # Case client without client
        docs = []
        total_ref_count = 25
        test_machine = ("CI-CORRECTOR", "MemberClassA", "MemberCodeA", "SubsystemCodeD")
        for i in range(total_ref_count):
            doc_test_machine = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                               end_request_in_ts=end_timestamp,
                                                               specify_client_machine=test_machine)
            doc_test_machine['client'] = None
            docs.append(doc_test_machine)
        mongodb_h.add_clean_documents(docs)
        # member_code, subsystem_code, member_class, x_road_instance, start_time_timestamp, end_time_timestamp
        matching_docs = []
        for doc in db_manager.get_matching_documents(test_machine[2], test_machine[3], test_machine[1],
                                                     test_machine[0], start_timestamp, end_timestamp):
            matching_docs.append(doc)
        self.assertEqual(len(matching_docs), total_ref_count)

        # Case same producer and client
        docs = []
        total_ref_count = 30
        test_machine = ("CI-CORRECTOR", "MemberClassA", "MemberCodeA", "SubsystemCodeE")
        for i in range(total_ref_count):
            doc_test_machine = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                               end_request_in_ts=end_timestamp,
                                                               specify_client_machine=test_machine,
                                                               specify_producer_machine=test_machine)
            docs.append(doc_test_machine)
        mongodb_h.add_clean_documents(docs)

        # Query faulty documents
        faulty_doc_set = db_manager.get_faulty_documents(
            test_machine[2], test_machine[3], test_machine[1],
            test_machine[0], start_timestamp, end_timestamp)
        faulty_docs_found = set()

        # member_code, subsystem_code, member_class, x_road_instance, start_time_timestamp, end_time_timestamp
        matching_docs = []
        for doc in db_manager.get_matching_documents(test_machine[2], test_machine[3], test_machine[1],
                                                     test_machine[0], start_timestamp, end_timestamp):

            if doc['_id'] in faulty_docs_found:
                continue
            if doc['_id'] in faulty_doc_set:
                faulty_docs_found.add(doc['_id'])
            matching_docs.append(doc)

        self.assertEqual(len(matching_docs), total_ref_count)

        # Clean before exit
        mongodb_h.remove_all()

    # @unittest.skip("demonstrating skipping")
    def test_get_matching_documents_within_timestamp(self):
        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_get_matching_documents_within_timestamp')
        mongodb_h = MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()

        log_manager = MagicMock()
        db_manager = DatabaseManager(mongodb_h, log_manager)

        total_random_count = 100
        total_ref_before_count = 10
        total_ref_within_count = 20
        total_ref_after_count = 30

        # Test Time
        # |---------------|-----------------|---------------|
        # T1             T2                 T3              T4
        #       Before           Within            After
        t1 = date_to_timestamp_milliseconds(string_to_date("2017-01-01"))
        t2 = date_to_timestamp_milliseconds(string_to_date("2017-02-01"))
        t3 = date_to_timestamp_milliseconds(string_to_date("2017-03-01"))
        t4 = date_to_timestamp_milliseconds(string_to_date("2017-04-01"))

        # Docs random
        docs = []
        for i in range(total_random_count):
            doc_random_machine = ci_helper.create_clean_document(start_request_in_ts=t1,
                                                                 end_request_in_ts=t4,
                                                                 force_random_machine=True)
            docs.append(doc_random_machine)

        # Test machine code to be used as producer
        test_machine = ("CI-CORRECTOR", "MemberClassA", "MemberCodeA", "SubsystemCodeA")
        # Docs before
        for i in range(total_ref_before_count):
            doc_test_machine = ci_helper.create_clean_document(start_request_in_ts=t1,
                                                               end_request_in_ts=t2,
                                                               specify_producer_machine=test_machine)
            docs.append(doc_test_machine)
        # Docs within
        for i in range(total_ref_within_count):
            doc_test_machine = ci_helper.create_clean_document(start_request_in_ts=t2,
                                                               end_request_in_ts=t3,
                                                               specify_producer_machine=test_machine)
            docs.append(doc_test_machine)
        # Docs after
        for i in range(total_ref_after_count):
            doc_test_machine = ci_helper.create_clean_document(start_request_in_ts=t3,
                                                               end_request_in_ts=t4,
                                                               specify_producer_machine=test_machine)
            docs.append(doc_test_machine)

        # Add all docs
        mongodb_h.add_clean_documents(docs)

        # member_code, subsystem_code, member_class, x_road_instance, start_time_timestamp, end_time_timestamp
        matching_docs = []
        for doc in db_manager.get_matching_documents(test_machine[2], test_machine[3], test_machine[1],
                                                     test_machine[0], t1, t2):
            matching_docs.append(doc)
        self.assertEqual(len(matching_docs), total_ref_before_count)
        # member_code, subsystem_code, member_class, x_road_instance, start_time_timestamp, end_time_timestamp
        matching_docs = []
        for doc in db_manager.get_matching_documents(test_machine[2], test_machine[3], test_machine[1],
                                                     test_machine[0], t2, t3):
            matching_docs.append(doc)
        self.assertEqual(len(matching_docs), total_ref_within_count)
        # member_code, subsystem_code, member_class, x_road_instance, start_time_timestamp, end_time_timestamp
        matching_docs = []
        for doc in db_manager.get_matching_documents(test_machine[2], test_machine[3], test_machine[1],
                                                     test_machine[0], t3, t4):
            matching_docs.append(doc)
        self.assertEqual(len(matching_docs), total_ref_after_count)
        # member_code, subsystem_code, member_class, x_road_instance, start_time_timestamp, end_time_timestamp
        matching_docs = []
        for doc in db_manager.get_matching_documents(test_machine[2], test_machine[3], test_machine[1],
                                                     test_machine[0], t1, t4):
            matching_docs.append(doc)
        total_count = total_ref_before_count + total_ref_within_count + total_ref_after_count
        self.assertEqual(len(matching_docs), total_count)

        # Clean before exit
        mongodb_h.remove_all()

    @staticmethod
    def get_translation(value):
        return value

    # @unittest.skip("demonstrating skipping")
    def test_generate_report(self):

        self.maxDiff = None

        settings = Settings()
        mongodb_h = MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()

        log_manager = MagicMock()
        db_manager = DatabaseManager(mongodb_h, log_manager)

        # Clean database state
        number_of_produced_services = 7
        number_of_produced_meta_services = 11
        number_of_consumed_services = 13
        number_of_consumed_meta_services = 17

        # Test machine code to be used as producer
        test_machine = ("CI-REPORTS", "MemberClassA", "MemberCodeA", "SubsystemCodeA")
        service_code = "serviceCodeA"
        service_version = "1.0"

        docs = []
        producer_request_duration_list = []
        request_size = []
        response_size = []

        # Creating producers
        for i in range(number_of_produced_services):
            doc_producer = ci_helper.create_clean_document(specify_producer_machine=test_machine)
            doc_producer['client']['clientMemberClass'] = "MemberClass1"
            doc_producer['client']['clientMemberCode'] = "MemberCode1"
            doc_producer['client']['clientSubsystemCode'] = "SubsystemCode1"
            doc_producer['client']['serviceCode'] = service_code
            doc_producer['client']['serviceVersion'] = service_version
            producer_request_duration_list.append(doc_producer['producerDurationProducerView'])
            request_size.append(doc_producer['clientRequestSize'])
            response_size.append(doc_producer['clientResponseSize'])
            docs.append(doc_producer)

        # Creating 1 failed producer
        docs[0]['client']['succeeded'] = False

        meta_producer_request_duration_list = []
        meta_request_size = []
        meta_response_size = []

        # Creating metaproducers
        for i in range(number_of_produced_meta_services):
            doc_producer = ci_helper.create_clean_document(specify_producer_machine=test_machine)
            doc_producer['producer']['serviceCode'] = "getWsdl"
            doc_producer['client']['serviceCode'] = doc_producer['producer']['serviceCode']
            doc_producer['client']['serviceCode'] = "getWsdl"
            doc_producer['client']['serviceVersion'] = service_version
            doc_producer['client']['clientMemberClass'] = "MemberClass1"
            doc_producer['client']['clientMemberCode'] = "MemberCode1"
            doc_producer['client']['clientSubsystemCode'] = "SubsystemCode1"
            meta_producer_request_duration_list.append(doc_producer['producerDurationProducerView'])
            meta_request_size.append(doc_producer['clientRequestSize'])
            meta_response_size.append(doc_producer['clientResponseSize'])
            docs.append(doc_producer)

        consumer_request_duration_list = []
        cons_request_size = []
        cons_response_size = []

        # Creating consumers
        for i in range(number_of_consumed_services):
            doc_producer = ci_helper.create_clean_document(specify_client_machine=test_machine)
            doc_producer['client']['serviceCode'] = service_code
            doc_producer['client']['serviceVersion'] = service_version
            doc_producer['client']['serviceMemberClass'] = "MemberClass1"
            doc_producer['client']['serviceMemberCode'] = "MemberCode1"
            doc_producer['client']['serviceSubsystemCode'] = "SubsystemCode1"
            consumer_request_duration_list.append(doc_producer['totalDuration'])
            cons_request_size.append(doc_producer['clientRequestSize'])
            cons_response_size.append(doc_producer['clientResponseSize'])
            docs.append(doc_producer)

        # Creating 1 failed consumer
        docs[20]['client']['succeeded'] = False

        meta_consumer_request_duration_list = []
        meta_cons_request_size = []
        meta_cons_response_size = []

        # Creating metaconsumers
        for i in range(number_of_consumed_meta_services):
            doc_producer = ci_helper.create_clean_document(specify_client_machine=test_machine)
            doc_producer['client']['serviceCode'] = "getWsdl"
            doc_producer['producer']['serviceCode'] = doc_producer['client']['serviceCode']
            doc_producer['client']['serviceMemberClass'] = "MemberClass1"
            doc_producer['client']['serviceMemberCode'] = "MemberCode1"
            doc_producer['client']['serviceSubsystemCode'] = "SubsystemCode1"
            doc_producer['client']['serviceVersion'] = service_version
            meta_consumer_request_duration_list.append(doc_producer['totalDuration'])
            meta_cons_request_size.append(doc_producer['clientRequestSize'])
            meta_cons_response_size.append(doc_producer['clientResponseSize'])
            docs.append(doc_producer)

        # Add documents into the MongoDB
        mongodb_h.add_clean_documents(docs)

        # Produced service:
        # producer_request_duration_list
        # [-82400, 9810, -61287, -78865, -38082, 13780, 76099]

        # request_size
        # [49797, 13238, 28785, 97912, 89166, 99943, 69163]

        # response_zise
        # [45082, 59429, 7331, 76484, 89353, 69514, 27760]

        # Produced metaservice:

        # meta_producer_request_duration_list
        # [-21810, -24887, -7648, 32715, -32418, -88489, 58120, 32870, -57522, 4230, -44214]

        # meta_request_size
        # [92778, 55519, 70855, 28534, 75880, 81416, 34664, 34335, 87416, 45830, 56959]

        # meta_response_size
        # [30007, 95561, 98771, 96434, 81183, 9602, 97310, 57912, 73385, 29219, 41114]

        # Consumed service:

        # consumer_request_duration_list
        # [41114, 63779, -49667, -18066, -18385, -8924, 53571, 23562, -36997, -477, 21489, -66685, -11144]

        # cons_request_size
        # [66469, 85813, 62277, 17477, 10155, 76556, 52994, 98567, 28569, 39529, 85256, 27802, 90673]

        # cons_response_size
        # [53528, 57905, 59692, 69616, 30735, 75456, 61261, 10735, 33586, 15866, 70539, 44608, 87026]

        # Consumed metaservice:

        # meta_consumer_request_duration_list
        # [73851, 63965, -54644, 44225, 24367, -28349, -22960, -19809, -62915, 52779, 6305,
        # -28436, 23416, -33396, -81974, 15363, 80896]

        # meta_cons_request_size
        # [99901, 91411, 73772, 34687, 86662, 57377, 83202, 67449, 79806, 50277, 59682,
        # 59890, 89705, 89364, 45293, 79482, 11813]

        # meta_cons_response_size
        # [25105, 98669, 32530, 20585, 15043, 5224, 61605, 71118, 20758, 66616, 91422,
        # 18894, 97880, 22946, 83746, 37512, 97973]

        # Generate the final report MemberCodeA", "MemberClassA", "CI-REPORTS

        HTML_TEMPLATE_PATH = "/reports_module/pdf_files/pdf_report_template.html"
        CSS_FILES = ["reports_module/pdf_files/pdf_report_style.css"]

        # Initialize translator
        with open('reports_module/lang/et_lang.json', 'rb') as language_file:
            language_template = json.loads(language_file.read().decode("utf-8"))
        translator = Translator(language_template)

        language = "et"
        RIA_IMAGE_1 = "reports_module/pdf_files/header_images/ria_75_{LANGUAGE}.png".format(LANGUAGE=language)
        RIA_IMAGE_2 = "reports_module/pdf_files/header_images/eu_rdf_75_{LANGUAGE}.png".format(LANGUAGE=language)
        RIA_IMAGE_3 = "reports_module/pdf_files/header_images/xroad_75_{LANGUAGE}.png".format(LANGUAGE=language)

        report_manager = ReportManager("CI-REPORTS", "MemberClassA", "MemberCodeA", "SubsystemCodeA", "1970-1-1",
                                       "1980-1-1", None, log_manager, db_manager, language,
                                       ["getWsdl", "listMethods", "allowedMethods", "getSecurityServerMetrics",
                                        "getSecurityServerOperationalData", "getSecurityServerHealthData"], translator,
                                       HTML_TEMPLATE_PATH, "integration_tests/ci_reports", CSS_FILES, RIA_IMAGE_1,
                                       RIA_IMAGE_2, RIA_IMAGE_3)

        report_manager.generate_report()

        # Clean before exit
        mongodb_h.remove_all()
