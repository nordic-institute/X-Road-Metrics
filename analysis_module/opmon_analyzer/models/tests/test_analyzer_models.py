#  The MIT License
#  Copyright (c) 2021- Nordic Institute for Interoperability Solutions (NIIS)
#  Copyright (c) 2017-2020 Estonian Information System Authority (RIA)
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

import os
import pytest
import pathlib

import pandas as pd
import numpy as np
from datetime import datetime

from opmon_analyzer.models.FailedRequestRatioModel import FailedRequestRatioModel
from opmon_analyzer.models.DuplicateMessageIdModel import DuplicateMessageIdModel
from opmon_analyzer.models.TimeSyncModel import TimeSyncModel
from opmon_analyzer.models.AveragesByTimeperiodModel import AveragesByTimeperiodModel

from opmon_analyzer.analyzer_conf import DataModelConfiguration
from opmon_analyzer.settings_parser import OpmonSettingsManager

time_window = {'agg_window_name': 'hour_monthday', 'agg_minutes': 60, 'pd_timeunit': 'h'}

similarity_time_window = {
    'timeunit_name': 'hour_weekday',
    'agg_window': time_window,
    'similar_periods': ['hour', 'weekday']
}


@pytest.fixture
def unittest_settings():
    os.chdir(pathlib.Path(__file__).parent.absolute())
    return OpmonSettingsManager().settings


@pytest.fixture
def unittest_config(unittest_settings):
    return DataModelConfiguration(unittest_settings)


def test_failed_request_ratio_model_empty_dataframe(unittest_config, unittest_settings):
    model = FailedRequestRatioModel(unittest_settings)
    data = pd.DataFrame()
    anomalies = model.transform(data, time_window)
    assert (len(anomalies) == 0)


def test_failed_request_ratio_model_anomaly_found(mocker, unittest_config, unittest_settings):
    patch_constants(mocker, 'FailedRequestRatioModel')

    model = FailedRequestRatioModel(unittest_settings)
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


def test_failed_request_ratio_model_anomaly_not_found(mocker, unittest_config, unittest_settings):
    patch_constants(mocker, 'FailedRequestRatioModel')

    model = FailedRequestRatioModel(unittest_settings)
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


def test_duplicate_message_id_model_empty_dataframe():
    model = DuplicateMessageIdModel()
    data = pd.DataFrame()
    anomalies = model.transform(data, time_window)
    assert (len(anomalies) == 0)


def test_duplicate_message_id_model_anomaly_not_found():
    model = DuplicateMessageIdModel()
    data = pd.DataFrame()
    anomalies = model.transform(data, time_window)
    assert (0 == len(anomalies))


def test_duplicate_message_id_model_anomaly_found(mocker):
    patch_constants(mocker, 'DuplicateMessageIdModel')
    model = DuplicateMessageIdModel()
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


def test_time_sync_model_empty_dataframe():
    model = TimeSyncModel()
    data = pd.DataFrame()
    metric = "responseTime"
    threshold = 0
    anomalies = model.transform(data, metric, threshold, time_window)
    assert (0 == len(anomalies))


def test_time_sync_model_anomaly_not_found():
    model = TimeSyncModel()
    metric = "responseTime"
    threshold = 0
    data = pd.DataFrame()
    anomalies = model.transform(data, metric, threshold, time_window)
    assert (0 == len(anomalies))


def test_time_sync_model_anomaly_found(mocker):
    patch_constants(mocker, 'TimeSyncModel')
    model = TimeSyncModel()
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


def test_averages_by_timeperiod_model_fit_empty_dataframe(unittest_config, mocker):
    patch_constants(mocker, 'AveragesByTimeperiodModel')
    model = AveragesByTimeperiodModel(similarity_time_window, unittest_config)
    data = pd.DataFrame()
    model.fit(data)
    assert (None is model.dt_avgs)


def test_averages_by_timeperiod_model_fit_single_query(unittest_config, mocker):
    patch_constants(mocker, 'AveragesByTimeperiodModel')
    service_call = "sc1"
    similar_periods = "10_3"  # 10 o'clock on a Wednesday
    ts = datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
    request_ids = ["id"]
    request_count = 2
    data = pd.DataFrame(
        [(ts, service_call, request_count, request_ids)],
        columns=["timestamp", "service_call", "request_count", "request_ids"])

    model = AveragesByTimeperiodModel(similarity_time_window, unittest_config)
    model.fit(data)

    assert (len(model.dt_avgs.index) == 1)

    row_label = model.dt_avgs.index.to_numpy()[0]

    assert (row_label == (service_call, similar_periods))
    assert (request_count == model.dt_avgs.at[row_label, "request_count_mean"])
    assert (0 == model.dt_avgs.at[row_label, "request_count_std"])


def test_averages_by_timeperiod_model_fit_two_queries(unittest_config, mocker):
    patch_constants(mocker, 'AveragesByTimeperiodModel')
    service_call = "sc1"
    similar_periods = "10_3"  # 10 o'clock on a Wednesday
    ts = datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
    request_ids = ["id"]

    data = pd.DataFrame(
        [(ts, service_call, 2, request_ids),
         (ts, service_call, 3, request_ids)
         ],
        columns=["timestamp", "service_call", "request_count", "request_ids"])

    model = AveragesByTimeperiodModel(similarity_time_window, unittest_config)
    model.fit(data)

    assert (len(model.dt_avgs.index) == 1)

    row_label = model.dt_avgs.index.to_numpy()[0]

    assert (row_label == (service_call, similar_periods))
    assert (np.mean([2, 3]) == model.dt_avgs.at[row_label, "request_count_mean"])
    assert (np.std([2, 3], ddof=0) == model.dt_avgs.at[row_label, "request_count_std"])


def test_averages_by_timeperiod_model_transform_empty_dataframe(unittest_config):
    service_call = "sc1"
    similar_periods = "10_3"
    dt_avgs = pd.DataFrame(
        [(service_call, similar_periods, 2.5, 0.5)],
        columns=["service_call", "similar_periods", "request_count_mean", "request_count_std"]
    )
    model = AveragesByTimeperiodModel(similarity_time_window, unittest_config, dt_avgs=dt_avgs)
    data = pd.DataFrame()
    anomalies = model.transform(data)
    assert (0 == len(anomalies))


def test_averages_by_timeperiod_model_transform_anomaly_found(unittest_config, mocker):
    patch_constants(mocker, 'AveragesByTimeperiodModel')

    service_call = "sc1"
    similar_periods = "10_3"
    request_ids = ["id"]

    ts = datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
    dt_avgs = pd.DataFrame(
        [(service_call, similar_periods, 2.5, 0.5, 1)],
        columns=["service_call", "similar_periods", "request_count_mean", "request_count_std", "model_version"]
    )
    model = AveragesByTimeperiodModel(similarity_time_window, unittest_config, dt_avgs=dt_avgs)

    data = pd.DataFrame(
        [(ts, service_call, 10, request_ids)],
        columns=["timestamp", "service_call", "request_count", "request_ids"]
    )
    anomalies = model.transform(data)
    assert (1 == len(anomalies))


def test_averages_by_timeperiod_model_transform_anomaly_not_found(unittest_config, mocker):
    patch_constants(mocker, 'AveragesByTimeperiodModel')

    service_call = "sc1"
    similar_periods = "10_3"
    request_ids = ["id"]

    ts = datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
    dt_avgs = pd.DataFrame(
        [(service_call, similar_periods, 2.5, 0.5, 1)],
        columns=["service_call", "similar_periods", "request_count_mean", "request_count_std", "model_version"]
    )
    model = AveragesByTimeperiodModel(similarity_time_window, unittest_config, dt_avgs=dt_avgs)

    data = pd.DataFrame(
        [(ts, service_call, 2.5, request_ids)],
        columns=["timestamp", "service_call", "request_count", "request_ids"]
    )
    anomalies = model.transform(data)
    assert (0 == len(anomalies))


def test_averages_by_timeperiod_model_transform_period_not_in_model(unittest_config, mocker):
    patch_constants(mocker, 'AveragesByTimeperiodModel')

    service_call = "sc1"
    similar_periods = "11_3"
    request_ids = ["id"]

    ts = datetime.strptime("5/10/2017 10:00:00", "%d/%m/%Y %H:%M:%S")
    dt_avgs = pd.DataFrame(
        [(service_call, similar_periods, 2.5, 0.5, 1)],
        columns=["service_call", "similar_periods", "request_count_mean", "request_count_std", "model_version"]
    )
    model = AveragesByTimeperiodModel(similarity_time_window, unittest_config, dt_avgs=dt_avgs)

    data = pd.DataFrame(
        [(ts, service_call, 2.5, request_ids)],
        columns=["timestamp", "service_call", "request_count", "request_ids"]
    )
    anomalies = model.transform(data)
    assert (1 == len(anomalies))


def test_averages_by_timeperiod_model_update_empty_dataframe(unittest_config):
    service_call = "sc1"
    similar_periods = "10_3"
    mean_val = 2.5
    std_val = 0.5
    dt_avgs = pd.DataFrame(
        [(service_call, similar_periods, mean_val, std_val, 1)],
        columns=["service_call", "similar_periods", "request_count_mean", "request_count_std", "model_version"]
    )
    model = AveragesByTimeperiodModel(similarity_time_window, unittest_config, dt_avgs=dt_avgs)
    data = pd.DataFrame()
    model.update_model(data)
    assert (dt_avgs.equals(model.dt_avgs))


def test_averages_by_timeperiod_model_update_existing_period(unittest_config, mocker):
    patch_constants(mocker, 'AveragesByTimeperiodModel')

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

    model = AveragesByTimeperiodModel(similarity_time_window, unittest_config, dt_avgs=dt_avgs)

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


def test_averages_by_timeperiod_model_add_new_period(unittest_config, mocker):
    patch_constants(mocker, 'AveragesByTimeperiodModel')
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
    model = AveragesByTimeperiodModel(similarity_time_window, unittest_config, dt_avgs=dt_avgs)

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


def patch_constants(mocker, model_name):
    constants_package = f'opmon_analyzer.models.{model_name}.constants'
    mocker.patch(f'{constants_package}.timestamp_field', 'timestamp')
    mocker.patch(f'{constants_package}.service_identifier_column_names', ["service_call"])
