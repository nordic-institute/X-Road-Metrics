# some specific relevant fields
timestamp_field = 'requestInTs'
service_call_fields = ["clientMemberClass", "clientMemberCode", "clientXRoadInstance", "clientSubsystemCode",
                       "serviceCode", "serviceVersion", "serviceMemberClass", "serviceMemberCode",
                       "serviceXRoadInstance", "serviceSubsystemCode"]

# Fields to query from the database

# 'relevant_cols_general' are fields that are present on the top level
relevant_cols_general = ["_id", 'totalDuration', 'producerDurationProducerView', 'requestNwDuration',
                         'responseNwDuration', 'correctorStatus']

# 'relevant_cols_nested' are fields that are nested inside 'client' and 'producer'.
# If 'client' is present, values for these fields will be taken from there, otherwise from 'producer'.
relevant_cols_nested = service_call_fields + ["succeeded", "messageId", timestamp_field]

# 'relevant_cols_general_alternative' are fields that are present on the top level, but exist for both
# client and producer.
# The value will be taken from the field assigned in the second position in the triplet if it exists,
# otherwise from the third field. The first value in the triplet is the name that will be used.
# Example: metric 'requestSize' will be assigned value from database field 'clientRequestSize' if it exists,
# otherwise from the database field 'producerRequestSize'.
relevant_cols_general_alternative = [('requestSize', 'clientRequestSize', 'producerRequestSize'),
                                     ('responseSize', 'clientResponseSize', 'producerResponseSize')]

# some possible aggregation windows
hour_aggregation_time_window = {'agg_window_name': 'hour', 'agg_minutes': 60, 'pd_timeunit': 'h'}
day_aggregation_time_window = {'agg_window_name': 'day', 'agg_minutes': 1440, 'pd_timeunit': 'd'}

# for historic averages model, we also need to determine which are the "similar" periods
hour_weekday_similarity_time_window = {'timeunit_name': 'hour_weekday', 'agg_window': hour_aggregation_time_window,
                                       'similar_periods': ['hour', 'weekday']}

weekday_similarity_time_window = {'timeunit_name': 'weekday', 'agg_window': day_aggregation_time_window,
                                  'similar_periods': ['weekday']}

hour_monthday_similarity_time_window = {'timeunit_name': 'hour_monthday', 'agg_window': hour_aggregation_time_window,
                                        'similar_periods': ['hour', 'day']}

monthday_similarity_time_window = {'timeunit_name': 'monthday', 'agg_window': day_aggregation_time_window,
                                   'similar_periods': ['day']}

# which windows are actually used
time_windows = {"failed_request_ratio": hour_aggregation_time_window,
                "duplicate_message_ids": day_aggregation_time_window,
                "time_sync_errors": hour_aggregation_time_window}

historic_averages_time_windows = [(hour_weekday_similarity_time_window, "update"),
                                  (weekday_similarity_time_window, "update")]

# set the relevant fields (metrics) that will be monitored, aggregation functions to apply
# and their anomaly confidence thresholds for the historic averages model
historic_averages_thresholds = {'request_count': 0.95,
                                'mean_request_size': 0.95,
                                'mean_response_size': 0.95,
                                'mean_client_duration': 0.95,
                                'mean_producer_duration': 0.95}

# set the relevant fields for monitoring time sync anomalies, and the respective minimum value threshold
time_sync_monitored_lower_thresholds = {'requestNwDuration': -2000,
                                        'responseNwDuration': -2000}

# set the ratio of allowed failed requests per time window
failed_request_ratio_threshold = 0.9

corrector_buffer_time = 14400  # minutes
incident_expiration_time = 14400  # minutes
training_period_time = 3  # months
