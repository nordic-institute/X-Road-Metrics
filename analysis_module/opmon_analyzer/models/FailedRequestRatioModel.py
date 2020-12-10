import pandas as pd
import numpy as np
import time
from datetime import datetime


class FailedRequestRatioModel(object):
    
    def __init__(self, config):
        self.anomaly_type = 'failed_request_ratio'
        self._config = config
        
    def fit(self, data):
        return self
    
    def transform(self, data, time_window):
        if len(data) > 0:
            
            tmp_succeeded = data[data.succeeded]
            tmp_failed = data[~data.succeeded]
            tmp_succeeded = tmp_succeeded.drop(["request_ids", "succeeded"], axis=1)
            tmp_failed = tmp_failed.drop(["succeeded"], axis=1)
            tmp = tmp_succeeded.merge(tmp_failed,
                                      on=self._config.service_call_fields + [self._config.timestamp_field],
                                      how="outer",
                                      suffixes=["_successful", "_failed"])
            tmp = tmp.fillna(0)
            tmp = tmp.assign(request_count=tmp["count_successful"] + tmp["count_failed"])
            tmp = tmp.assign(failed_request_ratio=tmp["count_failed"] / tmp["request_count"])

            tmp = tmp.assign(diff=tmp.failed_request_ratio - self._config.failed_request_ratio_threshold)
            anomalies = tmp[tmp.failed_request_ratio > self._config.failed_request_ratio_threshold]
        
            if len(anomalies) <= 0:
                return pd.DataFrame()
        
            # select relevant columns
            current_time = datetime.now()
            anomalies = anomalies.reset_index()

            anomalies = anomalies.assign(incident_creation_timestamp=current_time)
            anomalies = anomalies.assign(incident_update_timestamp=current_time)
            anomalies = anomalies.assign(model_version=1)
            anomalies = anomalies.assign(aggregation_timeunit=time_window['agg_window_name'])
            anomalies = anomalies.assign(model_timeunit=time_window['agg_window_name'])
            anomalies = anomalies.assign(incident_status='new')
            anomalies = anomalies.assign(period_end_time=anomalies[self._config.timestamp_field] + pd.to_timedelta(1, unit=time_window['pd_timeunit']))

            anomalies = anomalies.assign(anomalous_metric=self.anomaly_type)
            anomalies = anomalies.assign(comments="")
            anomalies = anomalies.assign(monitored_metric_value=anomalies.failed_request_ratio)
            anomalies = anomalies.assign(difference_from_normal=anomalies['diff'])
            anomalies = anomalies.assign(anomaly_confidence=1.0)
            anomalies = anomalies.assign(model_params=[{"failed_request_ratio_threshold": self._config.failed_request_ratio_threshold}] * len(anomalies))

            anomalies = anomalies.assign(description=anomalies.apply(self._generate_description, axis=1))

            anomalies = anomalies[self._config.service_call_fields +
                                  ["anomaly_confidence", self._config.timestamp_field, 'incident_creation_timestamp',
                                   'incident_update_timestamp', "request_count", "difference_from_normal",
                                   'model_version', 'anomalous_metric', 'aggregation_timeunit', 'period_end_time',
                                   'monitored_metric_value', 'model_params', 'description', 'incident_status', "request_ids",
                                   "comments"]]
            anomalies = anomalies.rename(columns={self._config.timestamp_field: 'period_start_time'})
        
            return anomalies
        else:
            return pd.DataFrame()
    
    def _generate_description(self, row):
        desc = "Allowed failed_request_ratio is %s, but observed was %s (%s requests out of %s failed)." % (
            self._config.failed_request_ratio_threshold,
            round(row.failed_request_ratio, 2),
            int(row["count_failed"]),
            int(row["request_count"]))
        return desc
