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

# TODO: add exception handling
#
from opmon_analyzer.AnalyzerDatabaseManager import AnalyzerDatabaseManager
from opmon_analyzer.models.AveragesByTimeperiodModel import AveragesByTimeperiodModel
from opmon_analyzer import analyzer_conf

from . import constants
from .logger_manager import LoggerManager
from . import __version__

import time
import datetime
from dateutil.relativedelta import relativedelta

import numpy as np
import pandas as pd


def update_model(settings):
    config = analyzer_conf.DataModelConfiguration(settings)
    log_activity = 'train_or_update_historic_averages_models'
    db_manager = AnalyzerDatabaseManager(settings)
    logger_m = LoggerManager(settings['logger'], settings['xroad']['instance'], __version__)

    # add first request timestamps for service calls that have appeared
    logger_m.log_heartbeat("Checking if completely new service calls have appeared", 'SUCCEEDED')
    db_manager.add_first_request_timestamps_from_clean_data()

    metric_names = list(config.historic_averages_thresholds.keys())

    current_time = datetime.datetime.now()
    buffer_time = settings['analyzer']['corrector-buffer-time']
    incident_expiration_time = settings['analyzer']['incident-expiration-time']

    max_incident_creation_time = current_time - datetime.timedelta(minutes=incident_expiration_time)
    first_model_train_time = get_first_model_train_time(settings, current_time, logger_m)
    max_request_time = current_time - datetime.timedelta(minutes=buffer_time)

    # retrieve service calls according to stages
    logger_m.log_heartbeat("Determining service call stages", "SUCCEEDED")
    logger_m.log_info(
        log_activity,
        f"Getting service calls for trains stages, t1: {first_model_train_time} t2: {max_incident_creation_time}"
    )
    sc_regular, sc_first_model, sc_second_model = db_manager.get_service_calls_for_train_stages(
        time_first_model=first_model_train_time,
        time_second_model=max_incident_creation_time
    )

    logger_m.log_info(
        log_activity,
        f"Number of service calls for first model training: {len(sc_first_model)}"
    )

    logger_m.log_info(
        log_activity,
        f"Number of service calls for model re-training: {len(sc_second_model)}"
    )

    logger_m.log_info(
        log_activity,
        f"Number of service calls that will be updated in regular mode: {len(sc_regular)}"
    )

    if len(sc_first_model) == 0 and len(sc_second_model) == 0 and len(sc_regular) == 0:
        logger_m.log_info(log_activity, "No data to train or update historic average models")
        return

    # 4.3.5 - 4.3.9 Comparison with historic averages for:
    # request count, response size, request size, response duration, request duration
    for time_window, train_mode in config.historic_averages_time_windows:
        model_type = time_window['timeunit_name']
        last_fit_timestamp = db_manager.get_timestamp(ts_type="last_fit_timestamp",
                                                      model_type=model_type)
        last_fit_timestamp = last_fit_timestamp if train_mode != "retrain" else None

        min_incident_creation_timestamp = (
            None if last_fit_timestamp is None
            else last_fit_timestamp - datetime.timedelta(minutes=incident_expiration_time)
        )

        start = time.time()
        logger_m.log_heartbeat(
            f"Retrieving data according to service call stages ({model_type} model)", "SUCCEEDED")

        data_regular, data_first_train, data_first_retrain = db_manager.get_data_for_train_stages(
            sc_regular=sc_regular,
            sc_first_model=sc_first_model,
            sc_second_model=sc_second_model,
            relevant_anomalous_metrics=metric_names,
            max_incident_creation_timestamp=max_incident_creation_time,
            last_fit_timestamp=last_fit_timestamp,
            agg_minutes=time_window["agg_window"]["agg_minutes"],
            max_request_timestamp=max_request_time,
            min_incident_creation_timestamp=min_incident_creation_timestamp,
            aggregation_timeunits=[time_window['agg_window']['agg_window_name']]
        )
        data = pd.concat([data_regular, data_first_train, data_first_retrain])

        logger_m.log_info(log_activity, f"Data (regular training) shape is: {str(data_regular.shape)}")
        logger_m.log_info(log_activity, f"Data (first-time training) shape is: {str(data_first_train.shape)}")
        logger_m.log_info(log_activity, f"Data (retraining) shape is: {str(data_first_retrain.shape)}")

        t0 = np.round(time.time() - start, 2)
        logger_m.log_info(log_activity, f"Aggregating the data took: {t0} seconds")

        if train_mode == "retrain" or last_fit_timestamp is None:
            logger_m.log_heartbeat(f"Training the {model_type} model", 'SUCCEEDED')
            if max_request_time is not None:
                logger_m.log_info(log_activity, f"Using data until {max_request_time}.")
            else:
                logger_m.log_info(log_activity, "Using all data.")

            # Fit the model
            start = time.time()
            averages_by_time_period_model = AveragesByTimeperiodModel(time_window, config)
            averages_by_time_period_model.fit(data)

            t0 = np.round(time.time() - start, 2)
            logger_m.log_info(log_activity, f"Averages by timeperiod model ({model_type}) fitting time: {t0} seconds")

            # Save the model
            logger_m.log_heartbeat(f"Saving the {model_type} model", 'SUCCEEDED')
            db_manager.save_model(averages_by_time_period_model.dt_avgs.reset_index())

        elif train_mode == "update":
            logger_m.log_heartbeat(f"Updating the {model_type} model", 'SUCCEEDED')
            if max_request_time is not None:
                logger_m.log_info(log_activity, f"Using data between {last_fit_timestamp} and {max_request_time}.")
            else:
                logger_m.log_info(log_activity, f"Using data from {last_fit_timestamp} until today.")

            # Load the model
            logger_m.log_heartbeat(f"Loading the existing {model_type} model", 'SUCCEEDED')
            dt_model = db_manager.load_model(model_name=model_type, version=None)
            model_version = dt_model.version.iloc[0]
            model_creation_timestamp = dt_model.model_creation_timestamp.iloc[0]

            # Discard from the model service calls that will be (re)trained
            dt_model.index = dt_model[constants.service_identifier_column_names]
            if len(data_first_train) > 0:
                data_first_train.index = data_first_train[constants.service_identifier_column_names]
                dt_model = dt_model[~dt_model.index.isin(data_first_train.index)]
            if len(data_first_retrain) > 0:
                data_first_retrain.index = data_first_retrain[constants.service_identifier_column_names]
                dt_model = dt_model[~dt_model.index.isin(data_first_retrain.index)]

            # Generate the correct index for the model
            dt_model = dt_model.groupby(constants.service_identifier_column_names + ["similar_periods"]).first()
            averages_by_time_period_model = AveragesByTimeperiodModel(
                time_window,
                config,
                dt_model,
                version=model_version,
                model_creation_timestamp=model_creation_timestamp
            )

            # Update the model using new data
            start = time.time()
            averages_by_time_period_model.update_model(data)

            t0 = np.round(time.time() - start, 2)
            logger_m.log_info(log_activity, f"Updating the {model_type} model took: {t0} seconds")

            # Save the updated model
            logger_m.log_heartbeat(f"Saving the {model_type} model", 'SUCCEEDED')
            db_manager.save_model(averages_by_time_period_model.dt_avgs.reset_index())

        else:
            logger_m.log_error(log_activity, "Unknown training mode.")

        if len(data) > 0:
            max_request_time = data[constants.timestamp_field].max()

            logger_m.log_info(log_activity, f"Maximum aggregated request timestamp used: {max_request_time}")
            logger_m.log_heartbeat(f"Updating last train timestamp (model {model_type})", 'SUCCEEDED')

            db_manager.set_timestamp(ts_type="last_fit_timestamp", model_type=model_type, value=max_request_time)

    # Update "first" timestamps for service calls that were trained or retrained
    logger_m.log_heartbeat("Updating timestamps", 'SUCCEEDED')
    db_manager.update_first_train_retrain_timestamps(sc_first_model, sc_second_model, current_time)
    logger_m.log_heartbeat("Finished training", 'SUCCEEDED')


def get_first_model_train_time(settings, current_time, logger_m):
    length = settings['analyzer']['training-period']['length']
    unit = settings['analyzer']['training-period']['unit']
    deltas = {
        "MONTHS": relativedelta(months=length),
        "WEEKS": relativedelta(weeks=length),
        "DAYS": relativedelta(days=length)
    }

    if unit not in deltas:
        logger_m("get_first_model_train_time", f"Invalid unit for training-period. Options are: {deltas.keys()}")
        raise ValueError("Invalid unit for training-period.")

    return current_time - deltas[unit]
