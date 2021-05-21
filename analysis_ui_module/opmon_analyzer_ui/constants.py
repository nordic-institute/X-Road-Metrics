service_call_fields = ["clientXRoadInstance",
                       "clientMemberClass",
                       "clientMemberCode",
                       "clientSubsystemCode",
                       "serviceXRoadInstance",
                       "serviceMemberClass",
                       "serviceMemberCode",
                       "serviceSubsystemCode",
                       "serviceCode",
                       "serviceVersion"]

historic_averages_anomaly_types = [
    "request_count",
    "mean_request_size",
    "mean_response_size",
    "mean_client_duration",
    "mean_producer_duration"
]

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

# NEW INCIDENTS TABLE #

new_incident_columns = [(field, field, "categorical", None, None) for field in service_call_fields]
new_incident_columns += [("anomalous metric", "anomalous_metric", "categorical", None, None),
                         ("anomaly confidence", "anomaly_confidence", "numeric", 2, None),
                         ("period start time", "period_start_time", "date", None, "%a %Y-%m-%d %H:%M"),
                         ("aggregation timeunit", "aggregation_timeunit", "categorical", None, None),
                         ("monitored metric value", "monitored_metric_value", "numeric", 2, None),
                         ("difference from normal", "difference_from_normal", "numeric", 2, None),
                         ("request count", "request_count", "numeric", 0, None),
                         ("description", "description", "text", None, None),
                         ("comments", "comments", "text", None, None)]

# new_incident_order = [["request_count", "desc"]]
new_incident_order = [
    ["anomaly_confidence", "desc"],
    ["request_count", "desc"],
    ["period_start_time", "desc"]
]

# HISTORICAL INCIDENTS TABLE #

historical_incident_columns = new_incident_columns[:-1]
historical_incident_columns += [
    ("incident status", "incident_status", "categorical", None, None),
    ("incident update timestamp", "incident_update_timestamp", "date", None, "%a %Y-%m-%d %H:%M")
]

historical_incident_order = [["incident_update_timestamp", "desc"]]

# EXAMPLE REQUESTS TABLE #

relevant_fields_for_example_requests_general = ['totalDuration', 'producerDurationProducerView']
relevant_fields_for_example_requests_nested = ['messageId', 'requestInTs', 'succeeded']
relevant_fields_for_example_requests_alternative = [
    ('responseSize', 'clientResponseSize', 'producerResponseSize'),
    ('requestSize', 'clientRequestSize', 'producerRequestSize')
]

example_request_limit = 10  # 0 means no limit

# FILTERING

accepted_date_formats = [
    "%a %Y-%m-%d %H:%M",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y"
]

incident_expiration_time = 14400  # minutes
