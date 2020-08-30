import os
import unittest
from unittest.mock import MagicMock, Mock

import pandas as pd
import numpy as np
from datetime import datetime

# import os
# ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
# os.chdir(os.path.join(ROOT_DIR, '..'))

from models.FailedRequestRatioModel import FailedRequestRatioModel
from models.DuplicateMessageIdModel import DuplicateMessageIdModel
from models.TimeSyncModel import TimeSyncModel
from models.AveragesByTimeperiodModel import AveragesByTimeperiodModel


class TestAnalyzerModels(unittest.TestCase):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = Mock()
        config.timestamp_field = "timestamp"
        config.service_call_fields = ["service_call"]
        config.failed_request_ratio_threshold = 0.7
        config.historic_averages_thresholds = {'request_count': 0.95}
        self._config = config
        self._time_window = {'agg_window_name': 'hour', 'agg_minutes': 60, 'pd_timeunit': 'h'}
        self._similarity_time_window = {'timeunit_name': 'hour_weekday', 'agg_window': self._time_window,
                                        'similar_periods': ['hour', 'weekday']}
    
    def test_failed_request_ratio_model_empty_dataframe(self):
        model = FailedRequestRatioModel(self._config)
        data = pd.DataFrame()
        anomalies = model.transform(data, self._time_window)
        self.assertEqual(0, len(anomalies))
        
    def test_failed_request_ratio_model_anomaly_found(self):
        model = FailedRequestRatioModel(self._config)
        ts = datetime.now()
        service_call = "sc1"
        request_ids = ["id"]
        data = pd.DataFrame([(ts, service_call, True, 1, request_ids),
                             (ts, service_call, False, 3, request_ids)],
                            columns=["timestamp", "service_call", "succeeded", "count", "request_ids"])
        anomalies = model.transform(data, self._time_window)
        self.assertEqual(1, len(anomalies))
      
    def test_failed_request_ratio_model_anomaly_not_found(self):
        model = FailedRequestRatioModel(self._config)
        ts = datetime.now()
        service_call = "sc1"
        request_ids = ["id"]
        data = pd.DataFrame([(ts, service_call, True, 3, request_ids),
                             (ts, service_call, False, 1, request_ids)],
                            columns=["timestamp", "service_call", "succeeded", "count", "request_ids"])
        anomalies = model.transform(data, self._time_window)
        self.assertEqual(0, len(anomalies))
        
    def test_duplicate_message_id_model_empty_dataframe(self):
        model = DuplicateMessageIdModel(self._config)
        data = pd.DataFrame()
        anomalies = model.transform(data, self._time_window)
        self.assertEqual(0, len(anomalies))
     
    def test_duplicate_message_id_model_anomaly_not_found(self):
        model = DuplicateMessageIdModel(self._config)
        ts = datetime.now()
        service_call = "sc1"
        request_ids = ["id"]
        message_id1 = "messageID1"
        message_id2 = "messageID2"
        data = pd.DataFrame()
        anomalies = model.transform(data, self._time_window)
        self.assertEqual(0, len(anomalies))
    
    def test_duplicate_message_id_model_anomaly_found(self):
        model = DuplicateMessageIdModel(self._config)
        ts = datetime.now()
        service_call = "sc1"
        request_ids = ["id"]
        message_id1 = "messageID1"
        message_id2 = "messageID2"
        data = pd.DataFrame([(ts, service_call, message_id1, 2, request_ids)],
                            columns=["timestamp", "service_call", "messageId", "message_id_count", "request_ids"])
        anomalies = model.transform(data, self._time_window)
        self.assertEqual(1, len(anomalies))
        
    def test_time_sync_model_empty_dataframe(self):
        model = TimeSyncModel(self._config)
        data = pd.DataFrame()
        metric = "responseTime"
        threshold = 0
        anomalies = model.transform(data, metric, threshold, self._time_window)
        self.assertEqual(0, len(anomalies))

    def test_time_sync_model_anomaly_not_found(self):
        model = TimeSyncModel(self._config)
        metric = "responseTime"
        threshold = 0
        ts = datetime.now()
        service_call = "sc1"
        request_ids = ["id"]
        data = pd.DataFrame()
        anomalies = model.transform(data, metric, threshold, self._time_window)
        self.assertEqual(0, len(anomalies))
        
    def test_time_sync_model_anomaly_found(self):
        model = TimeSyncModel(self._config)
        metric = "responseTime"
        threshold = 0
        ts = datetime.now()
        service_call = "sc1"
        request_ids = ["id"]
        data = pd.DataFrame([(ts, service_call, 1, 2, 0.5, request_ids)],
                            columns=["timestamp", "service_call", "erroneous_count", "request_count", "avg_erroneous_diff", "request_ids"])
        anomalies = model.transform(data, metric, threshold, self._time_window)
        self.assertEqual(1, len(anomalies))
    
    def test_averages_by_timeperiod_model_fit_empty_dataframe(self):
        model = AveragesByTimeperiodModel(self._similarity_time_window, self._config)
        data = pd.DataFrame()
        model.fit(data)
        self.assertEqual(None, model.dt_avgs)
        
    def test_averages_by_timeperiod_model_fit_single_query(self):
        service_call = "sc1"
        similar_periods = "10_3"  # 10 o'clock on a Wednesday
        ts = datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        request_ids = ["id"]
        request_count = 2
        data = pd.DataFrame([(ts, service_call, request_count, request_ids)],
                            columns=["timestamp", "service_call", "request_count", "request_ids"])
                
        model = AveragesByTimeperiodModel(self._similarity_time_window, self._config)
        model.fit(data)
        model_row = model.dt_avgs.loc[(model.dt_avgs.index.get_level_values("service_call") == service_call) &
                                      (model.dt_avgs.index.get_level_values("similar_periods") == similar_periods)]
        self.assertEqual(request_count, model_row.ix[0, "request_count_mean"])
        self.assertEqual(0, model_row.ix[0, "request_count_std"])
        
    def test_averages_by_timeperiod_model_fit_two_queries(self):
        service_call = "sc1"
        similar_periods = "10_3"  # 10 o'clock on a Wednesday
        ts = datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        request_ids = ["id"]
        data = pd.DataFrame([(ts, service_call, 2, request_ids),
                             (ts, service_call, 3, request_ids)],
                            columns=["timestamp", "service_call", "request_count", "request_ids"])
                
        model = AveragesByTimeperiodModel(self._similarity_time_window, self._config)
        model.fit(data)
        model_row = model.dt_avgs.loc[(model.dt_avgs.index.get_level_values("service_call") == service_call) &
                                      (model.dt_avgs.index.get_level_values("similar_periods") == similar_periods)]
        self.assertEqual(np.mean([2, 3]), model_row.ix[0, "request_count_mean"])
        self.assertEqual(np.std([2, 3], ddof=0), model_row.ix[0, "request_count_std"])
        
    def test_averages_by_timeperiod_model_transform_empty_dataframe(self):
        service_call = "sc1"
        similar_periods = "10_3"
        dt_avgs = pd.DataFrame([(service_call, similar_periods, 2.5, 0.5)],
                               columns=["service_call", "similar_periods", "request_count_mean", "request_count_std"])
        model = AveragesByTimeperiodModel(self._similarity_time_window, self._config, dt_avgs=dt_avgs)
        data = pd.DataFrame()
        anomalies = model.transform(data)
        self.assertEqual(0, len(anomalies))
        
    def test_averages_by_timeperiod_model_transform_anomaly_found(self):
        service_call = "sc1"
        similar_periods = "10_3"
        request_ids = ["id"]
        
        ts = datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        dt_avgs = pd.DataFrame([(service_call, similar_periods, 2.5, 0.5, 1)],
                               columns=["service_call", "similar_periods", "request_count_mean", "request_count_std",
                                        "model_version"])
        model = AveragesByTimeperiodModel(self._similarity_time_window, self._config, dt_avgs=dt_avgs)
        
        data = pd.DataFrame([(ts, service_call, 10, request_ids)],
                            columns=["timestamp", "service_call", "request_count", "request_ids"])
        anomalies = model.transform(data)
        self.assertEqual(1, len(anomalies))
        
    def test_averages_by_timeperiod_model_transform_anomaly_not_found(self):
        service_call = "sc1"
        similar_periods = "10_3"
        request_ids = ["id"]
        
        ts = datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        dt_avgs = pd.DataFrame([(service_call, similar_periods, 2.5, 0.5, 1)],
                               columns=["service_call", "similar_periods", "request_count_mean", "request_count_std",
                                        "model_version"])
        model = AveragesByTimeperiodModel(self._similarity_time_window, self._config, dt_avgs=dt_avgs)
        
        data = pd.DataFrame([(ts, service_call, 2.5, request_ids)],
                            columns=["timestamp", "service_call", "request_count", "request_ids"])
        anomalies = model.transform(data)
        self.assertEqual(0, len(anomalies))
        
    def test_averages_by_timeperiod_model_transform_period_not_in_model(self):
        service_call = "sc1"
        similar_periods = "11_3"
        request_ids = ["id"]
        
        ts = datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        dt_avgs = pd.DataFrame([(service_call, similar_periods, 2.5, 0.5, 1)],
                               columns=["service_call", "similar_periods", "request_count_mean", "request_count_std",
                                        "model_version"])
        model = AveragesByTimeperiodModel(self._similarity_time_window, self._config, dt_avgs=dt_avgs)
        
        data = pd.DataFrame([(ts, service_call, 2.5, request_ids)],
                            columns=["timestamp", "service_call", "request_count", "request_ids"])
        anomalies = model.transform(data)
        self.assertEqual(1, len(anomalies))
    
    def test_averages_by_timeperiod_model_update_empty_dataframe(self):
        service_call = "sc1"
        similar_periods = "10_3"
        mean_val = 2.5
        std_val = 0.5
        dt_avgs = pd.DataFrame([(service_call, similar_periods, mean_val, std_val, 1)],
                               columns=["service_call", "similar_periods", "request_count_mean", "request_count_std", "model_version"])
        model = AveragesByTimeperiodModel(self._similarity_time_window, self._config, dt_avgs=dt_avgs)
        data = pd.DataFrame()
        model.update_model(data)
        self.assertEqual(dt_avgs.shape, model.dt_avgs.shape)
        model_row = model.dt_avgs.loc[(model.dt_avgs.service_call == service_call) & (model.dt_avgs.similar_periods == similar_periods)]
        self.assertEqual(mean_val, model_row.ix[0, "request_count_mean"])
        self.assertEqual(std_val, model_row.ix[0, "request_count_std"])
        
    def test_averages_by_timeperiod_model_update_existing_period(self):
        service_call = "sc1"
        similar_periods = "10_3"
        request_ids = ["id"]
        ts = datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
        dt_avgs = pd.DataFrame([(service_call, similar_periods, 2., 0., 1, 2., 4., 1., datetime.now())],
                               columns=["service_call", "similar_periods", "request_count_mean", "request_count_std",
                                        "version", "request_count_sum", "request_count_ssq", "request_count_count",
                                        "model_creation_timestamp"])
        dt_avgs = dt_avgs.set_index(["service_call", "similar_periods"])
        model = AveragesByTimeperiodModel(self._similarity_time_window, self._config, dt_avgs=dt_avgs)
        
        data = pd.DataFrame([(ts, service_call, 3, request_ids)],
                            columns=["timestamp", "service_call", "request_count", "request_ids"])
        model.update_model(data)
        
        self.assertEqual(dt_avgs.shape[0], model.dt_avgs.shape[0])
        model_row = model.dt_avgs.loc[(model.dt_avgs.index.get_level_values("service_call") == service_call) &
                                      (model.dt_avgs.index.get_level_values("similar_periods") == similar_periods)]
        self.assertEqual(np.mean([2, 3]), model_row.ix[0, "request_count_mean"])
        self.assertEqual(np.std([2, 3], ddof=0), model_row.ix[0, "request_count_std"])
        self.assertEqual(2 + 3, model_row.ix[0, "request_count_sum"])
        self.assertEqual(4 + 9, model_row.ix[0, "request_count_ssq"])
        self.assertEqual(2, model_row.ix[0, "request_count_count"])
        
    def test_averages_by_timeperiod_model_add_new_period(self):
        service_call = "sc1"
        similar_periods = "10_3"
        request_ids = ["id"]
        ts = datetime.strptime("5/10/2017 11:00:00", "%d/%m/%Y %H:%M:%S")
        dt_avgs = pd.DataFrame([(service_call, similar_periods, 2., 0., 1, 2., 4., 1., datetime.now())],
                               columns=["service_call", "similar_periods", "request_count_mean", "request_count_std",
                                        "version", "request_count_sum", "request_count_ssq", "request_count_count",
                                        "model_creation_timestamp"])
        dt_avgs = dt_avgs.set_index(["service_call", "similar_periods"])
        model = AveragesByTimeperiodModel(self._similarity_time_window, self._config, dt_avgs=dt_avgs)
        
        data = pd.DataFrame([(ts, service_call, 3, request_ids)],
                            columns=["timestamp", "service_call", "request_count", "request_ids"])
        model.update_model(data)
        
        self.assertEqual(dt_avgs.shape[0] + 1, model.dt_avgs.shape[0])
        model_row = model.dt_avgs.loc[(model.dt_avgs.index.get_level_values("service_call") == service_call) &
                                      (model.dt_avgs.index.get_level_values("similar_periods") == "11_3")]
        self.assertEqual(3, model_row.ix[0, "request_count_mean"])
        self.assertEqual(0, model_row.ix[0, "request_count_std"])
        self.assertEqual(3, model_row.ix[0, "request_count_sum"])
        self.assertEqual(9, model_row.ix[0, "request_count_ssq"])
        self.assertEqual(1, model_row.ix[0, "request_count_count"])
