import unittest
from unittest.mock import Mock

from integration_tests.helpers import cl_db_handler, ci_analyzer_db_handler
from integration_tests.ci_analyzer.ci_analyzer_settings import Settings

from analysis_module.analyzer.AnalyzerDatabaseManager import AnalyzerDatabaseManager

import datetime
from dateutil.relativedelta import relativedelta
import time

import pandas as pd


class TestAnalyzerTimeperiodsCI(unittest.TestCase):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # load the test database settings
        settings = Settings()
        
        # initialize a helper for operations the test database
        self.mongodb_h = cl_db_handler.MongoDBHandler(settings.MONGODB_USER, settings.MONGODB_PWD, settings.MONGODB_SERVER)
        self.mongodb_analyzer_h = ci_analyzer_db_handler.MongoAnalyzerDBHandler(settings.MONGODB_USER,
                                                                                settings.MONGODB_PWD,
                                                                                settings.MONGODB_SERVER)
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
        config.incident_expiration_time = 14400  # minutes
        config.training_period_time = 3  # months
        config.corrector_buffer_time = 14400
        self._config = config
        
        # set up the Analyzer database manager to be tested
        self.db_manager = AnalyzerDatabaseManager(db_config, config)
    
    def test_get_service_calls_for_train_stages_empty_clean_data(self):
        
        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()
        self.mongodb_analyzer_h.remove_all()
        
        # assign timestamp values
        current_time = datetime.datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        time_first_model = (current_time - relativedelta(months=self._config.training_period_time))
        time_second_model = (current_time - datetime.timedelta(minutes=self._config.incident_expiration_time))
        
        # add data
        first_timestamp_docs = []
        clean_documents = []
        self.mongodb_h.add_clean_documents(clean_documents)
        self.mongodb_analyzer_h.add_service_call_first_timestamps(first_timestamp_docs)
        
        # make query
        sc_regular, sc_first_model, sc_second_model = self.db_manager.get_service_calls_for_train_stages(time_first_model,
                                                                                                         time_second_model)
        # test
        self.assertEqual(0, len(sc_regular))
        self.assertEqual(0, len(sc_first_model))
        self.assertEqual(0, len(sc_second_model))
        
        # Clean before exit
        self.mongodb_h.remove_all()
        self.mongodb_analyzer_h.remove_all()
    
    def test_add_first_request_timestamps_from_clean_data(self):
        
        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()
        self.mongodb_analyzer_h.remove_all()
        
        # assign timestamp values
        current_time = datetime.datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        time_first_model = (current_time - relativedelta(months=self._config.training_period_time))
        time_second_model = (current_time - datetime.timedelta(minutes=self._config.incident_expiration_time))
        
        # add data
        client = {"timestamp": datetime.datetime.strptime("5/6/2017 10:00:00", "%d/%m/%Y %H:%M:%S").timestamp() * 1000,
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
        
        # make query
        self.db_manager.add_first_request_timestamps_from_clean_data()
        sc_regular, sc_first_model, sc_second_model = self.db_manager.get_service_calls_for_train_stages(time_first_model,
                                                                                                         time_second_model)
        # test
        self.assertEqual(0, len(sc_regular))
        self.assertEqual(1, len(sc_first_model))
        self.assertEqual(0, len(sc_second_model))
        
        # Clean before exit
        self.mongodb_h.remove_all()
        self.mongodb_analyzer_h.remove_all()
    
    def test_get_service_calls_for_train_stages_regular(self):
        
        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()
        self.mongodb_analyzer_h.remove_all()
        
        # assign timestamp values
        current_time = datetime.datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        time_first_model = (current_time - relativedelta(months=self._config.training_period_time))
        time_second_model = (current_time - datetime.timedelta(minutes=self._config.incident_expiration_time))
        
        ts = datetime.datetime.strptime("5/6/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        # add data
        doc = {"first_request_timestamp": ts,
               "first_model_train_timestamp": ts + relativedelta(months=self._config.training_period_time),
               "first_incident_timestamp": ts + relativedelta(months=self._config.training_period_time),
               "first_model_retrain_timestamp": ts + relativedelta(months=self._config.training_period_time,
                                                                   minutes=self._config.incident_expiration_time),
               "service_call": "sc1"}
        documents = [doc]
        self.mongodb_analyzer_h.add_service_call_first_timestamps(documents)
        
        # make query
        sc_regular, sc_first_model, sc_second_model = self.db_manager.get_service_calls_for_train_stages(time_first_model,
                                                                                                         time_second_model)
        # test
        self.assertEqual(1, len(sc_regular))
        self.assertEqual(0, len(sc_first_model))
        self.assertEqual(0, len(sc_second_model))
        
        # Clean before exit
        self.mongodb_h.remove_all()
        self.mongodb_analyzer_h.remove_all()
        
    def test_get_service_calls_for_train_stages_retrain(self):
        
        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()
        self.mongodb_analyzer_h.remove_all()
        
        # assign timestamp values
        current_time = datetime.datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        time_first_model = (current_time - relativedelta(months=self._config.training_period_time))
        time_second_model = (current_time - datetime.timedelta(minutes=self._config.incident_expiration_time))
        
        ts = datetime.datetime.strptime("5/6/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        # add data
        doc = {"first_request_timestamp": ts,
               "first_model_train_timestamp": ts + relativedelta(months=self._config.training_period_time),
               "first_incident_timestamp": ts + relativedelta(months=self._config.training_period_time),
               "first_model_retrain_timestamp": None,
               "service_call": "sc1"}
        documents = [doc]
        self.mongodb_analyzer_h.add_service_call_first_timestamps(documents)
        
        # make query
        sc_regular, sc_first_model, sc_second_model = self.db_manager.get_service_calls_for_train_stages(time_first_model,
                                                                                                         time_second_model)
        # test
        self.assertEqual(0, len(sc_regular))
        self.assertEqual(0, len(sc_first_model))
        self.assertEqual(1, len(sc_second_model))
        
        # Clean before exit
        self.mongodb_h.remove_all()
        self.mongodb_analyzer_h.remove_all()
        
    def test_get_service_calls_for_train_stages_first_train(self):
        
        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()
        self.mongodb_analyzer_h.remove_all()
        
        # assign timestamp values
        current_time = datetime.datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        time_first_model = (current_time - relativedelta(months=self._config.training_period_time))
        time_second_model = (current_time - datetime.timedelta(minutes=self._config.incident_expiration_time))
        
        ts = datetime.datetime.strptime("5/6/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        # add data
        doc = {"first_request_timestamp": ts,
               "first_model_train_timestamp": None,
               "first_incident_timestamp": None,
               "first_model_retrain_timestamp": None,
               "service_call": "sc1"}
        documents = [doc]
        self.mongodb_analyzer_h.add_service_call_first_timestamps(documents)
        
        # make query
        sc_regular, sc_first_model, sc_second_model = self.db_manager.get_service_calls_for_train_stages(time_first_model,
                                                                                                         time_second_model)
        # test
        self.assertEqual(0, len(sc_regular))
        self.assertEqual(1, len(sc_first_model))
        self.assertEqual(0, len(sc_second_model))
        
        # Clean before exit
        self.mongodb_h.remove_all()
        self.mongodb_analyzer_h.remove_all()
        
    def test_get_service_calls_for_train_stages_none(self):
        
        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()
        self.mongodb_analyzer_h.remove_all()
        
        # assign timestamp values
        current_time = datetime.datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        time_first_model = (current_time - relativedelta(months=self._config.training_period_time))
        time_second_model = (current_time - datetime.timedelta(minutes=self._config.incident_expiration_time))
        
        ts = datetime.datetime.strptime("5/8/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        # add data
        doc = {"first_request_timestamp": ts,
               "first_model_train_timestamp": None,
               "first_incident_timestamp": None,
               "first_model_retrain_timestamp": None,
               "service_call": "sc1"}
        documents = [doc]
        self.mongodb_analyzer_h.add_service_call_first_timestamps(documents)
        
        # make query
        sc_regular, sc_first_model, sc_second_model = self.db_manager.get_service_calls_for_train_stages(time_first_model,
                                                                                                         time_second_model)
        # test
        self.assertEqual(0, len(sc_regular))
        self.assertEqual(0, len(sc_first_model))
        self.assertEqual(0, len(sc_second_model))
        
        # Clean before exit
        self.mongodb_h.remove_all()
        self.mongodb_analyzer_h.remove_all()
    
    def test_get_data_for_train_stages_empty_data(self):
        
        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()
        self.mongodb_analyzer_h.remove_all()
        
        sc_regular = pd.DataFrame()
        sc_first_model = pd.DataFrame()
        sc_second_model = pd.DataFrame()
        metric_names = ["request_count"]
        
        # assign timestamp values
        current_time = datetime.datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        last_fit_timestamp = (current_time - datetime.timedelta(minutes=self._config.incident_expiration_time + 10))
        max_incident_creation_timestamp = (current_time - datetime.timedelta(minutes=self._config.incident_expiration_time))
        max_request_timestamp = (current_time - datetime.timedelta(minutes=self._config.corrector_buffer_time))
        agg_minutes = 60
        
        data_regular, data_first_train, data_first_retrain = self.db_manager.get_data_for_train_stages(
            sc_regular=sc_regular,
            sc_first_model=sc_first_model,
            sc_second_model=sc_second_model,
            relevant_anomalous_metrics=metric_names,
            max_incident_creation_timestamp=max_incident_creation_timestamp,
            last_fit_timestamp=last_fit_timestamp,
            agg_minutes=agg_minutes,
            max_request_timestamp=max_request_timestamp)
        
        self.assertEqual(0, len(data_regular))
        self.assertEqual(0, len(data_first_train))
        self.assertEqual(0, len(data_first_retrain))
        
        # Clean before exit
        self.mongodb_h.remove_all()
        self.mongodb_analyzer_h.remove_all()
        
    def test_get_data_for_train_stages_regular(self):
        
        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()
        self.mongodb_analyzer_h.remove_all()
        
        # assign timestamp values
        current_time = datetime.datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        ts = datetime.datetime.strptime("5/6/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        last_fit_timestamp = ts
        max_incident_creation_timestamp = (current_time - datetime.timedelta(minutes=self._config.incident_expiration_time))
        max_request_timestamp = (current_time - datetime.timedelta(minutes=self._config.corrector_buffer_time))
        agg_minutes = 60
        time_first_model = (current_time - relativedelta(months=self._config.training_period_time))
        time_second_model = (current_time - datetime.timedelta(minutes=self._config.incident_expiration_time))
        
        # add data
        doc = {"first_request_timestamp": ts,
               "first_model_train_timestamp": ts + relativedelta(months=self._config.training_period_time),
               "first_incident_timestamp": ts + relativedelta(months=self._config.training_period_time),
               "first_model_retrain_timestamp": ts + relativedelta(months=self._config.training_period_time,
                                                                   minutes=self._config.incident_expiration_time),
               "service_call": "sc1"}
        documents = [doc]
        self.mongodb_analyzer_h.add_service_call_first_timestamps(documents)
        
        # add data
        client = {"timestamp": (current_time -
                                datetime.timedelta(minutes=self._config.incident_expiration_time + 5)).timestamp() * 1000,
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
        
        # make query
        sc_regular, sc_first_model, sc_second_model = self.db_manager.get_service_calls_for_train_stages(time_first_model,
                                                                                                         time_second_model)
        
        metric_names = ["request_count"]
        data_regular, data_first_train, data_first_retrain = self.db_manager.get_data_for_train_stages(
            sc_regular=sc_regular,
            sc_first_model=sc_first_model,
            sc_second_model=sc_second_model,
            relevant_anomalous_metrics=metric_names,
            max_incident_creation_timestamp=max_incident_creation_timestamp,
            last_fit_timestamp=last_fit_timestamp,
            agg_minutes=agg_minutes,
            max_request_timestamp=max_request_timestamp)
        
        self.assertEqual(1, len(data_regular))
        self.assertEqual(0, len(data_first_train))
        self.assertEqual(0, len(data_first_retrain))
        
        # Clean before exit
        self.mongodb_h.remove_all()
        self.mongodb_analyzer_h.remove_all()
        
    def test_get_data_for_train_stages_regular_incident(self):
        
        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()
        self.mongodb_analyzer_h.remove_all()
        
        # assign timestamp values
        current_time = datetime.datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        ts = datetime.datetime.strptime("5/6/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        last_fit_timestamp = ts
        max_incident_creation_timestamp = (current_time - datetime.timedelta(minutes=self._config.incident_expiration_time))
        request_date = (current_time -
                        datetime.timedelta(minutes=self._config.incident_expiration_time + 5))
        time_first_model = (current_time - relativedelta(months=self._config.training_period_time))
        time_second_model = (current_time - datetime.timedelta(minutes=self._config.incident_expiration_time))
        max_request_timestamp = (current_time - datetime.timedelta(minutes=self._config.corrector_buffer_time))
        agg_minutes = 60
        
        # add data
        doc = {"first_request_timestamp": ts,
               "first_model_train_timestamp": ts + relativedelta(months=self._config.training_period_time),
               "first_incident_timestamp": ts + relativedelta(months=self._config.training_period_time),
               "first_model_retrain_timestamp": ts + relativedelta(months=self._config.training_period_time,
                                                                   minutes=self._config.incident_expiration_time),
               "service_call": "sc1"}
        documents = [doc]
        self.mongodb_analyzer_h.add_service_call_first_timestamps(documents)
        
        # add incident
        incident = {"service_call": "sc1", "request_ids": ["id1"], "incident_status": "incident",
                    "incident_creation_timestamp": max_incident_creation_timestamp - datetime.timedelta(minutes=120),
                    "anomalous_metric": "request_count",
                    "period_end_time": request_date + datetime.timedelta(minutes=30)}
        self.mongodb_analyzer_h.add_incidents([incident])
        
        # add clean data
        client = {"timestamp": request_date.timestamp() * 1000,
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
        
        # make query
        sc_regular, sc_first_model, sc_second_model = self.db_manager.get_service_calls_for_train_stages(time_first_model,
                                                                                                         time_second_model)
        
        metric_names = ["request_count"]
        data_regular, data_first_train, data_first_retrain = self.db_manager.get_data_for_train_stages(
            sc_regular=sc_regular,
            sc_first_model=sc_first_model,
            sc_second_model=sc_second_model,
            relevant_anomalous_metrics=metric_names,
            max_incident_creation_timestamp=max_incident_creation_timestamp,
            last_fit_timestamp=last_fit_timestamp,
            agg_minutes=agg_minutes,
            max_request_timestamp=max_request_timestamp)
        
        self.assertEqual(0, len(data_regular))
        self.assertEqual(0, len(data_first_train))
        self.assertEqual(0, len(data_first_retrain))
        
        # Clean before exit
        self.mongodb_h.remove_all()
        self.mongodb_analyzer_h.remove_all()
        
    def test_update_first_train_retrain_timestamps(self):
        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()
        self.mongodb_analyzer_h.remove_all()
        
        # add data
        ts = datetime.datetime.strptime("5/6/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        doc = {"first_request_timestamp": ts,
               "first_model_train_timestamp": None,
               "first_incident_timestamp": None,
               "first_model_retrain_timestamp": None,
               "service_call": "sc1"}
        documents = [doc]
        self.mongodb_analyzer_h.add_service_call_first_timestamps(documents)
        
        current_time = datetime.datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        time_first_model = (current_time - relativedelta(months=self._config.training_period_time))
        time_second_model = (current_time - datetime.timedelta(minutes=self._config.incident_expiration_time))
        
        _, sc_first_model, sc_second_model = self.db_manager.get_service_calls_for_train_stages(time_first_model,
                                                                                                time_second_model)
        
        self.db_manager.update_first_train_retrain_timestamps(sc_first_model, sc_second_model, current_time)
        data = self.db_manager.get_first_timestamps_for_service_calls()
        
        self.assertEquals(current_time, data.ix[0, "first_model_train_timestamp"])
        
        # Clean before exit
        self.mongodb_h.remove_all()
        self.mongodb_analyzer_h.remove_all()
    
    def test_get_service_calls_for_transform_stages_none(self):
        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()
        self.mongodb_analyzer_h.remove_all()
        
        # assign timestamp values
        current_time = datetime.datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        
        ts = datetime.datetime.strptime("5/6/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        # add data
        doc = {"first_request_timestamp": ts,
               "first_model_train_timestamp": None,
               "first_incident_timestamp": None,
               "first_model_retrain_timestamp": None,
               "service_call": "sc1"}
        documents = [doc]
        self.mongodb_analyzer_h.add_service_call_first_timestamps(documents)
        
        # make query
        sc_regular, sc_first_incidents = self.db_manager.get_service_calls_for_transform_stages()

        # test
        self.assertEqual(0, len(sc_regular))
        self.assertEqual(0, len(sc_first_incidents))
        
        # Clean before exit
        self.mongodb_h.remove_all()
        self.mongodb_analyzer_h.remove_all()
    
    def test_get_service_calls_for_transform_stages_first_incident(self):
        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()
        self.mongodb_analyzer_h.remove_all()
        
        # assign timestamp values
        current_time = datetime.datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        
        ts = datetime.datetime.strptime("5/6/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        # add data
        doc = {"first_request_timestamp": ts,
               "first_model_train_timestamp": ts + relativedelta(months=self._config.training_period_time),
               "first_incident_timestamp": None,
               "first_model_retrain_timestamp": None,
               "service_call": "sc1"}
        documents = [doc]
        self.mongodb_analyzer_h.add_service_call_first_timestamps(documents)
        
        # make query
        sc_regular, sc_first_incidents = self.db_manager.get_service_calls_for_transform_stages()

        # test
        self.assertEqual(0, len(sc_regular))
        self.assertEqual(1, len(sc_first_incidents))
        
        # Clean before exit
        self.mongodb_h.remove_all()
        self.mongodb_analyzer_h.remove_all()
        
    def test_get_service_calls_for_transform_stages_regular(self):
        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()
        self.mongodb_analyzer_h.remove_all()
        
        # assign timestamp values
        current_time = datetime.datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        
        ts = datetime.datetime.strptime("5/6/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        # add data
        doc = {"first_request_timestamp": ts,
               "first_model_train_timestamp": ts + relativedelta(months=self._config.training_period_time),
               "first_incident_timestamp": ts + relativedelta(months=self._config.training_period_time),
               "first_model_retrain_timestamp": ts + relativedelta(months=self._config.training_period_time,
                                                                   minutes=self._config.incident_expiration_time),
               "service_call": "sc1"}
        documents = [doc]
        self.mongodb_analyzer_h.add_service_call_first_timestamps(documents)
        
        # make query
        sc_regular, sc_first_incidents = self.db_manager.get_service_calls_for_transform_stages()

        # test
        self.assertEqual(1, len(sc_regular))
        self.assertEqual(0, len(sc_first_incidents))
        
        # Clean before exit
        self.mongodb_h.remove_all()
        self.mongodb_analyzer_h.remove_all()
    
    def test_get_data_for_transform_stages_empty_data(self):
        
        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()
        self.mongodb_analyzer_h.remove_all()
        
        sc_regular = pd.DataFrame()
        sc_first_model = pd.DataFrame()
        sc_second_model = pd.DataFrame()
        metric_names = ["request_count"]
        
        # assign timestamp values
        current_time = datetime.datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        last_transform_timestamp = (current_time - datetime.timedelta(minutes=self._config.incident_expiration_time))
        current_transform_timestamp = (current_time - datetime.timedelta(minutes=10))
        agg_minutes = 60
        
        data = self.db_manager.get_data_for_transform_stages(agg_minutes, last_transform_timestamp,
                                                             current_transform_timestamp, pd.DataFrame(), pd.DataFrame())
        
        self.assertEqual(0, len(data))
        
        # Clean before exit
        self.mongodb_h.remove_all()
        self.mongodb_analyzer_h.remove_all()
        
    def test_get_data_for_transform_stages_regular(self):
        
        # Clean database state
        self.mongodb_h.remove_all()
        self.mongodb_h.create_indexes()
        self.mongodb_analyzer_h.remove_all()
        
        # assign timestamp values
        current_time = datetime.datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        ts = datetime.datetime.strptime("5/6/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        last_transform_timestamp = (ts - datetime.timedelta(days=5)).timestamp() * 1000
        current_transform_timestamp = (current_time + datetime.timedelta(minutes=10)).timestamp() * 1000
        agg_minutes = 60
        
        # add data
        doc = {"first_request_timestamp": ts,
               "first_model_train_timestamp": ts + relativedelta(months=self._config.training_period_time),
               "first_incident_timestamp": ts + relativedelta(months=self._config.training_period_time),
               "first_model_retrain_timestamp": ts + relativedelta(months=self._config.training_period_time,
                                                                   minutes=self._config.incident_expiration_time),
               "service_call": "sc1"}
        documents = [doc]
        self.mongodb_analyzer_h.add_service_call_first_timestamps(documents)
        
        # add data
        client = {"timestamp": ts.timestamp() * 1000,
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
        
        # make query
        sc_regular, sc_first_incidents = self.db_manager.get_service_calls_for_transform_stages()
        
        self.assertEqual(1, len(sc_regular))
        self.assertEqual(0, len(sc_first_incidents))
        
        metric_names = ["request_count"]
        data = self.db_manager.get_data_for_transform_stages(agg_minutes, last_transform_timestamp,
                                                             current_transform_timestamp, sc_regular, sc_first_incidents)
        
        self.assertEqual(1, len(data))
        
        # Clean before exit
        self.mongodb_h.remove_all()
        self.mongodb_analyzer_h.remove_all()
