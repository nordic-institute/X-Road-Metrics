#
# The MIT License 
# Copyright (c) 2021- Nordic Institute for Interoperability Solutions (NIIS)
# Copyright (c) 2017-2020 Estonian Information System Authority (RIA)
#  
# Permission is hereby granted, free of charge, to any person obtaining a copy 
# of this software and associated documentation files (the "Software"), to deal 
# in the Software without restriction, including without limitation the rights 
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions: 
#  
# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software. 
#  
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN 
# THE SOFTWARE.
#

from datetime import datetime


def reduce_request_in_ts_precision(record):
    timestamp = int(record['requestInTs'] / 1000)
    initial_datetime = datetime.fromtimestamp(timestamp)
    altered_datetime = initial_datetime.replace(minute=0, second=0)
    record['requestInTs'] = int(altered_datetime.timestamp()) * 1000
    return record


def force_durations_to_integer_range(record):
    total_duration = record['totalDuration']
    if total_duration:
        record['totalDuration'] = (min(total_duration, 2**31 - 1) if total_duration > 0
                                   else max(total_duration, -(2**31 - 1)))

    producer_duration = record['producerDurationProducerView']
    if producer_duration:
        record['producerDurationProducerView'] = (min(producer_duration, 2**31 - 1) if producer_duration > 0
                                                  else max(producer_duration, -(2**31 - 1)))
    return record
