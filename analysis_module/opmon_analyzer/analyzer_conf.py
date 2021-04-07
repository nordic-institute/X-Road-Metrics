class DataModelConfiguration:
    _hour_aggregation_time_window = {'agg_window_name': 'hour', 'agg_minutes': 60, 'pd_timeunit': 'h'}
    _day_aggregation_time_window = {'agg_window_name': 'day', 'agg_minutes': 1440, 'pd_timeunit': 'd'}

    def __init__(self, settings):
        self.time_windows = self._init_time_windows(settings)

    def _init_time_windows(self, settings):
        time_windows = {}
        for key in ["failed_request_ratio", "duplicate_message_ids", "time_sync_errors"]:
            settings_key = key.replace('_', '-')
            if settings['analyzer'][settings_key]['hourly-time-window']:
                time_windows[key] = self._hour_aggregation_time_window
            else:
                time_windows[key] = self._day_aggregation_time_window

        return time_windows

    # for historic averages model, we also need to determine which are the "similar" periods
    hour_weekday_similarity_time_window = {
        'timeunit_name': 'hour_weekday',
        'agg_window': _hour_aggregation_time_window,
        'similar_periods': ['hour', 'weekday']
    }

    weekday_similarity_time_window = {
        'timeunit_name': 'weekday',
        'agg_window': _day_aggregation_time_window,
        'similar_periods': ['weekday']
    }

    hour_monthday_similarity_time_window = {
        'timeunit_name': 'hour_monthday',
        'agg_window': _hour_aggregation_time_window,
        'similar_periods': ['hour', 'day']
    }

    monthday_similarity_time_window = {
        'timeunit_name': 'monthday',
        'agg_window': _day_aggregation_time_window,
        'similar_periods': ['day']
    }

    historic_averages_time_windows = [
        (hour_weekday_similarity_time_window, "update"),
        (weekday_similarity_time_window, "update")
    ]

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
