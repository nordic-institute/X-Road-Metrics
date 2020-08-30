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
