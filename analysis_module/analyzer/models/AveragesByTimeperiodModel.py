import pandas as pd
import numpy as np
import scipy
import scipy.stats
import time
from datetime import datetime
import calendar
import sys
sys.path.append("..")
from AnalyzerDatabaseManager import AnalyzerDatabaseManager
import settings as db_conf


class AveragesByTimeperiodModel(object):
    
    def __init__(self, time_window, config, dt_avgs=None, version=0, model_creation_timestamp=0):
        
        self.time_window = time_window
        self._config = config
        self.dataset_manager = AnalyzerDatabaseManager(db_conf, config)
        
        self.dt_avgs = dt_avgs
        self.version = version
        self.model_creation_timestamp = model_creation_timestamp

    def fit(self, dt_agg):
        
        if len(dt_agg) <= 0:
            return
        
        dt_agg = self._add_similar_periods_string(dt_agg)

        self.dt_avgs = dt_agg.drop([self._config.timestamp_field, "request_ids"],
                                   axis=1).groupby(self._config.service_call_fields +
                                                   ["similar_periods"]).agg([np.mean,
                                                                             self.std,
                                                                             'count',
                                                                             np.sum,
                                                                             self.ssq])
        self.dt_avgs.columns = ['_'.join(col) for col in self.dt_avgs.columns.values]
        
        for metric in self._config.historic_averages_thresholds.keys():
            self.dt_avgs["%s_std" % metric] = self.dt_avgs["%s_std" % metric].fillna(0)
            
            self.dt_avgs["%s_mean" % metric] = self.dt_avgs["%s_mean" % metric].astype(float)
            self.dt_avgs["%s_std" % metric] = self.dt_avgs["%s_std" % metric].astype(float)
            self.dt_avgs["%s_count" % metric] = self.dt_avgs["%s_count" % metric].astype(float)
            self.dt_avgs["%s_sum" % metric] = self.dt_avgs["%s_sum" % metric].astype(float)
            self.dt_avgs["%s_ssq" % metric] = self.dt_avgs["%s_ssq" % metric].astype(float)
        
        current_time = datetime.now()
        
        self.dt_avgs = self.dt_avgs.assign(version=1)
        self.dt_avgs = self.dt_avgs.assign(model_creation_timestamp=current_time)
        self.dt_avgs = self.dt_avgs.assign(model_update_timestamp=current_time)
        self.dt_avgs = self.dt_avgs.assign(model_name=self.time_window['timeunit_name'])
        
    def transform(self, dt_agg):
        
        all_anomalies = pd.DataFrame()
        
        if self.dt_avgs is None or len(dt_agg) <= 0:
            return all_anomalies
        
        dt_agg = self._add_similar_periods_string(dt_agg)
            
        dt_merged = dt_agg.reset_index().merge(self.dt_avgs.reset_index(),
                                               on=self._config.service_call_fields + ['similar_periods'], how="left")
            
        for metric, threshold in self._config.historic_averages_thresholds.items():
            tmp = dt_merged.dropna(subset=[metric])
            if metric != "request_count":
                tmp = tmp.dropna(subset=["%s_mean" % metric])
            tmp = tmp.fillna(0)
            tmp = tmp.assign(z_score=(tmp[metric] - tmp["%s_mean" % metric]) / tmp["%s_std" % metric].replace(0, 0.001))
            tmp = tmp.assign(p_value=scipy.stats.norm.sf(abs(tmp['z_score'])) * 2)
            alpha = 1 - threshold
            anomalies = tmp[tmp['p_value'] < alpha]

            if len(anomalies) == 0:
                continue

            current_time = datetime.now()
            anomalies = anomalies.reset_index()

            anomalies = anomalies.assign(incident_creation_timestamp=current_time)
            anomalies = anomalies.assign(incident_update_timestamp=current_time)
            anomalies = anomalies.assign(aggregation_timeunit=self.time_window['agg_window']['agg_window_name'])
            anomalies = anomalies.assign(model_timeunit=self.time_window['timeunit_name'])
            anomalies = anomalies.assign(incident_status='new')
            anomalies = anomalies.assign(period_end_time=(anomalies[self._config.timestamp_field] +
                                                          pd.to_timedelta(1, unit=self.time_window['agg_window']['pd_timeunit'])))
                
            anomalies = anomalies.assign(anomalous_metric=metric)
            anomalies = anomalies.assign(comments="")
            anomalies = anomalies.assign(monitored_metric_value=anomalies[metric])
            anomalies = anomalies.assign(anomaly_confidence=1 - anomalies['p_value'])
            anomalies = anomalies.rename(columns={"%s_mean" % metric: "metric_mean",
                                                  "%s_std" % metric: "metric_std",
                                                  "version": "model_version"})
            anomalies = anomalies.assign(difference_from_normal=abs(anomalies["monitored_metric_value"] - anomalies["metric_mean"]))
            model_param_cols = ["metric_mean", "metric_std", 'model_timeunit', 'similar_periods']
            model_params = anomalies[model_param_cols].to_dict('records')
            anomalies = anomalies.assign(model_params=model_params)

            anomalies = anomalies.assign(description=anomalies.apply(self._generate_description, axis=1))

            anomalies = anomalies[self._config.service_call_fields +
                                  ["anomaly_confidence", self._config.timestamp_field, 'incident_creation_timestamp',
                                   'incident_update_timestamp', "request_count", "difference_from_normal",
                                   'model_version', 'anomalous_metric', 'aggregation_timeunit', 'period_end_time',
                                   'monitored_metric_value', 'model_params', 'description', 'incident_status',
                                   "request_ids", "comments"]]
            anomalies = anomalies.rename(columns={self._config.timestamp_field: 'period_start_time'})

            all_anomalies = pd.concat([all_anomalies, anomalies], axis=0)
        
        return all_anomalies
    
    def update_model(self, data_new_agg):
        print("Model will be updated based on %s new requests" % data_new_agg.shape[0])
        
        if len(data_new_agg) <= 0:
            return
        
        data_new_agg = self._add_similar_periods_string(data_new_agg)
            
        # separate time periods that already exist in the model from those that don't
        data_new_agg = data_new_agg.set_index(self._config.service_call_fields + ['similar_periods'])
            
        new_periods = data_new_agg.index.difference(self.dt_avgs.index)
        existing_periods = data_new_agg.index.intersection(self.dt_avgs.index)
            
        data_new_agg_new_periods = data_new_agg.loc[new_periods]
        data_new_agg_existing_periods = data_new_agg.loc[existing_periods]
        
        print("There are %s completely new periods and %s new entries to existing periods" % (len(new_periods), len(data_new_agg_existing_periods)))
        print("Updating existing periods...")
        
        # update existing periods in the model
        start = time.time()
        counter = 0
        for name, row in data_new_agg_existing_periods.iterrows():

            model_vals = self.dt_avgs.loc[name].fillna(0)

            for metric in self._config.historic_averages_thresholds.keys():

                mean, std, n, summ, ssq = self._update_mean_std_n(model_vals["%s_sum" % metric],
                                                                  model_vals["%s_ssq" % metric],
                                                                  model_vals["%s_count" % metric],
                                                                  row[metric])
                self.dt_avgs.set_value(name, "%s_mean" % metric, mean)
                self.dt_avgs.set_value(name, "%s_std" % metric, std)
                self.dt_avgs.set_value(name, "%s_count" % metric, n)
                self.dt_avgs.set_value(name, "%s_sum" % metric, summ)
                self.dt_avgs.set_value(name, "%s_ssq" % metric, ssq)
            counter += 1
            if counter % 1000 == 0:
                print("%s/%s done, time: %s" % (counter, len(data_new_agg_existing_periods), time.time() - start))
        print("%s/%s done, time: %s" % (counter, len(data_new_agg_existing_periods), time.time() - start))

        # add completely new periods to the model as additional rows
        print("Adding new periods...")
        start = time.time()
        data_new_agg_new_periods_grouped = data_new_agg_new_periods.reset_index().groupby(self._config.service_call_fields +
                                                                                          ['similar_periods'])
        relevant_metrics = list(self._config.historic_averages_thresholds.keys())
        tmp = data_new_agg_new_periods_grouped[relevant_metrics].agg([np.mean, self.std, 'count', np.sum, self.ssq])

        tmp.columns = ['_'.join(col) for col in tmp.columns.values]
        for metric in self._config.historic_averages_thresholds.keys():
            tmp["%s_std" % metric] = tmp["%s_std" % metric].fillna(0)
        
        current_time = datetime.now()
        tmp = tmp.assign(version=self.version)
        tmp = tmp.assign(model_creation_timestamp=self.model_creation_timestamp) #self.dt_avgs.model_creation_timestamp.iloc[0])
        tmp = tmp.assign(model_update_timestamp=current_time)
        tmp = tmp.assign(model_name=self.time_window['timeunit_name'])
        
        self.dt_avgs = self.dt_avgs.append(tmp)
        print("Done, time: %s" % (time.time() - start))
          
        self.dt_avgs = self.dt_avgs.assign(version=self.version + 1)
        self.dt_avgs = self.dt_avgs.assign(model_update_timestamp=current_time)
    
    def std(self, x):
        return np.std(x, ddof=0)
    
    def ssq(self, x):
        return np.sum(x * x)
    
    def _generate_description(self, row):
        desc = "Average %s per %s %s is %s, but observed %s was %s." % (
            row['anomalous_metric'],
            row['aggregation_timeunit'],
            " ".join([self._get_timeunit_name(unit, int(val)) for unit, val in zip(self.time_window['similar_periods'],
                                                                                   row['similar_periods'].split("_"))]),
            np.round(row['metric_mean'], 2),
            row['anomalous_metric'],
            np.round(row['monitored_metric_value'], 2))
        return desc
    
    def _get_timeunit_name(self, timeunit, value):
        if timeunit == "weekday":
            return("on %ss" % (list(calendar.day_name)[value]))
        elif timeunit == "hour":
            return("between %02d:00 and %02d:00" % (value, value + 1))
        if timeunit == "month":
            return("in %s" % (list(calendar.month_name)[value]))
        else:
            return(value)
    
    def _update_mean_std_n(self, summ, sumsq, n, x):
        n += 1
        summ += x
        sumsq += x * x
        if n < 2:
            var = 0
        else:
            var = (sumsq - (summ * summ) / n) / (n)
        mean = float(summ) / n
        return (mean, np.sqrt(var), n, summ, sumsq)

    def _get_timestamp(self, date):
        return int((pd.Series(date).astype(np.int64) / 1e6).astype(np.int64)[0])
    
    def _add_similar_periods_string(self, dt_agg):
        if len(dt_agg) > 0:
            dt_agg["similar_periods"] = getattr(dt_agg[self._config.timestamp_field].dt, self.time_window['similar_periods'][0]).apply(str)
            for i in range(1, len(self.time_window['similar_periods'])):
                dt_agg["similar_periods"] += "_"
                dt_agg["similar_periods"] += getattr(dt_agg[self._config.timestamp_field].dt,
                                                     self.time_window['similar_periods'][i]).apply(str)
        return dt_agg
