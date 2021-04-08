class DataModelConfiguration:
    """Create data model time windows and thresholds based on settings.yaml"""

    def __init__(self, settings):
        self.time_windows = self._init_time_windows(settings)
        self.historic_averages_time_windows = self._init_historic_averages_time_windows(settings)
        self.historic_averages_thresholds = settings['analyzer']['historic-averages']['thresholds']
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

    def _init_historic_averages_time_windows(self, settings):

        map_settings_to_time_windows = {
            'hour-weekday': self._hour_weekday_similarity_time_window,
            'weekday': self._weekday_similarity_time_window,
            'hour-monthday': self._hour_monthday_similarity_time_window,
            'monthday': self._hour_monthday_similarity_time_window
        }

        return [
            (time_window, "update")
            for key, time_window in map_settings_to_time_windows.items()
            if settings['analyzer']['historic-averages']['time-windows'][key]
        ]

    @staticmethod
    def _init_time_sync_monitored_lower_thresholds(settings):
        threshold_settings = settings['analyzer']['time-sync-errors']['thresholds']
        return {key: threshold_settings[key] for key in ['requestNwDuration', 'responseNwDuration']}

    _hour_aggregation_time_window = {'agg_window_name': 'hour', 'agg_minutes': 60, 'pd_timeunit': 'h'}
    _day_aggregation_time_window = {'agg_window_name': 'day', 'agg_minutes': 1440, 'pd_timeunit': 'd'}

    _hour_weekday_similarity_time_window = {
        'timeunit_name': 'hour_weekday',
        'agg_window': _hour_aggregation_time_window,
        'similar_periods': ['hour', 'weekday']
    }

    _weekday_similarity_time_window = {
        'timeunit_name': 'weekday',
        'agg_window': _day_aggregation_time_window,
        'similar_periods': ['weekday']
    }

    _hour_monthday_similarity_time_window = {
        'timeunit_name': 'hour_monthday',
        'agg_window': _hour_aggregation_time_window,
        'similar_periods': ['hour', 'day']
    }

    _monthday_similarity_time_window = {
        'timeunit_name': 'monthday',
        'agg_window': _day_aggregation_time_window,
        'similar_periods': ['day']
    }
