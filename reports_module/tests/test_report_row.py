import random
import unittest

from reports_module.reportslib.report_row import ReportRow


class TestReportRow(unittest.TestCase):
    def test_calculate_succeeded_queries(self):
        report_row = ReportRow(None)

        number_of_succeeded = 300
        number_of_failed = 200

        for i in range(number_of_succeeded):
            report_row.calculate_succeeded_queries(True)
        for i in range(number_of_failed):
            report_row.calculate_succeeded_queries(False)

        self.assertEqual(report_row.succeeded_queries, number_of_succeeded)

    def test_calculate_failed_queries(self):
        report_row = ReportRow(None)

        number_of_succeeded = 300
        number_of_failed = 200

        for i in range(number_of_succeeded):
            report_row.calculate_failed_queries(True)
        for i in range(number_of_failed):
            report_row.calculate_failed_queries(False)

        self.assertEqual(report_row.failed_queries, number_of_failed)

    def test_calculate_duration(self):
        report_row_producer = ReportRow(True)
        report_row_consumer = ReportRow(False)

        number_of_producers = 300
        number_of_consumers = 200

        producers_duration = []
        for i in range(number_of_producers):
            duration = random.randint(0, 1000)
            producers_duration.append(duration)
            new_doc = {'producerDurationProducerView': duration, 'totalDuration': None}
            new_doc_none = {'producerDurationProducerView': None, 'totalDuration': None}
            report_row_producer.calculate_duration(new_doc)
            report_row_producer.calculate_duration(new_doc_none)

        self.assertEqual(report_row_producer.duration_min, min(producers_duration))
        self.assertEqual(report_row_producer.duration_max, max(producers_duration))
        self.assertEqual(report_row_producer.duration_avg, (sum(producers_duration), number_of_producers))

        consumers_duration = []
        for i in range(number_of_consumers):
            duration = random.randint(0, 1000)
            consumers_duration.append(duration)
            new_doc = {'producerDurationProducerView': None, 'totalDuration': duration}
            new_doc_none = {'producerDurationProducerView': None, 'totalDuration': None}
            report_row_consumer.calculate_duration(new_doc)
            report_row_consumer.calculate_duration(new_doc_none)

        self.assertEqual(report_row_consumer.duration_min, min(consumers_duration))
        self.assertEqual(report_row_consumer.duration_max, max(consumers_duration))
        self.assertEqual(report_row_consumer.duration_avg, (sum(consumers_duration), number_of_consumers))

    def test_calculate_request(self):
        report_row_producer = ReportRow(None)
        report_row_consumer = ReportRow(None)

        number_of_client_requirements = 300
        number_of_producer_requirements = 200

        client_requirements = []
        for i in range(number_of_client_requirements):
            request_size = random.randint(0, 1000)
            client_requirements.append(request_size)
            new_doc = {'clientRequestSize': request_size, 'producerRequestSize': None}
            new_doc_none = {'clientRequestSize': None, 'producerRequestSize': None}
            report_row_producer.calculate_request(new_doc)
            report_row_producer.calculate_request(new_doc_none)

        self.assertEqual(report_row_producer.request_min, min(client_requirements))
        self.assertEqual(report_row_producer.request_max, max(client_requirements))
        self.assertEqual(report_row_producer.request_avg, (sum(client_requirements), number_of_client_requirements))

        producer_requirements = []
        for i in range(number_of_producer_requirements):
            request_size = random.randint(0, 1000)
            producer_requirements.append(request_size)
            new_doc = {'clientRequestSize': None, 'producerRequestSize': request_size}
            new_doc_none = {'clientRequestSize': None, 'producerRequestSize': None}
            report_row_consumer.calculate_request(new_doc)
            report_row_consumer.calculate_request(new_doc_none)

        self.assertEqual(report_row_consumer.request_min, min(producer_requirements))
        self.assertEqual(report_row_consumer.request_max, max(producer_requirements))
        self.assertEqual(report_row_consumer.request_avg, (sum(producer_requirements), number_of_producer_requirements))

    def test_calculate_response(self):
        report_row_producer = ReportRow(None)
        report_row_consumer = ReportRow(None)

        number_of_client_requirements = 300
        number_of_producer_requirements = 200

        client_requirements = []
        for i in range(number_of_client_requirements):
            response_size = random.randint(0, 1000)
            client_requirements.append(response_size)
            new_doc = {'clientResponseSize': response_size, 'producerResponseSize': None}
            new_doc_none = {'clientResponseSize': None, 'producerResponseSize': None}
            report_row_producer.calculate_response(new_doc)
            report_row_producer.calculate_response(new_doc_none)

        self.assertEqual(report_row_producer.response_min, min(client_requirements))
        self.assertEqual(report_row_producer.response_max, max(client_requirements))
        self.assertEqual(report_row_producer.response_avg, (sum(client_requirements), number_of_client_requirements))

        producer_requirements = []
        for i in range(number_of_producer_requirements):
            response_size = random.randint(0, 1000)
            producer_requirements.append(response_size)
            new_doc = {'clientResponseSize': None, 'producerResponseSize': response_size}
            new_doc_none = {'clientResponseSize': None, 'producerResponseSize': None}
            report_row_consumer.calculate_response(new_doc)
            report_row_consumer.calculate_response(new_doc_none)

        self.assertEqual(report_row_consumer.response_min, min(producer_requirements))
        self.assertEqual(report_row_consumer.response_max, max(producer_requirements))
        self.assertEqual(report_row_consumer.response_avg,
                         (sum(producer_requirements), number_of_producer_requirements))

    def test_update_row(self):
        report_row_producer = ReportRow(None)
        number_of_clients = 300

        client_responses = []
        client_requests = []
        client_durations = []
        for i in range(number_of_clients):
            response_size = random.randint(0, 1000)
            request_size = random.randint(0, 1000)
            duration_size = random.randint(0, 1000)
            client_responses.append(response_size)
            client_requests.append(request_size)
            client_durations.append(duration_size)
            new_doc = {
                'clientResponseSize': response_size, 'producerResponseSize': response_size,
                'clientRequestSize': request_size, 'producerRequestSize': request_size, 'succeeded': True,
                'producerDurationProducerView': duration_size, 'totalDuration': duration_size}
            new_doc_none = {
                'clientResponseSize': None, 'producerResponseSize': None,
                'clientRequestSize': None, 'producerRequestSize': None, 'succeeded': None,
                'producerDurationProducerView': None, 'totalDuration': None
            }
            report_row_producer.update_row(new_doc.copy())
            report_row_producer.update_row(new_doc_none.copy())

        self.assertEqual(report_row_producer.response_min, min(client_responses))
        self.assertEqual(report_row_producer.response_max, max(client_responses))
        self.assertEqual(report_row_producer.response_avg, (sum(client_responses), number_of_clients))
        self.assertEqual(report_row_producer.request_min, min(client_requests))
        self.assertEqual(report_row_producer.request_max, max(client_requests))
        self.assertEqual(report_row_producer.request_avg, (sum(client_requests), number_of_clients))
        self.assertEqual(report_row_producer.duration_min, min(client_durations))
        self.assertEqual(report_row_producer.duration_max, max(client_durations))
        self.assertEqual(report_row_producer.duration_avg, (sum(client_durations), number_of_clients))
        self.assertEqual(report_row_producer.succeeded_queries, number_of_clients)
        # It is equal to number_of_clients because the "succeeded": None means it is False in the new_doc_none.
        self.assertEqual(report_row_producer.failed_queries, number_of_clients)

    def test_return_row(self):
        report_row_producer = ReportRow(None)
        row = [0, 0, None, (None, None), None, None, (None, None), None, None, (None, None), None]
        self.assertEqual(report_row_producer.return_row(), row)

        report_row_producer = ReportRow(None)
        number_of_clients = 300

        client_responses = []
        client_requests = []
        client_durations = []
        for i in range(number_of_clients):
            response_size = random.randint(0, 1000)
            request_size = random.randint(0, 1000)
            duration_size = random.randint(0, 1000)
            client_responses.append(response_size)
            client_requests.append(request_size)
            client_durations.append(duration_size)
            new_doc = {
                'clientResponseSize': response_size, 'producerResponseSize': response_size,
                'clientRequestSize': request_size, 'producerRequestSize': request_size, 'succeeded': True,
                'producerDurationProducerView': duration_size, 'totalDuration': duration_size}
            new_doc_none = {
                'clientResponseSize': None, 'producerResponseSize': None,
                'clientRequestSize': None, 'producerRequestSize': None, 'succeeded': None,
                'producerDurationProducerView': None, 'totalDuration': None
            }
            report_row_producer.update_row(new_doc.copy())
            report_row_producer.update_row(new_doc_none.copy())

        row = [number_of_clients, number_of_clients, min(client_durations), (sum(client_durations), number_of_clients),
               max(client_durations), min(client_requests), (sum(client_requests), number_of_clients),
               max(client_requests), min(client_responses), (sum(client_responses), number_of_clients),
               max(client_responses)]

        self.assertEqual(report_row_producer.return_row(), row)
