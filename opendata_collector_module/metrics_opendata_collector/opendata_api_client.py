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

import urllib
from datetime import datetime

import requests

from metrics_opendata_collector.constants import (DT_FORMAT_W_TZ,
                                                  DT_FORMAT_WO_TZ)

DEFAULT_TZ_OFFSET = '+0000'


class InputValidationError(Exception):
    pass


class OpenDataAPIClient:
    def __init__(self, source_id: str, settings_manager):
        self._source_id = source_id
        self._settings_manager = settings_manager
        self._source_settings = (
            self._settings_manager.get_opendata_source_settings(source_id)
        )
        self._url = self._source_settings['url']
        self.timeout = self._settings_manager.settings.get('timeout') or 10

    def get_query_params(self, overrides: dict = {}) -> dict:
        dt_fields_to_query = ('from_dt', 'until_dt')

        allowed_override_keys = ('from_dt', 'from_row_id', 'offset', 'until_dt')
        params = {
            'from_dt': self._source_settings['from_dt'],
            'limit': self._source_settings['limit']
        }
        if self._source_settings.get('until_dt'):
            params['until_dt'] = self._source_settings['until_dt']

        for key in overrides:
            if key not in allowed_override_keys:
                raise InputValidationError(
                    f'{key} is not allowed for query parameters'
                )

        params.update(**overrides)

        for dt_field in dt_fields_to_query:
            if params.get(dt_field):
                params[dt_field] = self.prepare_dt_field(
                    params[dt_field], dt_field
                )
        return params

    def get_opendata(self, params_overrides: dict = {}) -> dict:
        params = self.get_query_params(params_overrides)
        encoded_params = urllib.parse.urlencode(params)
        get_url = f'{self._url}?{encoded_params}'
        response = requests.get(get_url, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def prepare_dt_field(self, dt_string: str, field_name: str) -> str:
        try:
            dt_object = datetime.strptime(dt_string, DT_FORMAT_WO_TZ)
        except ValueError:
            raise InputValidationError(
                f'{field_name} format should match format {DT_FORMAT_WO_TZ}'
            )
        dt_str = dt_object.strftime(DT_FORMAT_WO_TZ)
        tz_offset = self._source_settings.get(
            'opendata_api_tz_offset'
        ) or DEFAULT_TZ_OFFSET
        dt_str = f'{dt_str}{tz_offset}'
        try:
            dt_object = datetime.strptime(dt_str, DT_FORMAT_W_TZ)
        except ValueError:
            raise InputValidationError(
                f'{field_name} format should match format {DT_FORMAT_W_TZ}'
            )
        return dt_object.strftime(DT_FORMAT_W_TZ)
