import unittest
from unittest.mock import Mock

from integration_tests.helpers import cl_db_handler
from integration_tests.ci_analyzer.ci_analyzer_settings import Settings

from analysis_module.analyzer.AnalyzerDatabaseManager import AnalyzerDatabaseManager

from datetime import datetime
import time


class TestAnalyzerAggregationQueriesCI(unittest.TestCase):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # load the test database settings
        settings = Settings()
        
        # initialize a helper for operations the test database
        self.mongodb_h = cl_db_handler.MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        
        # db conf
        db_config = Mock()
        db_config.MDB_USER = settings.MONGODB_USER
        db_config.MDB_PWD = settings.MONGODB_PWD
        db_config.MDB_SERVER = settings.MONGODB_SERVER
        db_config.MONGODB_URI = "mongodb://{0}:{1}@{2}/auth_db".format(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        db_config.MONGODB_QD = "CI_query_db"
        db_config.MONGODB_AD = "CI_analyzer_database"
        self._db_config = db_config
        
        # analyzer conf
        config = Mock()
        config.timestamp_field = "timestamp"
        config.service_call_fields = ["service_call"]
        config.failed_request_ratio_threshold = 0.7
        config.historic_averages_thresholds = {'request_count': 0.95}
        config.relevant_cols_nested = ["service_call", "succeeded", "messageId", "timestamp"]
        config.relevant_cols_general_alternative = [('requestSize', 'clientRequestSize', 'producerRequestSize'),
                                                    ('responseSize', 'clientResponseSize', 'producerResponseSize')]
        config.relevant_cols_general = ["_id", 'totalDuration', 'producerDurationProducerView', 'requestNwDuration',
                                        'responseNwDuration', 'correctorStatus']
        self._config = config
        
        # set up the Analyzer database manager to be tested
        self.db_manager = AnalyzerDatabaseManager(db_config, config)

    def test_aggregate_data_empty_database(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        clean_documents = []
        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data("failed_request_ratio", agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])
        self.assertEqual(0, len(data))
        
        data = self.db_manager.aggregate_data("duplicate_message_ids", agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])
        self.assertEqual(0, len(data))
        
        data = self.db_manager.aggregate_data(model_type="time_sync_errors", metric="responseNwDuration", threshold=0,
                                              agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])
        self.assertEqual(0, len(data))
        
        data = self.db_manager.aggregate_data_for_historic_averages_model(agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])
        self.assertEqual(0, len(data))

        # Clean before exit
        self.mongodb_h.remove_all()

    def test_aggregate_data_for_failed_request_ratio_model_single_query(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": client, "producer": client}
        clean_doc["clientRequestSize"] = 1000
        clean_doc["producerRequestSize"] = 1000
        clean_doc["clientResponseSize"] = 1000
        clean_doc["producerResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = 100
        clean_documents = [clean_doc]

        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data("failed_request_ratio", agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])

        self.assertEqual(1, len(data))
        self.assertEqual(1, data[data.succeeded].iloc[0]["count"])
        
        # Clean before exit
        self.mongodb_h.remove_all()
    
    def test_aggregate_data_for_failed_request_ratio_model_single_query_client_missing(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": None, "producer": client}
        clean_doc["producerRequestSize"] = 1000
        clean_doc["producerResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = 100
        clean_documents = [clean_doc]

        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data("failed_request_ratio", agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])

        self.assertEqual(1, len(data))
        self.assertEqual(1, data[data.succeeded].iloc[0]["count"])
        
        # Clean before exit
        self.mongodb_h.remove_all()
        
    def test_aggregate_data_for_failed_request_ratio_model_single_query_producer_missing(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": client, "producer": None}
        clean_doc["clientRequestSize"] = 1000
        clean_doc["clientResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = 100
        clean_documents = [clean_doc]

        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data("failed_request_ratio", agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])

        self.assertEqual(1, len(data))
        self.assertEqual(1, data[data.succeeded].iloc[0]["count"])
        
        # Clean before exit
        self.mongodb_h.remove_all()
        
    def test_aggregate_data_for_failed_request_ratio_model_two_queries_in_same_period_both_true(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": client, "producer": client}
        clean_doc["clientRequestSize"] = 1000
        clean_doc["producerRequestSize"] = 1000
        clean_doc["clientResponseSize"] = 1000
        clean_doc["producerResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = 100
        
        clean_doc2 = clean_doc.copy()
        clean_doc2["_id"] = "id2"
        client2 = client.copy()
        client2["timestamp"] = datetime.strptime("5/10/2017 10:30:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000
        clean_doc2["client"] = client2
        clean_doc2["producer"] = client2
        
        clean_documents = [clean_doc, clean_doc2]

        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data("failed_request_ratio", agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])

        self.assertEqual(1, len(data))
        self.assertEqual(2, data[data.succeeded].iloc[0]["count"])

        # Clean before exit
        self.mongodb_h.remove_all()
        
    def test_aggregate_data_for_failed_request_ratio_model_two_queries_in_same_period_different_values(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": client, "producer": client}
        clean_doc["clientRequestSize"] = 1000
        clean_doc["producerRequestSize"] = 1000
        clean_doc["clientResponseSize"] = 1000
        clean_doc["producerResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = 100
        
        clean_doc2 = clean_doc.copy()
        clean_doc2["_id"] = "id2"
        client2 = client.copy()
        client2["succeeded"] = False
        client2["timestamp"] = datetime.strptime("5/10/2017 10:30:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000
        clean_doc2["client"] = client2
        clean_doc2["producer"] = client2
        clean_documents = [clean_doc, clean_doc2]

        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data("failed_request_ratio", agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])

        self.assertEqual(2, len(data))
        self.assertEqual(1, data[data.succeeded].iloc[0]["count"])
        self.assertEqual(1, data[~data.succeeded].iloc[0]["count"])

        # Clean before exit
        self.mongodb_h.remove_all()
        
    def test_aggregate_data_for_failed_request_ratio_model_two_queries_in_different_periods_same_values(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": client, "producer": client}
        clean_doc["clientRequestSize"] = 1000
        clean_doc["producerRequestSize"] = 1000
        clean_doc["clientResponseSize"] = 1000
        clean_doc["producerResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = 100
        
        clean_doc2 = clean_doc.copy()
        clean_doc2["_id"] = "id2"
        client2 = client.copy()
        client2["timestamp"] = datetime.strptime("5/11/2017 10:30:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000
        clean_doc2["client"] = client2
        clean_doc2["producer"] = client2
        clean_documents = [clean_doc, clean_doc2]

        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data("failed_request_ratio", agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])

        self.assertEqual(2, len(data))
        self.assertEqual(2, sum(data.succeeded))
        self.assertEqual(1, data[data.succeeded].iloc[0]["count"])

        # Clean before exit
        self.mongodb_h.remove_all()
        
    def test_aggregate_data_for_failed_request_ratio_model_two_queries_limited_start_time(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": client, "producer": client}
        clean_doc["clientRequestSize"] = 1000
        clean_doc["producerRequestSize"] = 1000
        clean_doc["clientResponseSize"] = 1000
        clean_doc["producerResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = 100
        
        clean_doc2 = clean_doc.copy()
        clean_doc2["_id"] = "id2"
        client2 = client.copy()
        client2["timestamp"] = datetime.strptime("9/11/2017 10:30:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000
        clean_doc2["client"] = client2
        clean_doc2["producer"] = client2
        clean_documents = [clean_doc, clean_doc2]

        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data("failed_request_ratio", agg_minutes=60,
                                              start_time=datetime.strptime("7/11/2017 10:30:00",
                                                                           "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                                              end_time=None, ids_to_exclude=[])
        print(data)
        self.assertEqual(1, len(data))
        self.assertEqual(1, sum(data.succeeded))
        self.assertEqual(1, data[data.succeeded].iloc[0]["count"])
        self.assertEqual(["id2"], data[data.succeeded].iloc[0]["request_ids"])

        # Clean before exit
        self.mongodb_h.remove_all()
        
    def test_aggregate_data_for_failed_request_ratio_model_two_queries_limited_end_time(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": client, "producer": client}
        clean_doc["clientRequestSize"] = 1000
        clean_doc["producerRequestSize"] = 1000
        clean_doc["clientResponseSize"] = 1000
        clean_doc["producerResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = 100
        
        clean_doc2 = clean_doc.copy()
        clean_doc2["_id"] = "id2"
        client2 = client.copy()
        client2["timestamp"] = datetime.strptime("9/11/2017 10:30:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000
        clean_doc2["client"] = client2
        clean_doc2["producer"] = client2
        clean_documents = [clean_doc, clean_doc2]

        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data("failed_request_ratio", agg_minutes=60,
                                              start_time=None,
                                              end_time=datetime.strptime("7/11/2017 10:30:00",
                                                                         "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                                              ids_to_exclude=[])
        print(data)
        self.assertEqual(1, len(data))
        self.assertEqual(1, sum(data.succeeded))
        self.assertEqual(1, data[data.succeeded].iloc[0]["count"])
        self.assertEqual(["id1"], data[data.succeeded].iloc[0]["request_ids"])

        # Clean before exit
        self.mongodb_h.remove_all()
        
    def test_aggregate_data_for_failed_request_ratio_model_two_queries_excluded_ids(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": client, "producer": client}
        clean_doc["clientRequestSize"] = 1000
        clean_doc["producerRequestSize"] = 1000
        clean_doc["clientResponseSize"] = 1000
        clean_doc["producerResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = 100
        
        clean_doc2 = clean_doc.copy()
        clean_doc2["_id"] = "id2"
        client2 = client.copy()
        client2["timestamp"] = datetime.strptime("9/11/2017 10:30:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000
        clean_doc2["client"] = client2
        clean_doc2["producer"] = client2
        clean_documents = [clean_doc, clean_doc2]

        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data("failed_request_ratio", agg_minutes=60,
                                              start_time=None,
                                              end_time=None,
                                              ids_to_exclude=["id2"])
        print(data)
        self.assertEqual(1, len(data))
        self.assertEqual(1, sum(data.succeeded))
        self.assertEqual(1, data[data.succeeded].iloc[0]["count"])
        self.assertEqual(["id1"], data[data.succeeded].iloc[0]["request_ids"])

        # Clean before exit
        self.mongodb_h.remove_all()
    
    def test_aggregate_data_for_duplicate_message_id_model_single_query(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": client, "producer": client}
        clean_doc["clientRequestSize"] = 1000
        clean_doc["producerRequestSize"] = 1000
        clean_doc["clientResponseSize"] = 1000
        clean_doc["producerResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = 100
        clean_documents = [clean_doc]

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data("duplicate_message_ids", agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])

        self.assertEqual(0, len(data))

        # Clean before exit
        self.mongodb_h.remove_all()
        
    def test_aggregate_data_for_duplicate_message_id_model_two_queries_same_period_different_ids(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": client, "producer": client}
        clean_doc["clientRequestSize"] = 1000
        clean_doc["producerRequestSize"] = 1000
        clean_doc["clientResponseSize"] = 1000
        clean_doc["producerResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = 100
        
        clean_doc2 = clean_doc.copy()
        clean_doc2["_id"] = "id2"
        client2 = client.copy()
        client2["timestamp"] = datetime.strptime("5/10/2017 10:30:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000
        client2["messageId"] = "mID2"
        clean_doc2["client"] = client2
        clean_doc2["producer"] = client2
        
        clean_documents = [clean_doc, clean_doc2]

        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data("duplicate_message_ids", agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])

        self.assertEqual(0, len(data))

        # Clean before exit
        self.mongodb_h.remove_all()
        
    def test_aggregate_data_for_duplicate_message_id_model_two_queries_same_period_same_ids(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": client, "producer": client}
        clean_doc["clientRequestSize"] = 1000
        clean_doc["producerRequestSize"] = 1000
        clean_doc["clientResponseSize"] = 1000
        clean_doc["producerResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = 100
        
        clean_doc2 = clean_doc.copy()
        clean_doc2["_id"] = "id2"
        client2 = client.copy()
        client2["timestamp"] = datetime.strptime("5/10/2017 10:30:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000
        clean_doc2["client"] = client2
        clean_doc2["producer"] = client2
        
        clean_documents = [clean_doc, clean_doc2]

        self.mongodb_h.add_clean_documents(clean_documents)
        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data("duplicate_message_ids", agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])

        self.assertEqual(1, len(data))
        self.assertEqual(2, data.iloc[0]["message_id_count"])

        # Clean before exit
        self.mongodb_h.remove_all()
        
    def test_aggregate_data_for_duplicate_message_id_model_two_queries_different_periods_same_ids(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": client, "producer": client}
        clean_doc["clientRequestSize"] = 1000
        clean_doc["producerRequestSize"] = 1000
        clean_doc["clientResponseSize"] = 1000
        clean_doc["producerResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = 100
        
        clean_doc2 = clean_doc.copy()
        clean_doc2["_id"] = "id2"
        client2 = client.copy()
        client2["timestamp"] = datetime.strptime("5/12/2017 10:30:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000
        clean_doc2["client"] = client2
        clean_doc2["producer"] = client2
        
        clean_documents = [clean_doc, clean_doc2]

        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data("duplicate_message_ids", agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])

        self.assertEqual(0, len(data))

        # Clean before exit
        self.mongodb_h.remove_all()
        
    def test_aggregate_data_for_time_sync_model_no_anomaly_found(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": client, "producer": client}
        clean_doc["clientRequestSize"] = 1000
        clean_doc["producerRequestSize"] = 1000
        clean_doc["clientResponseSize"] = 1000
        clean_doc["producerResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = 100
        clean_documents = [clean_doc]
        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data(model_type="time_sync_errors", metric="responseNwDuration", threshold=0,
                                              agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])

        self.assertEqual(0, len(data))

        # Clean before exit
        self.mongodb_h.remove_all()
        
    def test_aggregate_data_for_time_sync_model_anomaly_found(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": client, "producer": client}
        clean_doc["clientRequestSize"] = 1000
        clean_doc["producerRequestSize"] = 1000
        clean_doc["clientResponseSize"] = 1000
        clean_doc["producerResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = -100
        clean_documents = [clean_doc]
        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data(model_type="time_sync_errors", metric="responseNwDuration", threshold=0,
                                              agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])

        self.assertEqual(1, len(data))
        self.assertEqual(1, data.iloc[0]["erroneous_count"])
        self.assertEqual(-100, data.iloc[0]["avg_erroneous_diff"])
        self.assertEqual(1, data.iloc[0]["request_count"])

        # Clean before exit
        self.mongodb_h.remove_all()
        
    def test_aggregate_data_for_time_sync_model_two_queries_in_same_period_one_anomalous(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": client, "producer": client}
        clean_doc["clientRequestSize"] = 1000
        clean_doc["producerRequestSize"] = 1000
        clean_doc["clientResponseSize"] = 1000
        clean_doc["producerResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = 100
        
        clean_doc2 = clean_doc.copy()
        clean_doc2["_id"] = "id2"
        client2 = client.copy()
        client2["timestamp"] = datetime.strptime("5/10/2017 10:30:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000
        clean_doc2["client"] = client2
        clean_doc2["producer"] = client2
        clean_doc2["responseNwDuration"] = -100
        
        clean_documents = [clean_doc, clean_doc2]
        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data(model_type="time_sync_errors", metric="responseNwDuration", threshold=0,
                                              agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])

        self.assertEqual(1, len(data))
        self.assertEqual(1, data.iloc[0]["erroneous_count"])
        self.assertEqual(-100, data.iloc[0]["avg_erroneous_diff"])
        self.assertEqual(2, data.iloc[0]["request_count"])

        # Clean before exit
        self.mongodb_h.remove_all()
        
    def test_aggregate_data_for_time_sync_model_two_queries_in_same_period_both_anomalous(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": client, "producer": client}
        clean_doc["clientRequestSize"] = 1000
        clean_doc["producerRequestSize"] = 1000
        clean_doc["clientResponseSize"] = 1000
        clean_doc["producerResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = -200
        
        clean_doc2 = clean_doc.copy()
        clean_doc2["_id"] = "id2"
        client2 = client.copy()
        client2["timestamp"] = datetime.strptime("5/10/2017 10:30:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000
        clean_doc2["client"] = client2
        clean_doc2["producer"] = client2
        clean_doc2["responseNwDuration"] = -100
        
        clean_documents = [clean_doc, clean_doc2]
        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data(model_type="time_sync_errors", metric="responseNwDuration", threshold=0,
                                              agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])

        self.assertEqual(1, len(data))
        self.assertEqual(2, data.iloc[0]["erroneous_count"])
        self.assertEqual(-150, data.iloc[0]["avg_erroneous_diff"])
        self.assertEqual(2, data.iloc[0]["request_count"])

        # Clean before exit
        self.mongodb_h.remove_all()
      
    def test_aggregate_data_for_historic_averages_model_single_query(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": client, "producer": client}
        clean_doc["clientRequestSize"] = 1000
        clean_doc["producerRequestSize"] = 1000
        clean_doc["clientResponseSize"] = 1000
        clean_doc["producerResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = 100
        clean_documents = [clean_doc]
        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data_for_historic_averages_model(agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])

        self.assertEqual(1, len(data))
        self.assertEqual(1, data.iloc[0]["request_count"])
        self.assertEqual(1000, data.iloc[0]["mean_request_size"])
        self.assertEqual(1000, data.iloc[0]["mean_response_size"])
        self.assertEqual(100, data.iloc[0]["mean_client_duration"])
        self.assertEqual(100, data.iloc[0]["mean_producer_duration"])

        # Clean before exit
        self.mongodb_h.remove_all()
        
    def test_aggregate_data_for_historic_averages_model_single_query_client_missing(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": None, "producer": client}
        clean_doc["producerRequestSize"] = 1000
        clean_doc["producerResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = 100
        clean_documents = [clean_doc]
        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data_for_historic_averages_model(agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])
        print(data)

        self.assertEqual(1, len(data))
        self.assertEqual(1, data.iloc[0]["request_count"])
        self.assertEqual(1000, data.iloc[0]["mean_request_size"])
        self.assertEqual(1000, data.iloc[0]["mean_response_size"])
        self.assertEqual(None, data.iloc[0]["mean_client_duration"])
        self.assertEqual(100, data.iloc[0]["mean_producer_duration"])

        # Clean before exit
        self.mongodb_h.remove_all()
        
    def test_aggregate_data_for_historic_averages_model_single_query_producer_missing(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": client, "producer": None}
        clean_doc["clientRequestSize"] = 1000
        clean_doc["clientResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = 100
        clean_documents = [clean_doc]
        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data_for_historic_averages_model(agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])

        self.assertEqual(1, len(data))
        self.assertEqual(1, data.iloc[0]["request_count"])
        self.assertEqual(1000, data.iloc[0]["mean_request_size"])
        self.assertEqual(1000, data.iloc[0]["mean_response_size"])
        self.assertEqual(100, data.iloc[0]["mean_client_duration"])
        self.assertEqual(None, data.iloc[0]["mean_producer_duration"])

        # Clean before exit
        self.mongodb_h.remove_all()
        
    def test_aggregate_data_for_historic_averages_model_single_query_client_producer_different(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": client, "producer": client}
        clean_doc["clientRequestSize"] = 1000
        clean_doc["producerRequestSize"] = 500
        clean_doc["clientResponseSize"] = 1000
        clean_doc["producerResponseSize"] = 500
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = 100
        clean_documents = [clean_doc]
        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data_for_historic_averages_model(agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])

        self.assertEqual(1, len(data))
        self.assertEqual(1, data.iloc[0]["request_count"])
        self.assertEqual(1000, data.iloc[0]["mean_request_size"])
        self.assertEqual(1000, data.iloc[0]["mean_response_size"])
        self.assertEqual(100, data.iloc[0]["mean_client_duration"])
        self.assertEqual(100, data.iloc[0]["mean_producer_duration"])

        # Clean before exit
        self.mongodb_h.remove_all()
        
    def test_aggregate_data_for_historic_averages_model_two_queries_in_same_period(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": client, "producer": client}
        clean_doc["clientRequestSize"] = 1000
        clean_doc["producerRequestSize"] = 1000
        clean_doc["clientResponseSize"] = 1000
        clean_doc["producerResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = 100
        
        clean_doc2 = clean_doc.copy()
        clean_doc2["_id"] = "id2"
        client2 = client.copy()
        client2["timestamp"] = datetime.strptime("5/10/2017 10:30:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000
        clean_doc2["client"] = client2
        clean_doc2["producer"] = client2
        
        clean_documents = [clean_doc, clean_doc2]
        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data_for_historic_averages_model(agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])

        self.assertEqual(1, len(data))
        self.assertEqual(2, data.iloc[0]["request_count"])
        self.assertEqual(1000, data.iloc[0]["mean_request_size"])
        self.assertEqual(1000, data.iloc[0]["mean_response_size"])
        self.assertEqual(100, data.iloc[0]["mean_client_duration"])
        self.assertEqual(100, data.iloc[0]["mean_producer_duration"])

        # Clean before exit
        self.mongodb_h.remove_all()
        
    def test_aggregate_data_for_historic_averages_model_two_queries_in_same_period_one_not_successful(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": client, "producer": client}
        clean_doc["clientRequestSize"] = 1000
        clean_doc["producerRequestSize"] = 1000
        clean_doc["clientResponseSize"] = 1000
        clean_doc["producerResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = 100
        
        clean_doc2 = clean_doc.copy()
        clean_doc2["_id"] = "id2"
        client2 = client.copy()
        client2["timestamp"] = datetime.strptime("5/10/2017 10:30:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000
        client2["succeeded"] = False
        clean_doc2["client"] = client2
        clean_doc2["producer"] = client2
        
        clean_documents = [clean_doc, clean_doc2]
        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data_for_historic_averages_model(agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])

        self.assertEqual(1, len(data))
        self.assertEqual(1, data.iloc[0]["request_count"])
        self.assertEqual(1000, data.iloc[0]["mean_request_size"])
        self.assertEqual(1000, data.iloc[0]["mean_response_size"])
        self.assertEqual(100, data.iloc[0]["mean_client_duration"])
        self.assertEqual(100, data.iloc[0]["mean_producer_duration"])

        # Clean before exit
        self.mongodb_h.remove_all()
        
    def test_aggregate_data_for_historic_averages_model_two_queries_in_same_period_different_service_calls(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": client, "producer": client}
        clean_doc["clientRequestSize"] = 1000
        clean_doc["producerRequestSize"] = 1000
        clean_doc["clientResponseSize"] = 1000
        clean_doc["producerResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = 100
        
        clean_doc2 = clean_doc.copy()
        clean_doc2["_id"] = "id2"
        client2 = client.copy()
        client2["timestamp"] = datetime.strptime("5/10/2017 10:30:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000
        client2["service_call"] = "sc2"
        clean_doc2["client"] = client2
        clean_doc2["producer"] = client2
        clean_doc2["clientRequestSize"] = 500
        clean_doc2["clientResponseSize"] = 500
        clean_doc2["totalDuration"] = 50
        clean_doc2["producerDurationProducerView"] = 50
        
        clean_documents = [clean_doc, clean_doc2]
        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data_for_historic_averages_model(agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])

        self.assertEqual(2, len(data))
        self.assertEqual(1, data[data.service_call == "sc1"].iloc[0]["request_count"])
        self.assertEqual(1, data[data.service_call == "sc2"].iloc[0]["request_count"])
        self.assertEqual(1000, data[data.service_call == "sc1"].iloc[0]["mean_request_size"])
        self.assertEqual(500, data[data.service_call == "sc2"].iloc[0]["mean_request_size"])
        self.assertEqual(1000, data[data.service_call == "sc1"].iloc[0]["mean_response_size"])
        self.assertEqual(500, data[data.service_call == "sc2"].iloc[0]["mean_response_size"])
        self.assertEqual(100, data[data.service_call == "sc1"].iloc[0]["mean_client_duration"])
        self.assertEqual(50, data[data.service_call == "sc2"].iloc[0]["mean_client_duration"])
        self.assertEqual(100, data[data.service_call == "sc1"].iloc[0]["mean_producer_duration"])
        self.assertEqual(50, data[data.service_call == "sc2"].iloc[0]["mean_producer_duration"])

        # Clean before exit
        self.mongodb_h.remove_all()
        
    def test_aggregate_data_for_historic_averages_model_two_queries_different_periods_same_service_call(self):

        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()

        # Add clean data
        client = {"timestamp": datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
                  "service_call": "sc1",
                  "succeeded": True,
                  "messageId": "mID"}
        clean_doc = {"client": client, "producer": client}
        clean_doc["clientRequestSize"] = 1000
        clean_doc["producerRequestSize"] = 1000
        clean_doc["clientResponseSize"] = 1000
        clean_doc["producerResponseSize"] = 1000
        clean_doc["_id"] = "id1"
        clean_doc["correctorStatus"] = "done"
        clean_doc["totalDuration"] = 100
        clean_doc["producerDurationProducerView"] = 100
        clean_doc["requestNwDuration"] = 100
        clean_doc["responseNwDuration"] = 100
        
        clean_doc2 = clean_doc.copy()
        clean_doc2["_id"] = "id2"
        client2 = client.copy()
        client2["timestamp"] = datetime.strptime("5/12/2017 10:30:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000
        clean_doc2["client"] = client2
        clean_doc2["producer"] = client2
        clean_doc2["clientRequestSize"] = 500
        clean_doc2["clientResponseSize"] = 500
        clean_doc2["totalDuration"] = 50
        clean_doc2["producerDurationProducerView"] = 50
        
        clean_documents = [clean_doc, clean_doc2]
        self.mongodb_h.add_clean_documents(clean_documents)

        # Run AnalyzerDatabaseManager
        data = self.db_manager.aggregate_data_for_historic_averages_model(agg_minutes=60, start_time=None, end_time=None, ids_to_exclude=[])
        
        print(data)

        self.assertEqual(2, len(data))
        self.assertEqual(1, data[data.timestamp.dt.month == 10].iloc[0]["request_count"])
        self.assertEqual(1, data[data.timestamp.dt.month == 12].iloc[0]["request_count"])
        self.assertEqual(1000, data[data.timestamp.dt.month == 10].iloc[0]["mean_request_size"])
        self.assertEqual(500, data[data.timestamp.dt.month == 12].iloc[0]["mean_request_size"])
        self.assertEqual(1000, data[data.timestamp.dt.month == 10].iloc[0]["mean_response_size"])
        self.assertEqual(500, data[data.timestamp.dt.month == 12].iloc[0]["mean_response_size"])
        self.assertEqual(100, data[data.timestamp.dt.month == 10].iloc[0]["mean_client_duration"])
        self.assertEqual(50, data[data.timestamp.dt.month == 12].iloc[0]["mean_client_duration"])
        self.assertEqual(100, data[data.timestamp.dt.month == 10].iloc[0]["mean_producer_duration"])
        self.assertEqual(50, data[data.timestamp.dt.month == 12].iloc[0]["mean_producer_duration"])

        # Clean before exit
        self.mongodb_h.remove_all()
