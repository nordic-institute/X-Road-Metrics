class DataModelConfiguration:
    """Create data model time windows and thresholds based on settings.yaml"""

    _hour_aggregation_time_window = {'agg_window_name': 'hour', 'agg_minutes': 60, 'pd_timeunit': 'h'}
    _day_aggregation_time_window = {'agg_window_name': 'day', 'agg_minutes': 1440, 'pd_timeunit': 'd'}

    def __init__(self, settings):
        self.time_windows = self._init_time_windows(settings)
        self.historic_averages_thresholds = self._init_historic_averages_thresholds(settings)
        self.time_sync_monitored_lower_thresholds = self._init_time_sync_monitored_lower_thresholds(settings)

    def _init_time_windows(self, settings):
        time_windows = {}
        for key in ["failed_request_ratio", "duplicate_message_ids", "time_sync_errors"]:
            settings_key = key.replace('_', '-')
            if settings['analyzer'][settings_key]['hourly-time-window']:
                time_windows[key] = self._hour_aggregation_time_window
            else:
                time_windows[key] = self._day_aggregation_time_window

        return time_windows

    @staticmethod
    def _init_historic_averages_thresholds(settings):
        threshold_settings = settings['analyzer']['historic-averages']['thresholds']
        return {
            key: threshold_settings[key] for key in [
                'request_count',
                'mean_request_size',
                'mean_response_size',
                'mean_client_duration',
                'mean_producer_duration'
            ]
        }

    @staticmethod
    def _init_time_sync_monitored_lower_thresholds(settings):
        threshold_settings = settings['analyzer']['time-sync-errors']['thresholds']
        return {key: threshold_settings[key] for key in ['requestNwDuration', 'responseNwDuration']}

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
