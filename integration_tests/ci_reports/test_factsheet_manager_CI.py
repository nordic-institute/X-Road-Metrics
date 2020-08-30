import random
import unittest
from unittest.mock import MagicMock

from integration_tests.ci_reports.ci_reports_settings import Settings
from integration_tests.helpers import ci_helper
from integration_tests.helpers.cl_db_handler import MongoDBHandler
from reports_module.reportslib.database_manager import DatabaseManager
from reports_module.reportslib.factsheet_manager import FactSheetManager
from reports_module.reportslib.logger_manager import LoggerManager
from reports_module.reportslib.time_date_tools import date_to_timestamp_milliseconds
from reports_module.reportslib.time_date_tools import string_to_date

random.seed(42)


class TestFactSheetCI(unittest.TestCase):
    # @unittest.skip("demonstrating skipping")
    def test_get_query_count(self):
        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_get_query_count')
        mongodb_h = MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()

        log_manager = LoggerManager("test_get_query_count", "test_get_query_count")
        db_manager = DatabaseManager(mongodb_h, log_manager)

        start_time = "2017-06-01"
        end_time = "2017-07-01"
        start_timestamp = date_to_timestamp_milliseconds(string_to_date(start_time))
        end_timestamp = date_to_timestamp_milliseconds(string_to_date(end_time), False)

        fs_manager = FactSheetManager(db_manager, log_manager, None, start_time, end_time, 5,
                                      5, None, None)

        # No queries added yet
        fs_manager.get_query_count()
        self.assertEqual(fs_manager.query_count, 0)

        total_clean_documents = 100
        total_clean_pairs = int(total_clean_documents / 2)

        # Add 100 pairs into the clean_data
        clean_documents = []
        for i in range(total_clean_pairs):
            clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                             end_request_in_ts=end_timestamp)
            clean_documents.append(clean_document.copy())
        mongodb_h.add_clean_documents(clean_documents)

        fs_manager.get_query_count()
        self.assertEqual(fs_manager.query_count, 50)

        # Add 2 not matching docs.
        clean_documents = []
        clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp - 2,
                                                         end_request_in_ts=start_timestamp - 1)
        clean_document_2 = ci_helper.create_clean_document(start_request_in_ts=end_timestamp + 1,
                                                           end_request_in_ts=end_timestamp + 2)
        clean_documents.append(clean_document)
        clean_documents.append(clean_document_2)
        mongodb_h.add_clean_documents(clean_documents)

        # Query DB
        fs_manager.get_query_count()
        self.assertEqual(fs_manager.query_count, 50)

        # Clean before exit
        mongodb_h.remove_all()

    # @unittest.skip("demonstrating skipping")
    def test_get_service_count(self):
        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_get_service_count')
        mongodb_h = MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()

        log_manager = LoggerManager("test_get_service_count", "test_get_service_count")
        db_manager = DatabaseManager(mongodb_h, log_manager)

        start_time = "2017-06-01"
        end_time = "2017-07-01"
        start_timestamp = date_to_timestamp_milliseconds(string_to_date(start_time))
        end_timestamp = date_to_timestamp_milliseconds(string_to_date(end_time), False)

        fs_manager = FactSheetManager(db_manager, log_manager, None, start_time, end_time, 5,
                                      5, None, None)

        # A service consists of the following values:
        # serviceCode, serviceVersion, serviceMemberCode, serviceMemberClass.

        number_of_docs = 6
        docs = []

        for i in range(number_of_docs):
            clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                             end_request_in_ts=end_timestamp,
                                                             document_succeeded=True)
            docs.append(clean_document)

        test_client = docs[0]
        test_client['client']['serviceCode'] = "sc1"
        test_client['client']['serviceVersion'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceMemberClass'] = "smcl1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[1]
        test_client['client']['serviceCode'] = "sc2"
        test_client['client']['serviceVersion'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceMemberClass'] = "smcl1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[2]
        test_client['client']['serviceCode'] = "sc1"
        test_client['client']['serviceVersion'] = "sv2"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceMemberClass'] = "smcl1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[3]
        test_client['client']['serviceCode'] = "sc1"
        test_client['client']['serviceVersion'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc2"
        test_client['client']['serviceMemberClass'] = "smcl1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[4]
        test_client['client']['serviceCode'] = "sc1"
        test_client['client']['serviceVersion'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceMemberClass'] = "smcl2"
        mongodb_h.add_clean_document(test_client)

        # Create same doc
        test_client = docs[5]['client']
        test_client['serviceCode'] = "sc1"
        test_client['serviceVersion'] = "sv1"
        test_client['serviceMemberCode'] = "smc1"
        test_client['serviceMemberClass'] = "smcl1"
        mongodb_h.add_clean_document(test_client)

        fs_manager.get_service_count()
        self.assertEqual(fs_manager.service_count, 5)

        # Add not matching docs.
        clean_documents = []
        clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp - 2,
                                                         end_request_in_ts=start_timestamp - 1,
                                                         document_succeeded=True)
        clean_document_2 = ci_helper.create_clean_document(start_request_in_ts=end_timestamp + 1,
                                                           end_request_in_ts=end_timestamp + 2,
                                                           document_succeeded=True)
        clean_document_3 = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                           end_request_in_ts=end_timestamp,
                                                           document_succeeded=False)
        clean_documents.append(clean_document)
        clean_documents.append(clean_document_2)
        clean_documents.append(clean_document_3)
        mongodb_h.add_clean_documents(clean_documents)

        # Query DB
        fs_manager.get_service_count()
        self.assertEqual(fs_manager.service_count, 5)

        # Add queries for the producer side (client must be None).
        number_of_docs = 6
        docs = []

        for i in range(number_of_docs):
            clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                             end_request_in_ts=end_timestamp,
                                                             document_succeeded=True)
            docs.append(clean_document)

        test_client = docs[0]
        test_client['client'] = None
        test_client['producer']['serviceCode'] = "ssc1"
        test_client['producer']['serviceVersion'] = "ssv1"
        test_client['producer']['serviceMemberCode'] = "ssmc1"
        test_client['producer']['serviceMemberClass'] = "ssmcl1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[1]
        test_client['client'] = None
        test_client['producer']['serviceCode'] = "ssc2"
        test_client['producer']['serviceVersion'] = "ssv1"
        test_client['producer']['serviceMemberCode'] = "ssmc1"
        test_client['producer']['serviceMemberClass'] = "ssmcl1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[2]
        test_client['client'] = None
        test_client['producer']['serviceCode'] = "ssc1"
        test_client['producer']['serviceVersion'] = "ssv2"
        test_client['producer']['serviceMemberCode'] = "ssmc1"
        test_client['producer']['serviceMemberClass'] = "ssmcl1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[3]
        test_client['client'] = None
        test_client['producer']['serviceCode'] = "ssc1"
        test_client['producer']['serviceVersion'] = "ssv1"
        test_client['producer']['serviceMemberCode'] = "ssmc2"
        test_client['producer']['serviceMemberClass'] = "ssmcl1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[4]
        test_client['client'] = None
        test_client['producer']['serviceCode'] = "ssc1"
        test_client['producer']['serviceVersion'] = "ssv1"
        test_client['producer']['serviceMemberCode'] = "ssmc1"
        test_client['producer']['serviceMemberClass'] = "ssmcl2"
        mongodb_h.add_clean_document(test_client)

        # Create same doc
        test_client = docs[5]
        test_client['client'] = None
        test_client['producer']['serviceCode'] = "sc1"
        test_client['producer']['serviceVersion'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc1"
        test_client['producer']['serviceMemberClass'] = "smcl1"
        mongodb_h.add_clean_document(test_client)

        fs_manager.get_service_count()
        self.assertEqual(fs_manager.service_count, 10)

        # Clean before exit
        mongodb_h.remove_all()

    # @unittest.skip("demonstrating skipping")
    def test_get_producer_count(self):
        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_get_producer_count')
        mongodb_h = MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()

        log_manager = LoggerManager("test_get_query_count", "test_get_query_count")
        db_manager = DatabaseManager(mongodb_h, log_manager)

        start_time = "2017-06-01"
        end_time = "2017-07-01"
        start_timestamp = date_to_timestamp_milliseconds(string_to_date(start_time))
        end_timestamp = date_to_timestamp_milliseconds(string_to_date(end_time), False)

        fs_manager = FactSheetManager(db_manager, log_manager, None, start_time, end_time, 5,
                                      5, None, None)

        # A producer consists of the following values: serviceXRoadInstance, serviceMemberClass, serviceMemberCode.

        number_of_docs = 5
        docs = []

        for i in range(number_of_docs):
            clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                             end_request_in_ts=end_timestamp,
                                                             document_succeeded=True)
            docs.append(clean_document)

        test_client = docs[0]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[1]
        test_client['client']['serviceXRoadInstance'] = "sc2"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[2]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv2"
        test_client['client']['serviceMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[3]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc2"
        mongodb_h.add_clean_document(test_client)

        # Create same doc
        test_client = docs[4]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        fs_manager.get_producer_count()
        self.assertEqual(fs_manager.producer_count, 4)

        # Add not matching docs.
        clean_documents = []
        clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp - 2,
                                                         end_request_in_ts=start_timestamp - 1,
                                                         document_succeeded=True)
        clean_document_2 = ci_helper.create_clean_document(start_request_in_ts=end_timestamp + 1,
                                                           end_request_in_ts=end_timestamp + 2,
                                                           document_succeeded=True)
        clean_document_3 = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                           end_request_in_ts=end_timestamp,
                                                           document_succeeded=False)
        clean_documents.append(clean_document)
        clean_documents.append(clean_document_2)
        clean_documents.append(clean_document_3)
        mongodb_h.add_clean_documents(clean_documents)

        # Query DB
        fs_manager.get_producer_count()
        self.assertEqual(fs_manager.producer_count, 4)

        # Test None fields: (adding 3 new ones)
        number_of_docs = 5
        docs = []

        for i in range(number_of_docs):
            clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                             end_request_in_ts=end_timestamp,
                                                             document_succeeded=True)
            docs.append(clean_document)

        test_client = docs[0]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = None
        mongodb_h.add_clean_document(test_client)

        test_client = docs[1]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = None
        test_client['client']['serviceMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[2]
        test_client['client']['serviceXRoadInstance'] = None
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        # Create same doc
        test_client = docs[3]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = None
        mongodb_h.add_clean_document(test_client)

        # Create same doc
        test_client = docs[4]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = None
        test_client['client']['serviceMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        fs_manager.get_producer_count()
        self.assertEqual(fs_manager.producer_count, 7)

        # Add queries for the producer side (client must be None).
        number_of_docs = 5
        docs = []

        for i in range(number_of_docs):
            clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                             end_request_in_ts=end_timestamp,
                                                             document_succeeded=True)
            docs.append(clean_document)

        test_client = docs[0]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "ssc1"
        test_client['producer']['serviceMemberClass'] = "ssv1"
        test_client['producer']['serviceMemberCode'] = "ssmc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[1]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "ssc2"
        test_client['producer']['serviceMemberClass'] = "ssv1"
        test_client['producer']['serviceMemberCode'] = "ssmc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[2]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "ssc1"
        test_client['producer']['serviceMemberClass'] = "ssv2"
        test_client['producer']['serviceMemberCode'] = "ssmc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[3]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "ssc1"
        test_client['producer']['serviceMemberClass'] = "ssv1"
        test_client['producer']['serviceMemberCode'] = "ssmc2"
        mongodb_h.add_clean_document(test_client)

        # Create same doc
        test_client = docs[4]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        fs_manager.get_producer_count()
        self.assertEqual(fs_manager.producer_count, 11)

        # Clean before exit
        mongodb_h.remove_all()

    # @unittest.skip("demonstrating skipping")
    def test_get_member_count(self):
        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_get_member_count')
        mongodb_h = MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()

        # A service member consists of the following values:
        # serviceXRoadInstance, serviceMemberClass, serviceMemberCode.
        # A client member consists of the following values:
        # clientXRoadInstance, clientMemberClass, clientMemberCode.

        start_time = "2017-06-01"
        end_time = "2017-07-01"
        start_timestamp = date_to_timestamp_milliseconds(string_to_date(start_time))
        end_timestamp = date_to_timestamp_milliseconds(string_to_date(end_time), False)

        number_of_docs = 11
        docs = []

        for i in range(number_of_docs):
            clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                             end_request_in_ts=end_timestamp,
                                                             document_succeeded=True)
            docs.append(clean_document)

        # Create service members
        test_client = docs[0]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[1]
        test_client['client']['serviceXRoadInstance'] = "sc2"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[2]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv2"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[3]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc2"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        # Create same doc
        test_client = docs[4]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        # Create client members
        test_client = docs[5]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[6]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['clientXRoadInstance'] = "sc2"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[7]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv2"
        test_client['client']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[8]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc2"
        mongodb_h.add_clean_document(test_client)

        # Create same doc
        test_client = docs[9]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        # Query DB
        log_manager = LoggerManager("test_get_member_count", "test_get_member_count")
        db_manager = DatabaseManager(mongodb_h, log_manager)

        fs_manager = FactSheetManager(db_manager, log_manager, None, start_time, end_time, 5,
                                      5, None, None)

        fs_manager.get_member_count()
        self.assertEqual(fs_manager.member_count, 4)

        fs_manager.get_gov_member_count()
        self.assertEqual(fs_manager.gov_member_count, 0)

        # Add not matching docs.
        clean_documents = []
        clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp - 2,
                                                         end_request_in_ts=start_timestamp - 1,
                                                         document_succeeded=True)
        clean_document_2 = ci_helper.create_clean_document(start_request_in_ts=end_timestamp + 1,
                                                           end_request_in_ts=end_timestamp + 2,
                                                           document_succeeded=True)
        clean_document_3 = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                           end_request_in_ts=end_timestamp,
                                                           document_succeeded=False)
        clean_documents.append(clean_document)
        clean_documents.append(clean_document_2)
        clean_documents.append(clean_document_3)
        mongodb_h.add_clean_documents(clean_documents)

        # Check again
        fs_manager.get_member_count()
        self.assertEqual(fs_manager.member_count, 4)

        fs_manager.get_gov_member_count()
        self.assertEqual(fs_manager.gov_member_count, 0)

        # Add gov member
        number_of_gov_members = 9
        docs = []

        for i in range(number_of_gov_members):
            clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                             end_request_in_ts=end_timestamp,
                                                             document_succeeded=True)
            docs.append(clean_document)

        # Create service members
        test_client = docs[0]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "GOV"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[1]
        test_client['client']['serviceXRoadInstance'] = "sc2"
        test_client['client']['serviceMemberClass'] = "GOV"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[2]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "GOV"
        test_client['client']['serviceMemberCode'] = "smc2"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        # Create same doc
        test_client = docs[3]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "GOV"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        # Create client members
        test_client = docs[4]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "GOV"
        test_client['client']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[5]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['clientXRoadInstance'] = "sc2"
        test_client['client']['clientMemberClass'] = "GOV"
        test_client['client']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[6]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "GOV"
        test_client['client']['clientMemberCode'] = "smc2"
        mongodb_h.add_clean_document(test_client)

        # Create same doc
        test_client = docs[7]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "GOV"
        test_client['client']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        fs_manager.get_gov_member_count()
        self.assertEqual(fs_manager.gov_member_count, 3)

        fs_manager.get_member_count()
        self.assertEqual(fs_manager.member_count, 7)

        # Create one more:
        test_client = docs[8]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = None
        mongodb_h.add_clean_document(test_client)

        fs_manager.get_gov_member_count()
        self.assertEqual(fs_manager.gov_member_count, 3)

        fs_manager.get_member_count()
        self.assertEqual(fs_manager.member_count, 8)

        # Test with producer as well (client = None)

        number_of_docs = 10
        docs = []

        for i in range(number_of_docs):
            clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                             end_request_in_ts=end_timestamp,
                                                             document_succeeded=True)
            docs.append(clean_document)

        # Create service members
        test_client = docs[0]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "ssc1"
        test_client['producer']['serviceMemberClass'] = "GOV"
        test_client['producer']['serviceMemberCode'] = "ssmc1"
        test_client['producer']['clientXRoadInstance'] = "sc1"
        test_client['producer']['clientMemberClass'] = "sv1"
        test_client['producer']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[1]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "ssc2"
        test_client['producer']['serviceMemberClass'] = "ssv1"
        test_client['producer']['serviceMemberCode'] = "ssmc1"
        test_client['producer']['clientXRoadInstance'] = "sc1"
        test_client['producer']['clientMemberClass'] = "sv1"
        test_client['producer']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[2]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "ssc1"
        test_client['producer']['serviceMemberClass'] = "ssv2"
        test_client['producer']['serviceMemberCode'] = "ssmc1"
        test_client['producer']['clientXRoadInstance'] = "sc1"
        test_client['producer']['clientMemberClass'] = "sv1"
        test_client['producer']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[3]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "ssc1"
        test_client['producer']['serviceMemberClass'] = "ssv1"
        test_client['producer']['serviceMemberCode'] = "ssmc2"
        test_client['producer']['clientXRoadInstance'] = "sc1"
        test_client['producer']['clientMemberClass'] = "sv1"
        test_client['producer']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        # Create same doc
        test_client = docs[4]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "ssc1"
        test_client['producer']['serviceMemberClass'] = "ssv1"
        test_client['producer']['serviceMemberCode'] = "ssmc1"
        test_client['producer']['clientXRoadInstance'] = "sc1"
        test_client['producer']['clientMemberClass'] = "sv1"
        test_client['producer']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        # Create client members
        test_client = docs[5]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc1"
        test_client['producer']['clientXRoadInstance'] = "ssc1"
        test_client['producer']['clientMemberClass'] = "GOV"
        test_client['producer']['clientMemberCode'] = "ssmc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[6]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc1"
        test_client['producer']['clientXRoadInstance'] = "ssc2"
        test_client['producer']['clientMemberClass'] = "ssv1"
        test_client['producer']['clientMemberCode'] = "ssmc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[7]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc1"
        test_client['producer']['clientXRoadInstance'] = "ssc1"
        test_client['producer']['clientMemberClass'] = "ssv2"
        test_client['producer']['clientMemberCode'] = "ssmc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[8]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc1"
        test_client['producer']['clientXRoadInstance'] = "ssc1"
        test_client['producer']['clientMemberClass'] = "ssv1"
        test_client['producer']['clientMemberCode'] = "ssmc2"
        mongodb_h.add_clean_document(test_client)

        # Create same doc
        test_client = docs[9]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc1"
        test_client['producer']['clientXRoadInstance'] = "ssc1"
        test_client['producer']['clientMemberClass'] = "ssv1"
        test_client['producer']['clientMemberCode'] = "ssmc1"
        mongodb_h.add_clean_document(test_client)

        fs_manager.get_gov_member_count()
        self.assertEqual(fs_manager.gov_member_count, 4)

        fs_manager.get_member_count()
        self.assertEqual(fs_manager.member_count, 13)

        # Clean before exit
        mongodb_h.remove_all()

    # @unittest.skip("demonstrating skipping")
    def test_get_subsystem_count(self):
        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_get_subsystem_count')
        mongodb_h = MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()
        log_manager = LoggerManager("test_get_subsystem_count", "test_get_subsystem_count")
        db_manager = DatabaseManager(mongodb_h, log_manager)

        start_time = "2017-06-01"
        end_time = "2017-07-01"
        start_timestamp = date_to_timestamp_milliseconds(string_to_date(start_time))
        end_timestamp = date_to_timestamp_milliseconds(string_to_date(end_time), False)

        fs_manager = FactSheetManager(db_manager, log_manager, None, start_time, end_time, 5,
                                      5, None, None)

        """
        service subsystems:
        "serviceXRoadInstance": "$document.serviceXRoadInstance",
        "serviceMemberClass": "$document.serviceMemberClass",
        "serviceMemberCode": "$document.serviceMemberCode",
        "serviceSubsystemCode": "$document.serviceSubsystemCode"

        client subsystems:
        "clientXRoadInstance": "$document.clientXRoadInstance",
        "clientMemberClass": "$document.clientMemberClass",
        "clientMemberCode": "$document.clientMemberCode",
        "clientSubsystemCode": "$document.clientSubsystemCode"
        """

        number_of_docs = 12
        docs = []

        for i in range(number_of_docs):
            clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                             end_request_in_ts=end_timestamp,
                                                             document_succeeded=True)
            docs.append(clean_document)

        # Create service subsystems
        test_client = docs[0]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        test_client['client']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[1]
        test_client['client']['serviceXRoadInstance'] = "sc2"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        test_client['client']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[2]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv2"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        test_client['client']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[3]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc2"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        test_client['client']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[4]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc2"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        test_client['client']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        # Create same doc
        test_client = docs[5]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        test_client['client']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        # Create client subsystems
        test_client = docs[6]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        test_client['client']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[7]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        test_client['client']['clientXRoadInstance'] = "sc2"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        test_client['client']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[8]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv2"
        test_client['client']['clientMemberCode'] = "smc1"
        test_client['client']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[9]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc2"
        test_client['client']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[10]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        test_client['client']['clientSubsystemCode'] = "ssc2"
        mongodb_h.add_clean_document(test_client)

        # Create same doc
        test_client = docs[11]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        test_client['client']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        fs_manager.get_subsystem_count()
        self.assertEqual(fs_manager.subsystem_count, 5)

        # Add not matching docs.
        clean_documents = []
        clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp - 2,
                                                         end_request_in_ts=start_timestamp - 1,
                                                         document_succeeded=True)
        clean_document_2 = ci_helper.create_clean_document(start_request_in_ts=end_timestamp + 1,
                                                           end_request_in_ts=end_timestamp + 2,
                                                           document_succeeded=True)
        clean_document_3 = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                           end_request_in_ts=end_timestamp,
                                                           document_succeeded=False)
        clean_documents.append(clean_document)
        clean_documents.append(clean_document_2)
        clean_documents.append(clean_document_3)
        mongodb_h.add_clean_documents(clean_documents)

        # Check again
        fs_manager.get_subsystem_count()
        self.assertEqual(fs_manager.subsystem_count, 5)

        # Check producer (Client = None)
        number_of_docs = 12
        docs = []

        for i in range(number_of_docs):
            clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                             end_request_in_ts=end_timestamp,
                                                             document_succeeded=True)
            docs.append(clean_document)

        # Create service subsystems
        test_client = docs[0]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "ssc1"
        test_client['producer']['serviceMemberClass'] = "ssv1"
        test_client['producer']['serviceMemberCode'] = None
        test_client['producer']['serviceSubsystemCode'] = "sssc1"
        test_client['producer']['clientXRoadInstance'] = "sc1"
        test_client['producer']['clientMemberClass'] = "sv1"
        test_client['producer']['clientMemberCode'] = "smc1"
        test_client['producer']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[1]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "ssc2"
        test_client['producer']['serviceMemberClass'] = "ssv1"
        test_client['producer']['serviceMemberCode'] = "ssmc1"
        test_client['producer']['serviceSubsystemCode'] = "sssc1"
        test_client['producer']['clientXRoadInstance'] = "sc1"
        test_client['producer']['clientMemberClass'] = "sv1"
        test_client['producer']['clientMemberCode'] = "smc1"
        test_client['producer']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[2]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "ssc1"
        test_client['producer']['serviceMemberClass'] = "ssv2"
        test_client['producer']['serviceMemberCode'] = "ssmc1"
        test_client['producer']['serviceSubsystemCode'] = "sssc1"
        test_client['producer']['clientXRoadInstance'] = "sc1"
        test_client['producer']['clientMemberClass'] = "sv1"
        test_client['producer']['clientMemberCode'] = "smc1"
        test_client['producer']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[3]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "ssc1"
        test_client['producer']['serviceMemberClass'] = "ssv1"
        test_client['producer']['serviceMemberCode'] = "ssmc2"
        test_client['producer']['serviceSubsystemCode'] = "sssc1"
        test_client['producer']['clientXRoadInstance'] = "sc1"
        test_client['producer']['clientMemberClass'] = "sv1"
        test_client['producer']['clientMemberCode'] = "smc1"
        test_client['producer']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[4]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "ssc1"
        test_client['producer']['serviceMemberClass'] = "ssv1"
        test_client['producer']['serviceMemberCode'] = "ssmc1"
        test_client['producer']['serviceSubsystemCode'] = "sssc2"
        test_client['producer']['clientXRoadInstance'] = "sc1"
        test_client['producer']['clientMemberClass'] = "sv1"
        test_client['producer']['clientMemberCode'] = "smc1"
        test_client['producer']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        # Create same doc
        test_client = docs[5]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "ssc1"
        test_client['producer']['serviceMemberClass'] = "ssv1"
        test_client['producer']['serviceMemberCode'] = None
        test_client['producer']['serviceSubsystemCode'] = "sssc1"
        test_client['producer']['clientXRoadInstance'] = "sc1"
        test_client['producer']['clientMemberClass'] = "sv1"
        test_client['producer']['clientMemberCode'] = "smc1"
        test_client['producer']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        # Create client subsystems
        test_client = docs[6]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc1"
        test_client['producer']['serviceSubsystemCode'] = "ssc1"
        test_client['producer']['clientXRoadInstance'] = "ssc1"
        test_client['producer']['clientMemberClass'] = "ssv1"
        test_client['producer']['clientMemberCode'] = "ssmc1"
        test_client['producer']['clientSubsystemCode'] = None
        mongodb_h.add_clean_document(test_client)

        test_client = docs[7]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc1"
        test_client['producer']['serviceSubsystemCode'] = "ssc1"
        test_client['producer']['clientXRoadInstance'] = "ssc2"
        test_client['producer']['clientMemberClass'] = "ssv1"
        test_client['producer']['clientMemberCode'] = "ssmc1"
        test_client['producer']['clientSubsystemCode'] = "sssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[8]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc1"
        test_client['producer']['serviceSubsystemCode'] = "ssc1"
        test_client['producer']['clientXRoadInstance'] = "ssc1"
        test_client['producer']['clientMemberClass'] = "ssv2"
        test_client['producer']['clientMemberCode'] = "ssmc1"
        test_client['producer']['clientSubsystemCode'] = "sssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[9]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc1"
        test_client['producer']['serviceSubsystemCode'] = "ssc1"
        test_client['producer']['clientXRoadInstance'] = "ssc1"
        test_client['producer']['clientMemberClass'] = "ssv1"
        test_client['producer']['clientMemberCode'] = "ssmc2"
        test_client['producer']['clientSubsystemCode'] = "sssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[10]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc1"
        test_client['producer']['serviceSubsystemCode'] = "ssc1"
        test_client['producer']['clientXRoadInstance'] = "ssc1"
        test_client['producer']['clientMemberClass'] = "ssv1"
        test_client['producer']['clientMemberCode'] = "ssmc1"
        test_client['producer']['clientSubsystemCode'] = "sssc2"
        mongodb_h.add_clean_document(test_client)

        # Create same doc
        test_client = docs[11]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc1"
        test_client['producer']['serviceSubsystemCode'] = "ssc1"
        test_client['producer']['clientXRoadInstance'] = "ssc1"
        test_client['producer']['clientMemberClass'] = "ssv1"
        test_client['producer']['clientMemberCode'] = "ssmc1"
        test_client['producer']['clientSubsystemCode'] = None
        mongodb_h.add_clean_document(test_client)

        fs_manager.get_subsystem_count()
        self.assertEqual(fs_manager.subsystem_count, 11)

        # Clean before exit
        mongodb_h.remove_all()

    # @unittest.skip("demonstrating skipping")
    def test_get_sec_srv_services(self):
        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_get_sec_srv_services')
        mongodb_h = MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()
        log_manager = LoggerManager("test_get_sec_srv_services", "test_get_sec_srv_services")
        db_manager = DatabaseManager(mongodb_h, log_manager)

        start_time = "2017-06-01"
        end_time = "2017-07-01"
        start_timestamp = date_to_timestamp_milliseconds(string_to_date(start_time))
        end_timestamp = date_to_timestamp_milliseconds(string_to_date(end_time), False)

        fs_manager = FactSheetManager(db_manager, log_manager, None, start_time, end_time, 5,
                                      5, None, None)

        # serviceSecurityServerAddress
        # clientSecurityServerAddress

        number_of_docs = 5
        docs = []

        for i in range(number_of_docs):
            clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                             end_request_in_ts=end_timestamp,
                                                             document_succeeded=True)
            docs.append(clean_document)

        # Create service subsystems
        test_client = docs[0]
        test_client['client']['serviceSecurityServerAddress'] = "sc1"
        test_client['client']['clientSecurityServerAddress'] = "sc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[1]
        test_client['client']['serviceSecurityServerAddress'] = "sc2"
        test_client['client']['clientSecurityServerAddress'] = "sc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[2]
        test_client['client']['serviceSecurityServerAddress'] = "sc1"
        test_client['client']['clientSecurityServerAddress'] = "sc2"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[3]
        test_client['client']['serviceSecurityServerAddress'] = "sc3"
        test_client['client']['clientSecurityServerAddress'] = "sc4"
        mongodb_h.add_clean_document(test_client)

        # Create same doc
        test_client = docs[4]
        test_client['client']['serviceSecurityServerAddress'] = "sc1"
        test_client['client']['clientSecurityServerAddress'] = "sc1"
        mongodb_h.add_clean_document(test_client)

        fs_manager.get_sec_srv_services()
        self.assertEqual(fs_manager.sec_srv_services, 4)

        # Add not matching docs.
        clean_documents = []
        clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp - 2,
                                                         end_request_in_ts=start_timestamp - 1,
                                                         document_succeeded=True)
        clean_document_2 = ci_helper.create_clean_document(start_request_in_ts=end_timestamp + 1,
                                                           end_request_in_ts=end_timestamp + 2,
                                                           document_succeeded=True)
        clean_document_3 = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                           end_request_in_ts=end_timestamp,
                                                           document_succeeded=False)
        clean_documents.append(clean_document)
        clean_documents.append(clean_document_2)
        clean_documents.append(clean_document_3)
        mongodb_h.add_clean_documents(clean_documents)

        # Check again
        fs_manager.get_sec_srv_services()
        self.assertEqual(fs_manager.sec_srv_services, 4)

        # Producer check (Client = None)

        number_of_docs = 6
        docs = []

        for i in range(number_of_docs):
            clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                             end_request_in_ts=end_timestamp,
                                                             document_succeeded=True)
            docs.append(clean_document)

        # Create service subsystems
        test_client = docs[0]
        test_client['client'] = None
        test_client['producer']['serviceSecurityServerAddress'] = "sc1"
        test_client['producer']['clientSecurityServerAddress'] = "sc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[1]
        test_client['client'] = None
        test_client['producer']['serviceSecurityServerAddress'] = "sc2"
        test_client['producer']['clientSecurityServerAddress'] = "sc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[2]
        test_client['client'] = None
        test_client['producer']['serviceSecurityServerAddress'] = "sc1"
        test_client['producer']['clientSecurityServerAddress'] = "sc2"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[3]
        test_client['client'] = None
        test_client['producer']['serviceSecurityServerAddress'] = "sc3"
        test_client['producer']['clientSecurityServerAddress'] = "ssc4"
        mongodb_h.add_clean_document(test_client)

        # None fields
        test_client = docs[4]
        test_client['client'] = None
        test_client['producer']['serviceSecurityServerAddress'] = None
        test_client['producer']['clientSecurityServerAddress'] = None
        mongodb_h.add_clean_document(test_client)

        # Create same doc
        test_client = docs[5]
        test_client['client'] = None
        test_client['producer']['serviceSecurityServerAddress'] = "ssc1"
        test_client['producer']['clientSecurityServerAddress'] = "sc1"
        mongodb_h.add_clean_document(test_client)

        fs_manager.get_sec_srv_services()
        self.assertEqual(fs_manager.sec_srv_services, 7)

        # Clean before exit
        mongodb_h.remove_all()

    # @unittest.skip("demonstrating skipping")
    def test_get_producers_top(self):
        # Clean database state
        settings = Settings()
        settings.logger.info('[test] test_get_producers_top')
        mongodb_h = MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()
        log_manager = LoggerManager("test_get_producers_top", "test_get_producers_top")
        db_manager = DatabaseManager(mongodb_h, log_manager)

        start_time = "2017-06-01"
        end_time = "2017-07-01"
        start_timestamp = date_to_timestamp_milliseconds(string_to_date(start_time))
        end_timestamp = date_to_timestamp_milliseconds(string_to_date(end_time), False)

        member_subsys_info = MagicMock()
        fs_manager = FactSheetManager(db_manager, log_manager, None, start_time, end_time, 5,
                                      5, None, member_subsys_info)

        # Create service subsystems
        number_of_docs = 6
        docs = []

        for i in range(number_of_docs):
            clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                             end_request_in_ts=end_timestamp,
                                                             document_succeeded=True)
            docs.append(clean_document)

        # Create service subsystems
        test_client = docs[0]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[1]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[2]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[3]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc2"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[4]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc2"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[5]
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv2"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        fs_manager.get_producers_top()
        self.assertEqual(fs_manager.producers_top['1']['query_count'], 3)
        self.assertEqual(fs_manager.producers_top['2']['query_count'], 2)
        self.assertEqual(fs_manager.producers_top['3']['query_count'], 1)

        # Add not matching docs.
        clean_documents = []
        clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp - 2,
                                                         end_request_in_ts=start_timestamp - 1,
                                                         document_succeeded=True)
        clean_document_2 = ci_helper.create_clean_document(start_request_in_ts=end_timestamp + 1,
                                                           end_request_in_ts=end_timestamp + 2,
                                                           document_succeeded=True)
        clean_document_3 = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                           end_request_in_ts=end_timestamp,
                                                           document_succeeded=False)
        clean_documents.append(clean_document)
        clean_documents.append(clean_document_2)
        clean_documents.append(clean_document_3)
        mongodb_h.add_clean_documents(clean_documents)

        # Check again
        fs_manager.get_producers_top()
        self.assertEqual(fs_manager.producers_top['1']['query_count'], 3)
        self.assertEqual(fs_manager.producers_top['2']['query_count'], 2)
        self.assertEqual(fs_manager.producers_top['3']['query_count'], 1)

        # Add producer documents (Client = None)
        # Create service subsystems
        number_of_docs = 6
        docs = []

        for i in range(number_of_docs):
            clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                             end_request_in_ts=end_timestamp,
                                                             document_succeeded=True)
            docs.append(clean_document)

        # Create service subsystems
        test_client = docs[0]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc1"
        test_client['producer']['serviceSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[1]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc1"
        test_client['producer']['serviceSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[2]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc1"
        test_client['producer']['serviceSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[3]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc2"
        test_client['producer']['serviceSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[4]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc2"
        test_client['producer']['serviceSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[5]
        test_client['client'] = None
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv2"
        test_client['producer']['serviceMemberCode'] = "smc1"
        test_client['producer']['serviceSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        fs_manager.get_producers_top()
        self.assertEqual(fs_manager.producers_top['1']['query_count'], 6)
        self.assertEqual(fs_manager.producers_top['2']['query_count'], 4)
        self.assertEqual(fs_manager.producers_top['3']['query_count'], 2)

        # Clean before exit
        mongodb_h.remove_all()

    # @unittest.skip("demonstrating skipping")
    def test_get_consumers_top(self):
        # Clean database state
        settings = Settings()
        settings.logger.info('[test] get_consumers_top')
        mongodb_h = MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()
        log_manager = LoggerManager("test_get_consumers_top", "test_get_consumers_top")
        db_manager = DatabaseManager(mongodb_h, log_manager)

        start_time = "2017-06-01"
        end_time = "2017-07-01"
        start_timestamp = date_to_timestamp_milliseconds(string_to_date(start_time))
        end_timestamp = date_to_timestamp_milliseconds(string_to_date(end_time), False)

        member_subsys_info = MagicMock()
        excluded_member_codes = MagicMock()
        fs_manager = FactSheetManager(db_manager, log_manager, None, start_time, end_time, 5,
                                      5, excluded_member_codes, member_subsys_info)

        number_of_docs = 6
        docs = []

        for i in range(number_of_docs):
            clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                             end_request_in_ts=end_timestamp,
                                                             document_succeeded=True)
            docs.append(clean_document)

        test_client = docs[0]
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[1]
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[2]
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[3]
        test_client['client']['clientXRoadInstance'] = "sc2"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[4]
        test_client['client']['clientXRoadInstance'] = "sc2"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[5]
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv2"
        test_client['client']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        fs_manager.get_consumers_top()
        self.assertEqual(fs_manager.consumers_top['1']['query_count'], 3)
        self.assertEqual(fs_manager.consumers_top['2']['query_count'], 2)
        self.assertEqual(fs_manager.consumers_top['3']['query_count'], 1)

        # Add not matching docs.
        clean_documents = []
        clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp - 2,
                                                         end_request_in_ts=start_timestamp - 1,
                                                         document_succeeded=True)
        clean_document_2 = ci_helper.create_clean_document(start_request_in_ts=end_timestamp + 1,
                                                           end_request_in_ts=end_timestamp + 2,
                                                           document_succeeded=True)
        clean_document_3 = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                           end_request_in_ts=end_timestamp,
                                                           document_succeeded=False)
        clean_documents.append(clean_document)
        clean_documents.append(clean_document_2)
        clean_documents.append(clean_document_3)
        mongodb_h.add_clean_documents(clean_documents)

        # Check again
        fs_manager.get_consumers_top()
        self.assertEqual(fs_manager.consumers_top['1']['query_count'], 3)
        self.assertEqual(fs_manager.consumers_top['2']['query_count'], 2)
        self.assertEqual(fs_manager.consumers_top['3']['query_count'], 1)

        # Add producer documents (Client = None)

        number_of_docs = 6
        docs = []

        for i in range(number_of_docs):
            clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                             end_request_in_ts=end_timestamp,
                                                             document_succeeded=True)
            docs.append(clean_document)

        test_client = docs[0]
        test_client['client'] = None
        test_client['producer']['clientXRoadInstance'] = "sc1"
        test_client['producer']['clientMemberClass'] = "sv1"
        test_client['producer']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[1]
        test_client['client'] = None
        test_client['producer']['clientXRoadInstance'] = "sc1"
        test_client['producer']['clientMemberClass'] = "sv1"
        test_client['producer']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[2]
        test_client['client'] = None
        test_client['producer']['clientXRoadInstance'] = "sc1"
        test_client['producer']['clientMemberClass'] = "sv1"
        test_client['producer']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[3]
        test_client['client'] = None
        test_client['producer']['clientXRoadInstance'] = "sc2"
        test_client['producer']['clientMemberClass'] = "sv1"
        test_client['producer']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[4]
        test_client['client'] = None
        test_client['producer']['clientXRoadInstance'] = "sc2"
        test_client['producer']['clientMemberClass'] = "sv1"
        test_client['producer']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[5]
        test_client['client'] = None
        test_client['producer']['clientXRoadInstance'] = "sc1"
        test_client['producer']['clientMemberClass'] = "sv2"
        test_client['producer']['clientMemberCode'] = "smc1"
        mongodb_h.add_clean_document(test_client)

        fs_manager.get_consumers_top()
        self.assertEqual(fs_manager.consumers_top['1']['query_count'], 6)
        self.assertEqual(fs_manager.consumers_top['2']['query_count'], 4)
        self.assertEqual(fs_manager.consumers_top['3']['query_count'], 2)

        # Clean before exit
        mongodb_h.remove_all()

    # @unittest.skip("demonstrating skipping")
    def test_create_results_document(self):
        # Clean database state
        settings = Settings()
        settings.logger.info('[test] get_consumers_top')
        mongodb_h = MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        mongodb_h.remove_all()
        mongodb_h.create_indexes()
        log_manager = LoggerManager("test_get_consumers_top", "test_get_consumers_top")
        db_manager = DatabaseManager(mongodb_h, log_manager)

        start_time = "2017-06-01"
        end_time = "2017-07-01"
        start_timestamp = date_to_timestamp_milliseconds(string_to_date(start_time))
        end_timestamp = date_to_timestamp_milliseconds(string_to_date(end_time), False)

        member_subsys_info = MagicMock()
        excluded_member_codes = MagicMock()
        fs_manager = FactSheetManager(db_manager, log_manager, None, start_time, end_time, 5,
                                      5, excluded_member_codes, member_subsys_info)

        number_of_docs = 12
        docs = []

        for i in range(number_of_docs):
            clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                             end_request_in_ts=end_timestamp,
                                                             document_succeeded=True)
            docs.append(clean_document)

        # Create service subsystems
        test_client = docs[0]
        test_client['client']["clientSecurityServerAddress"] = "1.1.1.1"
        test_client['client']["serviceSecurityServerAddress"] = "1.1.1.1"
        test_client['client']["serviceVersion"] = "2.0"
        test_client['client']['serviceCode'] = "new_sc_2"
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        test_client['client']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[1]
        test_client['client']["clientSecurityServerAddress"] = "1.1.1.1"
        test_client['client']["serviceSecurityServerAddress"] = "1.1.1.1"
        test_client['client']["serviceVersion"] = "2.0"
        test_client['client']['serviceCode'] = "new_sc_2"
        test_client['client']['serviceXRoadInstance'] = "sc2"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        test_client['client']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[2]
        test_client['client']["clientSecurityServerAddress"] = "1.1.1.1"
        test_client['client']["serviceSecurityServerAddress"] = "1.1.1.1"
        test_client['client']["serviceVersion"] = "2.0"
        test_client['client']['serviceCode'] = "new_sc_2"
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv2"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        test_client['client']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[3]
        test_client['client']["clientSecurityServerAddress"] = "1.1.1.2"
        test_client['client']["serviceSecurityServerAddress"] = "1.1.1.1"
        test_client['client']["serviceVersion"] = "2.0"
        test_client['client']['serviceCode'] = "new_sc_2"
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc2"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        test_client['client']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[4]
        test_client['client']["clientSecurityServerAddress"] = "1.1.1.1"
        test_client['client']["serviceSecurityServerAddress"] = "1.1.1.1"
        test_client['client']["serviceVersion"] = "2.0"
        test_client['client']['serviceCode'] = "new_sc_2"
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "GOV"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc2"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        test_client['client']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        # Create same doc
        test_client = docs[5]
        test_client['client']["clientSecurityServerAddress"] = "1.1.1.1"
        test_client['client']["serviceSecurityServerAddress"] = "1.1.1.1"
        test_client['client']["serviceVersion"] = "2.0"
        test_client['client']['serviceCode'] = "new_sc_2"
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        test_client['client']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        # Create client subsystems
        test_client = docs[6]
        test_client['client']["clientSecurityServerAddress"] = None
        test_client['client']["serviceSecurityServerAddress"] = "1.1.1.1"
        test_client['client']["serviceVersion"] = "2.0"
        test_client['client']['serviceCode'] = "new_sc_2"
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        test_client['client']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[7]
        test_client['client']["clientSecurityServerAddress"] = "1.1.1.1"
        test_client['client']["serviceSecurityServerAddress"] = "1.1.1.1"
        test_client['client']["serviceVersion"] = "2.0"
        test_client['client']['serviceCode'] = "new_sc_2"
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        test_client['client']['clientXRoadInstance'] = "sc2"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        test_client['client']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[8]
        test_client['client']["clientSecurityServerAddress"] = "1.1.1.1"
        test_client['client']["serviceSecurityServerAddress"] = "1.1.1.1"
        test_client['client']["serviceVersion"] = "2.0"
        test_client['client']['serviceCode'] = "new_sc_2"
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "GOV"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv2"
        test_client['client']['clientMemberCode'] = "smc1"
        test_client['client']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[9]
        test_client['client']["clientSecurityServerAddress"] = "1.1.1.1"
        test_client['client']["serviceSecurityServerAddress"] = None
        test_client['client']["serviceVersion"] = "2.0"
        test_client['client']['serviceCode'] = "new_sc_2"
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc2"
        test_client['client']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[10]
        test_client['client']["clientSecurityServerAddress"] = "1.1.1.1"
        test_client['client']["serviceSecurityServerAddress"] = "1.1.1.2"
        test_client['client']["serviceVersion"] = "2.0"
        test_client['client']['serviceCode'] = "new_sc_2"
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        test_client['client']['clientSubsystemCode'] = "ssc2"
        mongodb_h.add_clean_document(test_client)

        # Create same doc
        test_client = docs[11]
        test_client['client']["clientSecurityServerAddress"] = "1.1.1.1"
        test_client['client']["serviceSecurityServerAddress"] = "1.1.1.1"
        test_client['client']["serviceVersion"] = "2.0"
        test_client['client']['serviceCode'] = "new_sc_2"
        test_client['client']['serviceXRoadInstance'] = "sc1"
        test_client['client']['serviceMemberClass'] = "sv1"
        test_client['client']['serviceMemberCode'] = "smc1"
        test_client['client']['serviceSubsystemCode'] = "ssc1"
        test_client['client']['clientXRoadInstance'] = "sc1"
        test_client['client']['clientMemberClass'] = "sv1"
        test_client['client']['clientMemberCode'] = "smc1"
        test_client['client']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        # Add not matching docs.
        clean_documents = []
        clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp - 2,
                                                         end_request_in_ts=start_timestamp - 1,
                                                         document_succeeded=True)
        clean_document_2 = ci_helper.create_clean_document(start_request_in_ts=end_timestamp + 1,
                                                           end_request_in_ts=end_timestamp + 2,
                                                           document_succeeded=True)
        clean_document_3 = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                           end_request_in_ts=end_timestamp,
                                                           document_succeeded=False)
        clean_documents.append(clean_document)
        clean_documents.append(clean_document_2)
        clean_documents.append(clean_document_3)
        mongodb_h.add_clean_documents(clean_documents)

        # Check producer (Client = None)
        number_of_producer_docs = 12
        docs = []

        for i in range(number_of_producer_docs):
            clean_document = ci_helper.create_clean_document(start_request_in_ts=start_timestamp,
                                                             end_request_in_ts=end_timestamp,
                                                             document_succeeded=True)
            docs.append(clean_document)

        # Create service subsystems
        test_client = docs[0]
        test_client['client'] = None
        test_client['producer']["clientSecurityServerAddress"] = "1.1.1.1"
        test_client['producer']["serviceSecurityServerAddress"] = None
        test_client['producer']["serviceVersion"] = "1.0"
        test_client['producer']['serviceCode'] = "new_sc_1"
        test_client['producer']['serviceXRoadInstance'] = "ssc1"
        test_client['producer']['serviceMemberClass'] = "ssv1"
        test_client['producer']['serviceMemberCode'] = None
        test_client['producer']['serviceSubsystemCode'] = "sssc1"
        test_client['producer']['clientXRoadInstance'] = "sc1"
        test_client['producer']['clientMemberClass'] = "sv1"
        test_client['producer']['clientMemberCode'] = "smc1"
        test_client['producer']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[1]
        test_client['client'] = None
        test_client['producer']["clientSecurityServerAddress"] = "1.1.1,1"  # Comma differs
        test_client['producer']["serviceSecurityServerAddress"] = "1.1.1.1"
        test_client['producer']["serviceVersion"] = "1.0"
        test_client['producer']['serviceCode'] = "new_sc_1"
        test_client['producer']['serviceXRoadInstance'] = "ssc2"
        test_client['producer']['serviceMemberClass'] = "ssv1"
        test_client['producer']['serviceMemberCode'] = "ssmc1"
        test_client['producer']['serviceSubsystemCode'] = "sssc1"
        test_client['producer']['clientXRoadInstance'] = "sc1"
        test_client['producer']['clientMemberClass'] = "sv1"
        test_client['producer']['clientMemberCode'] = "smc1"
        test_client['producer']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[2]
        test_client['client'] = None
        test_client['producer']["clientSecurityServerAddress"] = "1.1.1.1"
        test_client['producer']["serviceSecurityServerAddress"] = "1.1.1.1"
        test_client['producer']["serviceVersion"] = "1.0"
        test_client['producer']['serviceCode'] = "new_sc_1"
        test_client['producer']['serviceXRoadInstance'] = "ssc1"
        test_client['producer']['serviceMemberClass'] = "ssv2"
        test_client['producer']['serviceMemberCode'] = "ssmc1"
        test_client['producer']['serviceSubsystemCode'] = "sssc1"
        test_client['producer']['clientXRoadInstance'] = "sc1"
        test_client['producer']['clientMemberClass'] = "sv1"
        test_client['producer']['clientMemberCode'] = "smc1"
        test_client['producer']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[3]
        test_client['client'] = None
        test_client['producer']["clientSecurityServerAddress"] = "1.1.1.1"
        test_client['producer']["serviceSecurityServerAddress"] = "1.1.1.1"
        test_client['producer']["serviceVersion"] = "1.0"
        test_client['producer']['serviceCode'] = "new_sc_1"
        test_client['producer']['serviceXRoadInstance'] = "ssc1"
        test_client['producer']['serviceMemberClass'] = "ssv1"
        test_client['producer']['serviceMemberCode'] = "ssmc2"
        test_client['producer']['serviceSubsystemCode'] = "sssc1"
        test_client['producer']['clientXRoadInstance'] = "sc1"
        test_client['producer']['clientMemberClass'] = "GOV"
        test_client['producer']['clientMemberCode'] = "smc1"
        test_client['producer']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[4]
        test_client['client'] = None
        test_client['producer']["clientSecurityServerAddress"] = "1.1.1.1"
        test_client['producer']["serviceSecurityServerAddress"] = "1.1.1.1"
        test_client['producer']["serviceVersion"] = "1.0"
        test_client['producer']['serviceCode'] = "new_sc_1"
        test_client['producer']['serviceXRoadInstance'] = "ssc1"
        test_client['producer']['serviceMemberClass'] = "ssv1"
        test_client['producer']['serviceMemberCode'] = "ssmc1"
        test_client['producer']['serviceSubsystemCode'] = "sssc2"
        test_client['producer']['clientXRoadInstance'] = "sc1"
        test_client['producer']['clientMemberClass'] = "sv1"
        test_client['producer']['clientMemberCode'] = "smc1"
        test_client['producer']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        # Create same doc
        test_client = docs[5]
        test_client['client'] = None
        test_client['producer']["clientSecurityServerAddress"] = "1.1.1.1"
        test_client['producer']["serviceSecurityServerAddress"] = "1.1.1.1"
        test_client['producer']["serviceVersion"] = "1.0"
        test_client['producer']['serviceCode'] = "new_sc_1"
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = None
        test_client['producer']['serviceSubsystemCode'] = "ssc1"
        test_client['producer']['clientXRoadInstance'] = "sc1"
        test_client['producer']['clientMemberClass'] = "sv1"
        test_client['producer']['clientMemberCode'] = "smc1"
        test_client['producer']['clientSubsystemCode'] = "ssc1"
        mongodb_h.add_clean_document(test_client)

        # Create client subsystems
        test_client = docs[6]
        test_client['client'] = None
        test_client['producer']["clientSecurityServerAddress"] = "1.1.1.1"
        test_client['producer']["serviceSecurityServerAddress"] = "1.1.1.1"
        test_client['producer']["serviceVersion"] = "1.0"
        test_client['producer']['serviceCode'] = "new_sc_1"
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc1"
        test_client['producer']['serviceSubsystemCode'] = "ssc1"
        test_client['producer']['clientXRoadInstance'] = "ssc1"
        test_client['producer']['clientMemberClass'] = "ssv1"
        test_client['producer']['clientMemberCode'] = "ssmc1"
        test_client['producer']['clientSubsystemCode'] = None
        mongodb_h.add_clean_document(test_client)

        test_client = docs[7]
        test_client['client'] = None
        test_client['producer']["clientSecurityServerAddress"] = None
        test_client['producer']["serviceSecurityServerAddress"] = "1.1.1.1"
        test_client['producer']["serviceVersion"] = "1.0"
        test_client['producer']['serviceCode'] = "new_sc_1"
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc1"
        test_client['producer']['serviceSubsystemCode'] = "ssc1"
        test_client['producer']['clientXRoadInstance'] = "ssc2"
        test_client['producer']['clientMemberClass'] = "ssv1"
        test_client['producer']['clientMemberCode'] = "ssmc1"
        test_client['producer']['clientSubsystemCode'] = "sssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[8]
        test_client['client'] = None
        test_client['producer']["clientSecurityServerAddress"] = "1.1.1.1"
        test_client['producer']["serviceSecurityServerAddress"] = "1.1.1.1"
        test_client['producer']["serviceVersion"] = "1.0"
        test_client['producer']['serviceCode'] = "new_sc_1"
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc1"
        test_client['producer']['serviceSubsystemCode'] = "ssc1"
        test_client['producer']['clientXRoadInstance'] = "ssc1"
        test_client['producer']['clientMemberClass'] = "ssv2"
        test_client['producer']['clientMemberCode'] = "ssmc1"
        test_client['producer']['clientSubsystemCode'] = "sssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[9]
        test_client['client'] = None
        test_client['producer']["clientSecurityServerAddress"] = "1.1.1.1"
        test_client['producer']["serviceSecurityServerAddress"] = "1.1.1.1"
        test_client['producer']["serviceVersion"] = "1.0"
        test_client['producer']['serviceCode'] = "new_sc_1"
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc1"
        test_client['producer']['serviceSubsystemCode'] = "ssc1"
        test_client['producer']['clientXRoadInstance'] = "ssc1"
        test_client['producer']['clientMemberClass'] = "GOV"
        test_client['producer']['clientMemberCode'] = "ssmc2"
        test_client['producer']['clientSubsystemCode'] = "sssc1"
        mongodb_h.add_clean_document(test_client)

        test_client = docs[10]
        test_client['client'] = None
        test_client['producer']["clientSecurityServerAddress"] = "1.1.1.1"
        test_client['producer']["serviceSecurityServerAddress"] = "1.1.1.1"
        test_client['producer']["serviceVersion"] = "1.0"
        test_client['producer']['serviceCode'] = "new_sc_1"
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc1"
        test_client['producer']['serviceSubsystemCode'] = "ssc1"
        test_client['producer']['clientXRoadInstance'] = "ssc1"
        test_client['producer']['clientMemberClass'] = "ssv1"
        test_client['producer']['clientMemberCode'] = "ssmc1"
        test_client['producer']['clientSubsystemCode'] = "sssc2"
        mongodb_h.add_clean_document(test_client)

        # Create same doc
        test_client = docs[11]
        test_client['client'] = None
        test_client['producer']["clientSecurityServerAddress"] = "1.1.1"
        test_client['producer']["serviceSecurityServerAddress"] = "1.1.1.1"
        test_client['producer']["serviceVersion"] = "1.0"
        test_client['producer']['serviceCode'] = "new_sc_1"
        test_client['producer']['serviceXRoadInstance'] = "sc1"
        test_client['producer']['serviceMemberClass'] = "sv1"
        test_client['producer']['serviceMemberCode'] = "smc1"
        test_client['producer']['serviceSubsystemCode'] = "ssc1"
        test_client['producer']['clientXRoadInstance'] = "ssc1"
        test_client['producer']['clientMemberClass'] = "ssv1"
        test_client['producer']['clientMemberCode'] = "ssmc1"
        test_client['producer']['clientSubsystemCode'] = None
        mongodb_h.add_clean_document(test_client)

        # Get all the variables.
        fs_manager.get_facts()

        prod_top = {"1": {
            "query_count": 13,
            "name_est": "",
            "name_eng": ""
        }, "2": {
            "query_count": 1,
            "name_est": "",
            "name_eng": ""
        }, "3": {
            "query_count": 1,
            "name_est": "",
            "name_eng": ""
        }, "4": {
            "query_count": 1,
            "name_est": "",
            "name_eng": ""
        }, "5": {
            "query_count": 1,
            "name_est": "",
            "name_eng": ""
        }

        }

        cons_top = {"1": {
            "query_count": 14,
            "name_est": "",
            "name_eng": ""
        }, "2": {
            "query_count": 3,
            "name_est": "",
            "name_eng": ""
        }, "3": {
            "query_count": 1,
            "name_est": "",
            "name_eng": ""
        }, "4": {
            "query_count": 1,
            "name_est": "",
            "name_eng": ""
        }, "5": {
            "query_count": 1,
            "name_est": "",
            "name_eng": ""
        }
        }

        manual_result_document = {
            "stats": {
                "2017": {
                    "months": {
                        "6": {
                            "query_count": number_of_docs + number_of_producer_docs + 1,  # The succeeded = False doc.
                            "service_count": 10,
                            "producer_count": 11,
                            "member_count": 12,
                            "gov_member_count": 2,
                            "subsystem_count": 15,
                            "secsrv_count": 5,
                            "producers_top": prod_top,
                            "consumers_top": cons_top
                        }
                    }
                }
            }
        }

        # Test producers top
        dict_keys = list(prod_top.keys())
        inner_dict_keys = ['query_count', 'name_est', 'name_eng']
        for key in dict_keys:
            for inner_key in inner_dict_keys:
                self.assertEqual(prod_top[key][inner_key], fs_manager.producers_top[key][inner_key])

        # Test consumers top
        dict_keys = list(cons_top.keys())
        inner_dict_keys = ['query_count', 'name_est']
        for key in dict_keys:
            for inner_key in inner_dict_keys:
                self.assertEqual(cons_top[key][inner_key], fs_manager.consumers_top[key][inner_key])

        fs_manager_result_doc = fs_manager.create_results_document()

        # Remove dictionaries that were compared before.
        del fs_manager_result_doc['stats']['2017']['months']['6']['producers_top']
        del fs_manager_result_doc['stats']['2017']['months']['6']['consumers_top']
        del manual_result_document['stats']['2017']['months']['6']['producers_top']
        del manual_result_document['stats']['2017']['months']['6']['consumers_top']

        self.maxDiff = None
        self.assertEqual(fs_manager_result_doc, manual_result_document)

        # Clean before exit
        mongodb_h.remove_all()
