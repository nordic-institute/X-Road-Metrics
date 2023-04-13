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

import requests


class OpenDataAPIClient:
    def __init__(self, xroad_settings, source_settings):
        self.source_settings = source_settings
        self.url = self.source_settings['url']
        self.timeout = xroad_settings.get('timeout') or 10

    def _get_request_params(self, overrides={}):
        params = {
            'from_dt': self.source_settings['from_dt'].isoformat(),
            'timestamp_tz': self.source_settings.get('timestamp_tz'),
            'limit': self.source_settings['limit']
        }
        if overrides.get('from_row_id'):
            params['from_row_id'] = overrides['from_row_id']

        if overrides.get('offset'):
            params['offset'] = overrides['offset']

        return params

    def get_opendata(self, params_overrides={}):
        params = self._get_request_params(params_overrides)

        encoded_params = urllib.parse.urlencode(params)
        get_url = f'{self.url}?{encoded_params}'

        response = requests.get(get_url, timeout=self.timeout)
        response.raise_for_status()
        response_data = response.json()
        return response_data['data'], response_data['columns'], response_data['total_query_count']
