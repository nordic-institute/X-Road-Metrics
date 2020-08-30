class ReportRow:
    def __init__(self, produced_service):
        self.succeeded_queries = 0
        self.failed_queries = 0
        self.duration_min = None
        self.duration_avg = (None, None)
        self.duration_max = None
        self.request_min = None
        self.request_avg = (None, None)
        self.request_max = None
        self.response_min = None
        self.response_avg = (None, None)
        self.response_max = None
        self.produced_service = produced_service

    def calculate_succeeded_queries(self, succeeded):
        self.succeeded_queries += 1 if succeeded else 0

    def calculate_failed_queries(self, succeeded):
        self.failed_queries += 1 if not succeeded else 0

    def calculate_duration(self, document):
        duration = document['producerDurationProducerView'] if self.produced_service else document['totalDuration']
        if duration is not None:
            self.duration_min = min(self.duration_min, duration) if self.duration_min is not None else duration
            self.duration_avg = (
                self.duration_avg[0] + duration, self.duration_avg[1] + 1) if self.duration_avg[0] is not None else (
                duration, 1)
            self.duration_max = max(self.duration_max, duration) if self.duration_max is not None else duration

    def calculate_request(self, document):
        request_size = None
        if document["clientRequestSize"] is not None:
            request_size = document["clientRequestSize"]
        elif document["producerRequestSize"] is not None:
            request_size = document["producerRequestSize"]
        if request_size is not None:
            self.request_min = min(self.request_min, request_size) if self.request_min is not None else request_size
            self.request_avg = (
                self.request_avg[0] + request_size, self.request_avg[1] + 1) if self.request_avg[0] is not None else (
                request_size, 1)
            self.request_max = max(self.request_max, request_size) if self.request_max is not None else request_size

    def calculate_response(self, document):
        response_size = None
        if document["clientResponseSize"] is not None:
            response_size = document["clientResponseSize"]
        elif document["producerResponseSize"] is not None:
            response_size = document["producerResponseSize"]
        if response_size is not None:
            self.response_min = min(self.response_min,
                                    response_size) if self.response_min is not None else response_size
            self.response_avg = (
                self.response_avg[0] +
                response_size, self.response_avg[1] + 1) if self.response_avg[0] is not None else (response_size, 1)
            self.response_max = max(self.response_max,
                                    response_size) if self.response_max is not None else response_size

    def update_row(self, document):
        self.calculate_succeeded_queries(document['succeeded'])
        self.calculate_failed_queries(document['succeeded'])
        if document['succeeded']:
            self.calculate_duration(document)
            self.calculate_request(document)
            self.calculate_response(document)

    def return_row(self):
        return [self.succeeded_queries, self.failed_queries, self.duration_min, self.duration_avg, self.duration_max,
                self.request_min, self.request_avg, self.request_max, self.response_min, self.response_avg,
                self.response_max]

    def __repr__(self):
        return "{0}".format(self.return_row())
