timestamp_field = 'requestInTs'

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

# These are present on the top level of "clean data" objects
top_level_column_names = [
    "_id",
    'totalDuration',
    'producerDurationProducerView',
    'requestNwDuration',
    'responseNwDuration',
    'correctorStatus'
]

# X-Road identifier column names
# These are present in both client and producer sections of clean data
service_identifier_column_names = [
    "clientMemberClass",
    "clientMemberCode",
    "clientXRoadInstance",
    "clientSubsystemCode",
    "serviceCode",
    "serviceVersion",
    "serviceMemberClass",
    "serviceMemberCode",
    "serviceXRoadInstance",
    "serviceSubsystemCode"
]

#  Request metadata columns in clean data client/producer sections
service_metadata_column_names = ["succeeded", "messageId", timestamp_field]
all_service_column_names = service_identifier_column_names + service_metadata_column_names

#  Alternative columns that are included primarily from client data and as a fallback from producer data.
alternative_columns = [
    {'outputName': 'requestSize', 'clientName': 'clientRequestSize', 'producerName': 'producerRequestSize'},
    {'outputName': 'responseSize', 'clientName': 'clientResponseSize', 'producerName': 'producerResponseSize'}
]
