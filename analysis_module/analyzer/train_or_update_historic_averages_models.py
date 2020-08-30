# TODO: add exception handling
#
from AnalyzerDatabaseManager import AnalyzerDatabaseManager
from models.AveragesByTimeperiodModel import AveragesByTimeperiodModel
import analyzer_conf
import settings

from logger_manager import LoggerManager

import os
import time
import datetime
from dateutil.relativedelta import relativedelta

import numpy as np
import pandas as pd

db_manager = AnalyzerDatabaseManager(settings, analyzer_conf)
logger_m = LoggerManager(settings.LOGGER_NAME, 'analyzer')

# add first request timestamps for service calls that have appeared
logger_m.log_heartbeat("Checking if completely new service calls have appeared", settings.HEARTBEAT_PATH,
                       settings.HEARTBEAT_FILE, 'SUCCEEDED')
db_manager.add_first_request_timestamps_from_clean_data()

metric_names = list(analyzer_conf.historic_averages_thresholds.keys())

current_time = datetime.datetime.now()
max_incident_creation_timestamp = (current_time - datetime.timedelta(minutes=analyzer_conf.incident_expiration_time))
first_model_train_timestamp = (current_time - relativedelta(months=analyzer_conf.training_period_time))
max_request_timestamp = (current_time - datetime.timedelta(minutes=analyzer_conf.corrector_buffer_time))

# retrieve service calls according to stages
logger_m.log_heartbeat("Determining service call stages", settings.HEARTBEAT_PATH, settings.HEARTBEAT_FILE)
sc_regular, sc_first_model, sc_second_model = db_manager.get_service_calls_for_train_stages(
    time_first_model=first_model_train_timestamp,
    time_second_model=max_incident_creation_timestamp)

logger_m.log_info('train_or_update_historic_averages_models',
                  "Number of service calls that have passed the training period (model will be trained for the first time): %s" % len(sc_first_model))
logger_m.log_info('train_or_update_historic_averages_models',
                  "Number of service calls that have passed the retraining period (model will be retrained for the first time): %s" % len(sc_second_model))
logger_m.log_info('train_or_update_historic_averages_models',
                  "Number of service calls that will be updated in regular mode: %s" % len(sc_regular))

# 4.3.5 - 4.3.9 Comparison with historic averages for:
# request count, response size, request size, response duration, request duration
for time_window, train_mode in analyzer_conf.historic_averages_time_windows:

    last_fit_timestamp = db_manager.get_timestamp(ts_type="last_fit_timestamp",
                                                  model_type=time_window['timeunit_name'])
    last_fit_timestamp = last_fit_timestamp if train_mode != "retrain" else None

    min_incident_creation_timestamp = last_fit_timestamp - datetime.timedelta(
        minutes=analyzer_conf.incident_expiration_time)

    start = time.time()
    logger_m.log_heartbeat(
        "Retrieving data according to service call stages (%s model)" % time_window['timeunit_name'],
        settings.HEARTBEAT_PATH, settings.HEARTBEAT_FILE)
    data_regular, data_first_train, data_first_retrain = db_manager.get_data_for_train_stages(
        sc_regular=sc_regular,
        sc_first_model=sc_first_model,
        sc_second_model=sc_second_model,
        relevant_anomalous_metrics=metric_names,
        max_incident_creation_timestamp=max_incident_creation_timestamp,
        last_fit_timestamp=last_fit_timestamp,
        agg_minutes=time_window["agg_window"]["agg_minutes"],
        max_request_timestamp=max_request_timestamp,
        min_incident_creation_timestamp=min_incident_creation_timestamp,
        aggregation_timeunits=[time_window['agg_window']['agg_window_name']])
    data = pd.concat([data_regular, data_first_train, data_first_retrain])
    
    logger_m.log_info('train_or_update_historic_averages_models', "Data (regular training) shape is: %s" % str(data_regular.shape))
    logger_m.log_info('train_or_update_historic_averages_models', "Data (first-time training) shape is: %s" % str(data_first_train.shape))
    logger_m.log_info('train_or_update_historic_averages_models', "Data (retraining) shape is: %s" % str(data_first_retrain.shape))
    logger_m.log_info('train_or_update_historic_averages_models', "Aggregating the data took: %s%s" % (str(np.round(time.time() - start, 2)), " seconds."))
    
    if train_mode == "retrain" or last_fit_timestamp is None:
        logger_m.log_heartbeat("Training the %s model" % time_window['timeunit_name'], settings.HEARTBEAT_PATH,
                               settings.HEARTBEAT_FILE, 'SUCCEEDED')
        if max_request_timestamp is not None:
            logger_m.log_info('train_or_update_historic_averages_models', "Using data until %s." % (max_request_timestamp))
        else:
            logger_m.log_info('train_or_update_historic_averages_models', "Using all data.")
        
        # Fit the model
        start = time.time()
        averages_by_time_period_model = AveragesByTimeperiodModel(time_window, analyzer_conf)
        averages_by_time_period_model.fit(data)
        logger_m.log_info('train_or_update_historic_averages_models',
                          "Averages by timeperiod model (%s) fitting time: %s%s" % (time_window['timeunit_name'],
                          np.round(time.time() - start, 2), " seconds."))

        # Save the model
        logger_m.log_heartbeat("Saving the %s model" % time_window['timeunit_name'], settings.HEARTBEAT_PATH,
                               settings.HEARTBEAT_FILE, 'SUCCEEDED')
        db_manager.save_model(averages_by_time_period_model.dt_avgs.reset_index())
            
    elif train_mode == "update":
        logger_m.log_heartbeat("Updating the %s model" % time_window['timeunit_name'], settings.HEARTBEAT_PATH,
                               settings.HEARTBEAT_FILE, 'SUCCEEDED')
        if max_request_timestamp is not None:
            logger_m.log_info('train_or_update_historic_averages_models', "Using data between %s and %s." % (last_fit_timestamp, max_request_timestamp))
        else:
            logger_m.log_info('train_or_update_historic_averages_models', "Using data from %s until today." % last_fit_timestamp)

        # Load the model
        logger_m.log_heartbeat("Loading the existing %s model" % time_window['timeunit_name'], settings.HEARTBEAT_PATH,
                               settings.HEARTBEAT_FILE, 'SUCCEEDED')
        dt_model = db_manager.load_model(model_name=time_window['timeunit_name'], version=None)
        model_version = dt_model.version.iloc[0]
        model_creation_timestamp = dt_model.model_creation_timestamp.iloc[0]

        # Discard from the model service calls that will be (re)trained
        # dt_model = dt_model.merge(data_regular[analyzer_conf.service_call_fields])
        dt_model.index = dt_model[analyzer_conf.service_call_fields]
        if len(data_first_train) > 0:
            data_first_train.index = data_first_train[analyzer_conf.service_call_fields]
            dt_model = dt_model[~dt_model.index.isin(data_first_train.index)]
        if len(data_first_retrain) > 0:
            data_first_retrain.index = data_first_retrain[analyzer_conf.service_call_fields]
            dt_model = dt_model[~dt_model.index.isin(data_first_retrain.index)]

        # Generate the correct index for the model
        dt_model = dt_model.groupby(analyzer_conf.service_call_fields + ["similar_periods"]).first()
        averages_by_time_period_model = AveragesByTimeperiodModel(time_window, analyzer_conf, dt_model,
                                                                  version=model_version,
                                                                  model_creation_timestamp=model_creation_timestamp)
        
        # Update the model using new data
        start = time.time()
        averages_by_time_period_model.update_model(data)
        logger_m.log_info('train_or_update_historic_averages_models',
                          "Updating the %s model took: %s%s" % (time_window['timeunit_name'], str(np.round(time.time() - start, 2)), " seconds."))

        # Save the updated model
        logger_m.log_heartbeat("Saving the %s model" % time_window['timeunit_name'], settings.HEARTBEAT_PATH,
                               settings.HEARTBEAT_FILE, 'SUCCEEDED')
        db_manager.save_model(averages_by_time_period_model.dt_avgs.reset_index())
    
    else:
        logger_m.log_error('train_or_update_historic_averages_models', "Unknown training mode.")

    if len(data) > 0:
        max_request_timestamp = data[analyzer_conf.timestamp_field].max()
        logger_m.log_info('train_or_update_historic_averages_models',
                          "Maximum aggregated request timestamp used: %s" % max_request_timestamp)
        logger_m.log_heartbeat("Updating last train timestamp (model %s)" % time_window['timeunit_name'],
                               settings.HEARTBEAT_PATH, settings.HEARTBEAT_FILE, 'SUCCEEDED')
        db_manager.set_timestamp(ts_type="last_fit_timestamp", model_type=time_window['timeunit_name'],
                                 value=max_request_timestamp)

# Update "first" timestamps for service calls that were trained or retrained
logger_m.log_heartbeat("Updating timestamps", settings.HEARTBEAT_PATH, settings.HEARTBEAT_FILE, 'SUCCEEDED')
db_manager.update_first_train_retrain_timestamps(sc_first_model, sc_second_model, current_time)
logger_m.log_heartbeat("Finished training", settings.HEARTBEAT_PATH, settings.HEARTBEAT_FILE, 'SUCCEEDED')
