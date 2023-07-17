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

from django.urls import include, path
from opmon_opendata import django_settings as settings
from opmon_opendata.api import views

urlpatterns = [
    path('heartbeat', views.heartbeat),
    path('daily_logs', views.get_daily_logs),
    path('daily_logs_meta', views.get_daily_logs_meta),
    path('logs_sample', views.get_preview_data),
    path('date_range', views.get_date_range),
    path('column_data', views.get_column_data),
    path('statistics', views.get_statistics_data),
]
if not settings.DISABLE_OPENDATA_HARVEST:
    urlpatterns.append(
        path('harvest', views.get_harvest_data)
    )
