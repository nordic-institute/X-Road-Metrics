#
# The MIT License 
# Copyright (c) 2021- Nordic Institute for Interoperability Solutions (NIIS)
# Copyright (c) 2017-2020 Estonian Information System Authority (RIA)
#  
# Permission is hereby granted, free of charge, to any person obtaining a copy 
# of this software and associated documentation files (the "Software"), to deal 
# in the Software without restriction, including without limitation the rights 
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions: 
#  
# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software. 
#  
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN 
# THE SOFTWARE.
#

import pandas as pd
import numpy as np
from datetime import datetime

from opmon_analyzer import constants


class TimeSyncModel(object):

    def __init__(self):
        pass

    def fit(self, data):
        return self

    def transform(self, anomalies, metric, threshold, time_window):
        if len(anomalies) > 0:
            # select relevant columns
            current_time = datetime.now()
            timedelta = pd.to_timedelta(1, unit=time_window['pd_timeunit'])
            period_end_time = anomalies[constants.timestamp_field] + timedelta

            anomalies = anomalies.assign(incident_creation_timestamp=current_time)
            anomalies = anomalies.assign(incident_update_timestamp=current_time)
            anomalies = anomalies.assign(model_version=1)
            anomalies = anomalies.assign(aggregation_timeunit=time_window['agg_window_name'])
            anomalies = anomalies.assign(model_timeunit=time_window['agg_window_name'])
            anomalies = anomalies.assign(incident_status='new')
            anomalies = anomalies.assign(period_end_time=period_end_time)

            anomalies = anomalies.assign(anomalous_metric=metric)
            anomalies = anomalies.assign(comments="")
            anomalies = anomalies.assign(difference_from_normal=-anomalies["avg_erroneous_diff"])
            anomalies = anomalies.assign(anomaly_confidence=1.0)
            anomalies = anomalies.assign(monitored_metric_value=anomalies["erroneous_count"])
            anomalies = anomalies.assign(model_params=[{'min_threshold': float(threshold)}] * len(anomalies))

            anomalies = anomalies.assign(
                description=anomalies.apply(self._generate_description, axis=1, metric=metric, threshold=threshold))

            anomaly_fields = [
                "anomaly_confidence", constants.timestamp_field, 'incident_creation_timestamp',
                'incident_update_timestamp', "request_count", "difference_from_normal",
                'model_version', 'anomalous_metric', 'aggregation_timeunit', 'period_end_time',
                'monitored_metric_value', 'model_params', 'description', 'incident_status', "request_ids",
                "comments"
            ]

            anomalies = anomalies[constants.service_identifier_column_names + anomaly_fields]
            anomalies = anomalies.rename(columns={constants.timestamp_field: 'period_start_time'})

        return anomalies

    @staticmethod
    def _generate_description(row, metric, threshold):
        desc = "%s must be greater than %s, but %s requests out of %s were smaller (by %s on average)" % (
            metric, threshold, int(row['erroneous_count']), int(row['request_count']),
            np.round(row['difference_from_normal'], 2))
        return desc
