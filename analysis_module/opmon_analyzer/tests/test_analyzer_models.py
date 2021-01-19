import os
import pytest
from unittest.mock import MagicMock, Mock

import pandas as pd
import numpy as np
from datetime import datetime

# import os
# ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
# os.chdir(os.path.join(ROOT_DIR, '..'))

from opmon_analyzer.models.FailedRequestRatioModel import FailedRequestRatioModel
from opmon_analyzer.models.DuplicateMessageIdModel import DuplicateMessageIdModel
from opmon_analyzer.models.TimeSyncModel import TimeSyncModel
from opmon_analyzer.models.AveragesByTimeperiodModel import AveragesByTimeperiodModel

time_window = {'agg_window_name': 'hour', 'agg_minutes': 60, 'pd_timeunit': 'h'}

similarity_time_window = {
    'timeunit_name': 'hour_weekday',
    'agg_window': time_window,
    'similar_periods': ['hour', 'weekday']
}


@pytest.fixture
def mock_config(mocker):
    config = mocker.Mock()
    config.timestamp_field = "timestamp"
    config.service_call_fields = ["service_call"]
    config.failed_request_ratio_threshold = 0.7
    config.historic_averages_thresholds = {'request_count': 0.95}
    return config


def test_failed_request_ratio_model_empty_dataframe(mock_config):
    model = FailedRequestRatioModel(mock_config)
    data = pd.DataFrame()
    anomalies = model.transform(data, time_window)
    assert (len(anomalies) == 0)


def test_failed_request_ratio_model_anomaly_found(mock_config):
    model = FailedRequestRatioModel(mock_config)
    ts = datetime.now()
    service_call = "sc1"
    request_ids = ["id"]

    data = pd.DataFrame(
        [
            (ts, service_call, True, 1, request_ids),
            (ts, service_call, False, 3, request_ids)
        ],
        columns=[
            "timestamp",
            "service_call",
            "succeeded",
            "count",
            "request_ids"
        ]
    )

    anomalies = model.transform(data, time_window)
    assert (len(anomalies) == 1)


def test_failed_request_ratio_model_anomaly_not_found(mock_config):
    model = FailedRequestRatioModel(mock_config)
    ts = datetime.now()
    service_call = "sc1"
    request_ids = ["id"]
    data = pd.DataFrame(
        [
            (ts, service_call, True, 3, request_ids),
            (ts, service_call, False, 1, request_ids)
        ],
        columns=[
            "timestamp",
            "service_call",
            "succeeded",
            "count",
            "request_ids"
        ]
    )
    anomalies = model.transform(data, time_window)
    assert (len(anomalies) == 0)


def test_duplicate_message_id_model_empty_dataframe(mock_config):
    model = DuplicateMessageIdModel(mock_config)
    data = pd.DataFrame()
    anomalies = model.transform(data, time_window)
    assert (len(anomalies) == 0)


def test_duplicate_message_id_model_anomaly_not_found(mock_config):
    model = DuplicateMessageIdModel(mock_config)
    data = pd.DataFrame()
    anomalies = model.transform(data, time_window)
    assert (0 == len(anomalies))


def test_duplicate_message_id_model_anomaly_found(mock_config):
    model = DuplicateMessageIdModel(mock_config)
    ts = datetime.now()
    service_call = "sc1"
    request_ids = ["id"]
    message_id1 = "messageID1"
    data = pd.DataFrame(
        [(ts, service_call, message_id1, 2, request_ids)],
        columns=[
            "timestamp", "service_call", "messageId", "message_id_count", "request_ids"
        ]
    )
    anomalies = model.transform(data, time_window)
    assert (1 == len(anomalies))


def test_time_sync_model_empty_dataframe(mock_config):
    model = TimeSyncModel(mock_config)
    data = pd.DataFrame()
    metric = "responseTime"
    threshold = 0
    anomalies = model.transform(data, metric, threshold, time_window)
    assert (0 == len(anomalies))


def test_time_sync_model_anomaly_not_found(mock_config):
    model = TimeSyncModel(mock_config)
    metric = "responseTime"
    threshold = 0
    data = pd.DataFrame()
    anomalies = model.transform(data, metric, threshold, time_window)
    assert (0 == len(anomalies))


def test_time_sync_model_anomaly_found(mock_config):
    model = TimeSyncModel(mock_config)
    metric = "responseTime"
    threshold = 0
    ts = datetime.now()
    service_call = "sc1"
    request_ids = ["id"]
    data = pd.DataFrame(
        [(ts, service_call, 1, 2, 0.5, request_ids)],
        columns=[
            "timestamp", "service_call", "erroneous_count", "request_count", "avg_erroneous_diff", "request_ids"
        ]
    )
    anomalies = model.transform(data, metric, threshold, time_window)
    assert (1 == len(anomalies))


def test_averages_by_timeperiod_model_fit_empty_dataframe(mock_config):
    model = AveragesByTimeperiodModel(similarity_time_window, mock_config)
    data = pd.DataFrame()
    model.fit(data)
    assert (None is model.dt_avgs)


def test_averages_by_timeperiod_model_fit_single_query(mock_config):
    service_call = "sc1"
    similar_periods = "10_3"  # 10 o'clock on a Wednesday
    ts = datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
    request_ids = ["id"]
    request_count = 2
    data = pd.DataFrame(
        [(ts, service_call, request_count, request_ids)],
        columns=["timestamp", "service_call", "request_count", "request_ids"])

    model = AveragesByTimeperiodModel(similarity_time_window, mock_config)
    model.fit(data)

    assert (len(model.dt_avgs.index) == 1)

    row_label = model.dt_avgs.index.to_numpy()[0]

    assert (row_label == (service_call, similar_periods))
    assert (request_count == model.dt_avgs.at[row_label, "request_count_mean"])
    assert (0 == model.dt_avgs.at[row_label, "request_count_std"])


def test_averages_by_timeperiod_model_fit_two_queries(mock_config):
    service_call = "sc1"
    similar_periods = "10_3"  # 10 o'clock on a Wednesday
    ts = datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
    request_ids = ["id"]

    data = pd.DataFrame(
        [(ts, service_call, 2, request_ids),
         (ts, service_call, 3, request_ids)
         ],
        columns=["timestamp", "service_call", "request_count", "request_ids"])

    model = AveragesByTimeperiodModel(similarity_time_window, mock_config)
    model.fit(data)

    assert (len(model.dt_avgs.index) == 1)

    row_label = model.dt_avgs.index.to_numpy()[0]

    assert (row_label == (service_call, similar_periods))
    assert (np.mean([2, 3]) == model.dt_avgs.at[row_label, "request_count_mean"])
    assert (np.std([2, 3], ddof=0) == model.dt_avgs.at[row_label, "request_count_std"])


def test_averages_by_timeperiod_model_transform_empty_dataframe(mock_config):
    service_call = "sc1"
    similar_periods = "10_3"
    dt_avgs = pd.DataFrame(
        [(service_call, similar_periods, 2.5, 0.5)],
        columns=["service_call", "similar_periods", "request_count_mean", "request_count_std"]
    )
    model = AveragesByTimeperiodModel(similarity_time_window, mock_config, dt_avgs=dt_avgs)
    data = pd.DataFrame()
    anomalies = model.transform(data)
    assert (0 == len(anomalies))


def test_averages_by_timeperiod_model_transform_anomaly_found(mock_config):
    service_call = "sc1"
    similar_periods = "10_3"
    request_ids = ["id"]

    ts = datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
    dt_avgs = pd.DataFrame(
        [(service_call, similar_periods, 2.5, 0.5, 1)],
        columns=["service_call", "similar_periods", "request_count_mean", "request_count_std", "model_version"]
    )
    model = AveragesByTimeperiodModel(similarity_time_window, mock_config, dt_avgs=dt_avgs)

    data = pd.DataFrame(
        [(ts, service_call, 10, request_ids)],
        columns=["timestamp", "service_call", "request_count", "request_ids"]
    )
    anomalies = model.transform(data)
    assert (1 == len(anomalies))


def test_averages_by_timeperiod_model_transform_anomaly_not_found(mock_config):
    service_call = "sc1"
    similar_periods = "10_3"
    request_ids = ["id"]

    ts = datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
    dt_avgs = pd.DataFrame(
        [(service_call, similar_periods, 2.5, 0.5, 1)],
        columns=["service_call", "similar_periods", "request_count_mean", "request_count_std", "model_version"]
    )
    model = AveragesByTimeperiodModel(similarity_time_window, mock_config, dt_avgs=dt_avgs)

    data = pd.DataFrame(
        [(ts, service_call, 2.5, request_ids)],
        columns=["timestamp", "service_call", "request_count", "request_ids"]
    )
    anomalies = model.transform(data)
    assert (0 == len(anomalies))


def test_averages_by_timeperiod_model_transform_period_not_in_model(mock_config):
    service_call = "sc1"
    similar_periods = "11_3"
    request_ids = ["id"]

    ts = datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
    dt_avgs = pd.DataFrame(
        [(service_call, similar_periods, 2.5, 0.5, 1)],
        columns=["service_call", "similar_periods", "request_count_mean", "request_count_std", "model_version"]
    )
    model = AveragesByTimeperiodModel(similarity_time_window, mock_config, dt_avgs=dt_avgs)

    data = pd.DataFrame(
        [(ts, service_call, 2.5, request_ids)],
        columns=["timestamp", "service_call", "request_count", "request_ids"]
    )
    anomalies = model.transform(data)
    assert (1 == len(anomalies))


def test_averages_by_timeperiod_model_update_empty_dataframe(mock_config):
    service_call = "sc1"
    similar_periods = "10_3"
    mean_val = 2.5
    std_val = 0.5
    dt_avgs = pd.DataFrame(
        [(service_call, similar_periods, mean_val, std_val, 1)],
        columns=["service_call", "similar_periods", "request_count_mean", "request_count_std", "model_version"]
    )
    model = AveragesByTimeperiodModel(similarity_time_window, mock_config, dt_avgs=dt_avgs)
    data = pd.DataFrame()
    model.update_model(data)
    assert (dt_avgs.equals(model.dt_avgs))


def test_averages_by_timeperiod_model_update_existing_period(mock_config):
    service_call = "sc1"
    similar_periods = "10_3"
    request_ids = ["id"]
    ts = datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")

    dt_avgs = pd.DataFrame(
        [(service_call, similar_periods, 2., 0., 1, 2., 4., 1., datetime.now())],
        columns=["service_call", "similar_periods", "request_count_mean", "request_count_std",
                 "version", "request_count_sum", "request_count_ssq", "request_count_count",
                 "model_creation_timestamp"]
    )

    dt_avgs = dt_avgs.set_index(["service_call", "similar_periods"])

    model = AveragesByTimeperiodModel(similarity_time_window, mock_config, dt_avgs=dt_avgs)

    data = pd.DataFrame(
        [(ts, service_call, 3, request_ids)],
        columns=["timestamp", "service_call", "request_count", "request_ids"]
    )

    model.update_model(data)

    assert (dt_avgs.shape[0] == model.dt_avgs.shape[0])

    assert (len(model.dt_avgs.index) == 1)

    row_label = model.dt_avgs.index.to_numpy()[0]

    assert (row_label == (service_call, similar_periods))
    assert (np.mean([2, 3]) == model.dt_avgs.at[row_label, "request_count_mean"])
    assert (np.std([2, 3], ddof=0) == model.dt_avgs.at[row_label, "request_count_std"])
    assert (2 + 3 == model.dt_avgs.at[row_label, "request_count_sum"])
    assert (4 + 9 == model.dt_avgs.at[row_label, "request_count_ssq"])
    assert (2 == model.dt_avgs.at[row_label, "request_count_count"])


def test_averages_by_timeperiod_model_add_new_period(mock_config):
    service_call = "sc1"
    similar_periods = "10_3"
    request_ids = ["id"]
    ts = datetime.strptime("5/10/2017 11:00:00", "%d/%m/%Y %H:%M:%S")
    dt_avgs = pd.DataFrame(
        [(service_call, similar_periods, 2., 0., 1, 2., 4., 1., datetime.now())],
        columns=["service_call", "similar_periods", "request_count_mean", "request_count_std",
                 "version", "request_count_sum", "request_count_ssq", "request_count_count",
                 "model_creation_timestamp"]
    )

    dt_avgs = dt_avgs.set_index(["service_call", "similar_periods"])
    model = AveragesByTimeperiodModel(similarity_time_window, mock_config, dt_avgs=dt_avgs)

    data = pd.DataFrame(
        [(ts, service_call, 3, request_ids)],
        columns=["timestamp", "service_call", "request_count", "request_ids"]
    )
    model.update_model(data)

    assert (dt_avgs.shape[0] + 1 == model.dt_avgs.shape[0])

    service_call_index = (model.dt_avgs.index.get_level_values("service_call") == service_call)
    similar_periods_index = (model.dt_avgs.index.get_level_values("similar_periods") == "11_3")

    model_row = model.dt_avgs.loc[service_call_index & similar_periods_index]

    assert (len(model_row) == 1)
    row_label = model_row.index.to_numpy()[0]

    assert (3 == model_row.at[row_label, "request_count_mean"])
    assert (0 == model_row.at[row_label, "request_count_std"])
    assert (3 == model_row.at[row_label, "request_count_sum"])
    assert (9 == model_row.at[row_label, "request_count_ssq"])
    assert (1 == model_row.at[row_label, "request_count_count"])

