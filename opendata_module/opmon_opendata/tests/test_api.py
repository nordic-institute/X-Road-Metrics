import datetime
import json

import pytest
import pytz
from freezegun import freeze_time

from .test_utils import (COLUMNS, TEST_SETTINGS, db, http_client, log_factory,
                         make_m_statistics, mock_logger_manager, mock_settings)


def test_get_harvest_empty_response(db, http_client):
    data = {
        'from_dt': '2022-11-07T08:00:00+0000',
    }
    response = http_client.get('/api/harvest', data)
    assert response.status_code == 200
    assert response.json() == {
        'data': [],
        'columns': [],
        'total_query_count': 0,
        'timestamp_tz_offset': '+0000',
        'limit': 0,
        'row_range': '0-0',
    }


def test_get_harvest_from_tz_negative_offset(db, http_client):
    data = {
        'from_dt': '2022-11-07T08:00:00-0500',
    }
    response = http_client.get('/api/harvest', data)
    assert response.status_code == 200


def test_get_harvest_from(db, http_client, caplog):
    now = datetime.datetime.now()

    log_factory(db, request_in_dt='2022-11-07T07:50:00')

    # happy logs
    log_factory(db, request_in_dt='2022-11-07T08:00:00')
    log_factory(db, request_in_dt=now)

    data = {
        'from_dt': '2022-11-07T08:00:00+0000',
    }
    response = http_client.get('/api/harvest', data)
    assert response.status_code == 200
    response_data = response.json()
    data = response_data.get('data')
    assert response_data['timestamp_tz_offset'] == '+0000'
    assert len(data) == 2
    assert 'api_get_harvest_response_success' in caplog.text
    assert 'returning 2 rows' in caplog.text
    assert response_data['row_range'] == '1-2'


def test_get_harvest_from_row_id(db, http_client):
    log_factory(db, request_in_dt='2022-11-07T07:50:00', id=1)
    log_factory(db, request_in_dt='2022-11-07T08:00:00', id=2)

    # happy logs
    log_factory(db, request_in_dt='2022-11-07T09:00:00', id=3)
    log_factory(db, request_in_dt='2022-11-07T10:00:00', id=4)
    log_factory(db, request_in_dt='2022-11-07T11:00:00', id=5)

    data = {
        'from_dt': '2022-11-07T07:00:00+0000',
        'from_row_id': 2,
    }
    response = http_client.get('/api/harvest', data)
    assert response.status_code == 200
    response_data = response.json()
    data = response_data.get('data')
    assert len(data) == 3
    assert response_data['row_range'] == '1-3'


@pytest.mark.parametrize('from_dt', [
    ('2022-11-07T09:00:00+0200'),
    ('2022-11-07T09:00:00 0200')
])
def test_get_harvest_timestamp_tz(db, http_client, from_dt):
    tzinfo = pytz.timezone('Europe/Helsinki')
    log_factory(db, request_in_dt=datetime.datetime(2022, 11, 7, 7, tzinfo=tzinfo))
    log_factory(db, request_in_dt=datetime.datetime(2022, 11, 7, 8, tzinfo=tzinfo))

    # happy logs
    log_factory(db, request_in_dt=datetime.datetime(2022, 11, 7, 9, tzinfo=tzinfo))
    log_factory(db, request_in_dt=datetime.datetime(2022, 11, 7, 10, tzinfo=tzinfo))
    log_factory(db, request_in_dt=datetime.datetime(2022, 11, 7, 11, tzinfo=tzinfo))

    data = {
        'from_dt': from_dt,
    }
    response = http_client.get('/api/harvest', data)
    assert response.status_code == 200
    response_data = response.json()
    data = response_data.get('data')
    actual_request_in_dates = [row[10] for row in data]
    assert actual_request_in_dates == ['1667805600000', '1667809200000', '1667812800000']
    assert response_data['timestamp_tz_offset'] == '+0200'


@pytest.mark.parametrize('from_dt,expected_columns, has_data', [
    ('2011-11-07T08:00:00+0000', COLUMNS, True),
    ('2023-01-07T08:00:00+0000', [], False)
])
def test_get_harvest_columns(db, http_client, from_dt, expected_columns, has_data):
    # Do not return columns for empty data
    log_factory(db, request_in_dt='2022-11-07T08:00:00')
    data = {
        'from_dt': from_dt,
    }
    response = http_client.get('/api/harvest', data)
    assert response.status_code == 200
    response_data = response.json()
    assert bool(response_data['data']) == has_data
    assert response_data['columns'] == expected_columns


def test_get_harvest_from_until(db, http_client):
    log_factory(db, request_in_dt='2022-11-07T07:50:00')

    # happy logs
    log_factory(db, request_in_dt='2022-11-07T08:00:00')
    log_factory(db, request_in_dt='2022-11-07T08:20:00')
    log_factory(db, request_in_dt='2022-11-07T08:47:00')

    log_factory(db, request_in_dt='2022-11-07T09:00:00')
    log_factory(db, request_in_dt='2022-11-07T09:15:00')

    query = {
        'from_dt': '2022-11-07T08:00:00+0000',
        'until_dt': '2022-11-07T09:00:00+0000',
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 200
    response_data = response.json()
    data = response_data.get('data')
    assert response_data['row_range'] == '1-3'
    assert len(data) == 3


def test_get_harvest_from_with_limit(db, http_client):
    log_factory(db, request_in_dt='2022-11-10T08:00:00')
    log_factory(db, request_in_dt='2022-11-08T08:20:00')
    log_factory(db, request_in_dt='2022-11-05T08:47:00')
    log_factory(db, request_in_dt='2022-11-09T09:30:00')
    log_factory(db, request_in_dt='2022-11-07T10:34:00')

    query = {
        'from_dt': '2022-11-05T08:00:00+0000',
        'limit': 4
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 200
    response_data = response.json()
    data = response_data.get('data')
    assert len(data) == 4
    actual_request_in_dates = [row[11] for row in data]
    assert actual_request_in_dates == [
        '2022-11-05',
        '2022-11-07',
        '2022-11-08',
        '2022-11-09'
    ]
    assert response_data['limit'] == 4
    assert response_data['row_range'] == '1-4'


def test_get_harvest_rows_less_than_limit(db, http_client):
    log_factory(db, request_in_dt='2022-11-07T10:34:00')
    log_factory(db, request_in_dt='2022-11-08T08:00:00')

    query = {
        'from_dt': '2022-11-05T08:00:00+0000',
        'limit': 100
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 200
    response_data = response.json()
    data = response_data.get('data')
    assert len(data) == 2
    actual_request_in_dates = [row[11] for row in data]
    assert actual_request_in_dates == [
        '2022-11-07',
        '2022-11-08',
    ]
    assert response_data['limit'] == 100
    assert response_data['row_range'] == '1-2'


def test_get_harvest_total_query_count(db, http_client):
    log_factory(db, request_in_dt='2022-11-10T08:00:00')
    log_factory(db, request_in_dt='2022-11-08T08:20:00')
    log_factory(db, request_in_dt='2022-11-05T08:47:00')
    log_factory(db, request_in_dt='2022-11-09T09:30:00')
    log_factory(db, request_in_dt='2022-11-07T10:34:00')

    query = {
        'from_dt': '2022-11-05T08:00:00+0000',
        'limit': 1
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['total_query_count'] == 5
    assert response_data['row_range'] == '1-1'


def test_get_harvest_from_with_limit_offset(db, http_client):
    log_factory(db, request_in_dt='2022-11-10T08:00:00')
    log_factory(db, request_in_dt='2022-11-08T08:20:00')
    log_factory(db, request_in_dt='2022-11-05T08:47:00')
    log_factory(db, request_in_dt='2022-11-09T09:30:00')
    log_factory(db, request_in_dt='2022-11-07T10:34:00')

    query = {
        'from_dt': '2022-11-05T07:00:00+0000',
        'limit': 4,
        'offset': 2
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 200
    response_data = response.json()
    data = response_data.get('data')
    assert len(data) == 3
    actual_request_in_dates = [row[11] for row in data]
    assert actual_request_in_dates == [
        '2022-11-08',
        '2022-11-09',
        '2022-11-10'
    ]
    assert response_data['row_range'] == '3-6'


def test_get_harvest_default_ordering(db, http_client):
    log_factory(db, request_in_dt='2022-11-15T10:34:00')
    log_factory(db, request_in_dt='2022-11-12T08:00:00')
    log_factory(db, request_in_dt='2022-11-07T09:30:00')
    log_factory(db, request_in_dt='2022-11-14T08:47:00')
    log_factory(db, request_in_dt='2022-11-13T08:20:00')

    query = {
        'from_dt': '2022-11-07T07:00:00+0000',
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 200
    response_data = response.json()
    data = response_data.get('data')
    assert len(data) == 5
    actual_request_in_dates = [row[11] for row in data]
    assert response_data['row_range'] == '1-5'
    assert actual_request_in_dates == [
        '2022-11-07',
        '2022-11-12',
        '2022-11-13',
        '2022-11-14',
        '2022-11-15'
    ]


@pytest.mark.parametrize('ordering,expected_rows', [
    ('ASC', [
        ('2022-11-15', '5'),
        ('2022-11-12', '25'),
        ('2022-11-07', '60'),
        ('2022-11-14', '100'),
        ('2022-11-13', '300')
    ]),
    ('DESC', [
        ('2022-11-13', '300'),
        ('2022-11-14', '100'),
        ('2022-11-07', '60'),
        ('2022-11-12', '25'),
        ('2022-11-15', '5'),
    ])
])
def test_get_harvest_ordering_requestinsize(db, http_client, ordering, expected_rows):
    log_factory(db, request_in_dt='2022-11-14T08:47:00', requestsize=100)
    log_factory(db, request_in_dt='2022-11-15T10:34:00', requestsize=5)
    log_factory(db, request_in_dt='2022-11-07T09:30:00', requestsize=60)
    log_factory(db, request_in_dt='2022-11-13T08:20:00', requestsize=300)
    log_factory(db, request_in_dt='2022-11-12T08:00:00', requestsize=25)

    query = {
        'from_dt': '2022-11-07T07:00:00+0000',
        'order': json.dumps({
            'column': 'requestsize',
            'order': ordering,
        })
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 200
    response_data = response.json()
    data = response_data.get('data')
    assert len(data) == 5
    actual_dates_request_sizes = [(row[11], row[14]) for row in data]
    assert actual_dates_request_sizes == expected_rows
    assert response_data['row_range'] == '1-5'


def test_get_harvest_error_missing_from_dt(http_client, caplog):
    query = {}
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 400
    response_data = response.json()
    assert response_data['errors'] == {
        'from_dt': ['This field is required.']
    }
    assert 'api_get_harvest_input_validation_failed' in caplog.text
    assert 'from_dt: This field is required' in caplog.text


@freeze_time('2022-12-10')
def test_get_harvest_error_from_dt_later_now(http_client):
    query = {
        'from_dt': '2022-12-11T07:00:00+0000',
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 400
    response_data = response.json()
    assert response_data['errors'] == {
        'from_dt': ['Ensure the value is not later than the current date and time']
    }


def test_get_harvest_error_from_dt_format(http_client):
    query = {
        'from_dt': '2022-12-11T07:00:00'
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 400
    response_data = response.json()
    assert response_data['errors'] == {
        'from_dt': ['Ensure the value matches format %Y-%m-%dT%H:%M:%S%z']
    }


def test_get_harvest_error_from_dt_later_until_dt(http_client):
    query = {
        'from_dt': '2022-12-13T07:00:00+0000',
        'until_dt': '2022-12-11T07:00:00+0000',
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 400
    response_data = response.json()
    assert response_data['errors'] == {
        'from_dt': ['Ensure the value is not later than until_dt'],
        'until_dt': ['Ensure the value is not earlier than from_dt']
    }


def test_get_harvest_error_invalid_json(http_client):
    query = {
        'from_dt': '2022-12-13T07:00:00+0000',
        'order': 'not valid'
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 400
    response_data = response.json()
    assert response_data['errors'] == {
        'order': ['Ensure "order" is valid json']
    }


def test_get_harvest_error_order_keys(http_client):
    query = {
        'from_dt': '2022-12-13T07:00:00+0000',
        'order': json.dumps({
            'column': 'requestsize',
            'notvalid': 'ASC',
        })
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 400
    response_data = response.json()
    assert response_data['errors'] == {
        'order': ['Ensure only "column" and "order" are set as keys']
    }


def test_get_harvest_error_order_order_values(http_client):
    query = {
        'from_dt': '2022-12-13T07:00:00+0000',
        'order': json.dumps({
            'column': 'requestsize',
            'order': 'asce',
        })
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 400
    response_data = response.json()
    assert response_data['errors'] == {
        'order': ['Ensure only "ASC" or "DESC" is set for order']
    }


def test_get_harvest_db_connection_error(http_client, caplog):
    # test failed connection to db handled successfully
    query = {
        'from_dt': '2022-12-13T07:00:00+0000',
    }
    response = http_client.get('/api/harvest', query)
    assert response.status_code == 500
    response_data = response.json()
    assert response_data['error'] == 'Server encountered error when getting harvest data.'
    assert 'api_get_harvest_query_failed' in caplog.text


def test_get_harvest_error_unsupported_method(http_client):
    query = {
        'from_dt': '2022-12-13T07:00:00+0000',
    }
    response = http_client.post('/api/harvest', query)
    assert response.status_code == 405
    response_data = response.json()
    assert response_data['error'] == 'The requested method is not allowed for the requested resource'


@freeze_time('2022-12-10')
def test_get_statistics_data_success(db, http_client, caplog):
    make_m_statistics(db, **{
        'current_month_request_count': 3742,
        'current_year_request_count': 4648,
        'previous_month_request_count': 872,
        'previous_year_request_count': 0,
        'today_request_count': 0,
        'total_request_count': 4648,
    })
    response = http_client.get('/api/statistics')
    assert response.status_code == 200
    assert response.json() == {
        'current_month_request_count': 3742,
        'current_year_request_count': 4648,
        'previous_month_request_count': 872,
        'previous_year_request_count': 0,
        'today_request_count': 0,
        'total_request_count': 4648,
        'update_time': '2022-12-10T00:00:00'
    }
    assert 'Statistics data fetched successfully' in caplog.text


def test_get_statistics_data_error_not_found(db, http_client, caplog):
    response = http_client.get('/api/statistics')
    assert response.status_code == 404
    assert response.json() == {'error': 'Statistics data was not found!'}
    assert 'Metrics statistics data was not found in database' in caplog.text


def test_get_statistics_data_error_server_failed(http_client, mocker, caplog):
    mocker.patch(
        'opmon_opendata.api.postgresql_manager.PostgreSQL_StatisticsManager.get_latest_metrics_statistics',
        side_effect=KeyError('test')
    )
    response = http_client.get('/api/statistics')
    assert response.status_code == 500
    assert response.json() == {'error': 'Server encountered error while getting statistics data'}
    assert 'KeyError' in caplog.text


def test_get_settings(http_client, caplog):
    response = http_client.get('/api/settings')
    assert response.status_code == 200
    assert response.json() == {
        'settings_profile': '',
        'maintenance_mode': TEST_SETTINGS['opendata']['maintenance-mode'],
        'x_road_instance': TEST_SETTINGS['xroad']['instance'],
        'header': TEST_SETTINGS['opendata']['header'],
        'footer': TEST_SETTINGS['opendata']['footer']
    }
    assert 'returning 5 settings' in caplog.text


def test_get_constraints(db, http_client, caplog):
    log_factory(db, request_in_dt='2021-11-07T07:50:00')
    log_factory(db, request_in_dt='2021-11-08T07:50:00')
    log_factory(db, request_in_dt='2021-11-10T07:50:00')
    log_factory(db, request_in_dt='2021-11-11T07:50:00')
    response = http_client.get('/api/constraints')
    assert response.status_code == 200
    assert response.json() == {
        'column_data': [
            {
                'name': 'field1',
                'description': 'test description',
                'type': 'string',
                'valid_operators': ['=', '!=']
            }
        ],
        'column_count': 1,
        # 2021-11-07 - delay-days
        'min_date': '2021-11-06',
        # 2021-11-11 - delay-days
        'max_date': '2021-11-10'
    }
    assert 'returning 1 columns' in caplog.text
