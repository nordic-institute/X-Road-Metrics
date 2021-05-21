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

class AverageValue:
    def __init__(self):
        self.sum = 0.0
        self.count = 0

    @property
    def average(self):
        if self.count == 0:
            return None
        return self.sum / self.count

    @property
    def rounded_average(self):
        if self.average is None:
            return None
        return round(self.average)

    def add_sample(self, sample: float):
        if sample is None:
            return
        self.sum += sample
        self.count += 1

    def __repr__(self):
        return f"{self.average}"


class ReportRow:
    def __init__(self, produced_service):
        self.succeeded_queries = 0
        self.failed_queries = 0
        self.duration_min = None
        self.duration_avg = AverageValue()
        self.duration_sample_count = 0
        self.duration_max = None
        self.request_min = None
        self.request_avg = AverageValue()
        self.request_max = None
        self.response_min = None
        self.response_avg = AverageValue()
        self.response_max = None
        self.produced_service = produced_service

    def update_success_counters(self, succeeded):
        if succeeded:
            self.succeeded_queries += 1
        else:
            self.failed_queries += 1

    def calculate_duration(self, document):
        duration = document['producerDurationProducerView'] if self.produced_service else document['totalDuration']
        if duration is None:
            return

        self.duration_min = min(self.duration_min, duration) if self.duration_min is not None else duration
        self.duration_max = max(self.duration_max, duration) if self.duration_max is not None else duration
        self.duration_avg.add_sample(duration)

    def calculate_request(self, document):
        request_size = None
        if document["clientRequestSize"] is not None:
            request_size = document["clientRequestSize"]
        elif document["producerRequestSize"] is not None:
            request_size = document["producerRequestSize"]
        if request_size is None:
            return

        self.request_min = min(self.request_min, request_size) if self.request_min is not None else request_size
        self.request_max = max(self.request_max, request_size) if self.request_max is not None else request_size
        self.request_avg.add_sample(request_size)

    def calculate_response(self, document):
        response_size = None
        if document["clientResponseSize"] is not None:
            response_size = document["clientResponseSize"]
        elif document["producerResponseSize"] is not None:
            response_size = document["producerResponseSize"]

        if response_size is None:
            return

        self.response_min = min(self.response_min, response_size) if self.response_min is not None else response_size
        self.response_max = max(self.response_max, response_size) if self.response_max is not None else response_size
        self.response_avg.add_sample(response_size)

    def update_row(self, document):
        self.update_success_counters(document['succeeded'])
        if document['succeeded']:
            self.calculate_duration(document)
            self.calculate_request(document)
            self.calculate_response(document)

    def __repr__(self):
        return "{0}".format(
            [
                self.succeeded_queries,
                self.failed_queries,
                self.duration_min,
                self.duration_avg.average,
                self.duration_max,
                self.request_min,
                self.request_avg.average,
                self.request_max,
                self.response_min,
                self.response_avg.average,
                self.response_max
            ]
        )
