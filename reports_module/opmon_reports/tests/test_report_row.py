import pytest
import random
from opmon_reports.report_row import ReportRow


@pytest.fixture()
def random_row():
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
    return report_row_producer, client_requests, client_responses, number_of_clients, client_durations


def test_update_success_counters():
    report_row = ReportRow(None)

    success_test_data = [True, False, True] * 4
    for success in success_test_data:
        report_row.update_success_counters(success)

    assert report_row.succeeded_queries == success_test_data.count(True)
    assert report_row.failed_queries == success_test_data.count(False)


def test_calculate_duration():
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

    assert (report_row_producer.duration_min == min(producers_duration))
    assert (report_row_producer.duration_max == max(producers_duration))
    assert (report_row_producer.duration_avg == (sum(producers_duration), number_of_producers))

    consumers_duration = []
    for i in range(number_of_consumers):
        duration = random.randint(0, 1000)
        consumers_duration.append(duration)
        new_doc = {'producerDurationProducerView': None, 'totalDuration': duration}
        new_doc_none = {'producerDurationProducerView': None, 'totalDuration': None}
        report_row_consumer.calculate_duration(new_doc)
        report_row_consumer.calculate_duration(new_doc_none)

    assert (report_row_consumer.duration_min == min(consumers_duration))
    assert (report_row_consumer.duration_max == max(consumers_duration))
    assert (report_row_consumer.duration_avg == (sum(consumers_duration), number_of_consumers))


def test_calculate_request():
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

    assert (report_row_producer.request_min == min(client_requirements))
    assert (report_row_producer.request_max == max(client_requirements))
    assert (report_row_producer.request_avg == (sum(client_requirements), number_of_client_requirements))

    producer_requirements = []
    for i in range(number_of_producer_requirements):
        request_size = random.randint(0, 1000)
        producer_requirements.append(request_size)
        new_doc = {'clientRequestSize': None, 'producerRequestSize': request_size}
        new_doc_none = {'clientRequestSize': None, 'producerRequestSize': None}
        report_row_consumer.calculate_request(new_doc)
        report_row_consumer.calculate_request(new_doc_none)

    assert (report_row_consumer.request_min == min(producer_requirements))
    assert (report_row_consumer.request_max == max(producer_requirements))
    assert (report_row_consumer.request_avg == (sum(producer_requirements), number_of_producer_requirements))


def test_calculate_response():
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

    assert (report_row_producer.response_min == min(client_requirements))
    assert (report_row_producer.response_max == max(client_requirements))
    assert (report_row_producer.response_avg == (sum(client_requirements), number_of_client_requirements))

    producer_requirements = []
    for i in range(number_of_producer_requirements):
        response_size = random.randint(0, 1000)
        producer_requirements.append(response_size)
        new_doc = {'clientResponseSize': None, 'producerResponseSize': response_size}
        new_doc_none = {'clientResponseSize': None, 'producerResponseSize': None}
        report_row_consumer.calculate_response(new_doc)
        report_row_consumer.calculate_response(new_doc_none)

    assert (report_row_consumer.response_min == min(producer_requirements))
    assert (report_row_consumer.response_max == max(producer_requirements))
    assert (report_row_consumer.response_avg == (sum(producer_requirements), number_of_producer_requirements))


def test_update_row(random_row):
    report_row_producer, client_requests, client_responses, number_of_clients, client_durations = random_row

    assert (report_row_producer.response_min == min(client_responses))
    assert (report_row_producer.response_max == max(client_responses))
    assert (report_row_producer.response_avg == (sum(client_responses), number_of_clients))
    assert (report_row_producer.request_min == min(client_requests))
    assert (report_row_producer.request_max == max(client_requests))
    assert (report_row_producer.request_avg == (sum(client_requests), number_of_clients))
    assert (report_row_producer.duration_min == min(client_durations))
    assert (report_row_producer.duration_max == max(client_durations))
    assert (report_row_producer.duration_avg == (sum(client_durations), number_of_clients))
    assert (report_row_producer.succeeded_queries == number_of_clients)
    # It is equal to number_of_clients because the "succeeded": None means it is False in the new_doc_none.
    assert (report_row_producer.failed_queries == number_of_clients)


def test_return_row_empty():
    report_row_producer = ReportRow(None)
    row = [0, 0, None, (None, None), None, None, (None, None), None, None, (None, None), None]
    assert (report_row_producer.return_row(), row)


def test_return_row_random(random_row):
    report_row_producer, client_requests, client_responses, number_of_clients, client_durations = random_row

    row = [
        number_of_clients,
        number_of_clients,
        min(client_durations),
        (sum(client_durations), number_of_clients),
        max(client_durations),
        min(client_requests),
        (sum(client_requests), number_of_clients),
        max(client_requests),
        min(client_responses),
        (sum(client_responses), number_of_clients),
        max(client_responses)
    ]

    assert (report_row_producer.return_row() == row)
