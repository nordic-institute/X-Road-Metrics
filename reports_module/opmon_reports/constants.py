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

import os

# --------------------------------------------------------
# Report constants
# --------------------------------------------------------
# The column order for produced services
PRODUCED_SERVICES_COLUMN_ORDER = [
    "SERVICE",
    "CLIENT",
    "SUCCEEDED_QUERIES",
    "FAILED_QUERIES",
    "DURATION_MIN_MEAN_MAX_MS",
    "REQUEST_SIZE_MIN_MEAN_MAX_B",
    "RESPONSE_SIZE_MIN_MEAN_MAX_B"
]

# The column order for consumed services
CONSUMED_SERVICES_COLUMN_ORDER = [
    "PRODUCER",
    "SERVICE",
    "SUCCEEDED_QUERIES",
    "FAILED_QUERIES",
    "DURATION_MIN_MEAN_MAX_MS",
    "REQUEST_SIZE_MIN_MEAN_MAX_B",
    "RESPONSE_SIZE_MIN_MEAN_MAX_B"
]

# Sort the report rows by the following columns
PRODUCED_SERVICES_SORTING_ORDER = ["SERVICE", "CLIENT"]
CONSUMED_SERVICES_SORTING_ORDER = ["PRODUCER", "SERVICE"]

# Group the report rows by the following columns
PRODUCED_SERVICES_GROUPING_ORDER = ["SERVICE", "CLIENT"]
CONSUMED_SERVICES_GROUPING_ORDER = ["PRODUCER", "SERVICE"]

# The list of services that are considered as meta services
META_SERVICE_LIST = ["getWsdl", "listMethods", "allowedMethods", "getSecurityServerMetrics",
                     "getSecurityServerOperationalData", "getSecurityServerHealthData",
                     "getOpenAPI"]

# The following producer fields are merged
PRODUCER_MERGED_FIELDS_1 = (["serviceCode", "serviceVersion"], ".", "service")
PRODUCER_MERGED_FIELDS_2 = (
    ["clientXRoadInstance", "clientMemberClass", "clientMemberCode", "clientSubsystemCode"], "/", "client")

# The following consumer fields are merged
CONSUMER_MERGED_FIELDS_1 = (["serviceCode", "serviceVersion"], ".", "service")
CONSUMER_MERGED_FIELDS_2 = (
    ["serviceXRoadInstance", "serviceMemberClass", "serviceMemberCode", "serviceSubsystemCode"], "/", "producer")

# Report logo image paths
LOGO_IMAGE_1 = os.path.join("{IMAGE_PATH}", "xroad-metrics-vertical.png")
LOGO_IMAGE_2 = os.path.join("{IMAGE_PATH}", "eu_rdf_100_{LANGUAGE}.png")
