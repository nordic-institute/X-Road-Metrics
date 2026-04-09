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

import unittest
from datetime import datetime, timezone

from opmon_anonymizer.transformers.default import (
    reduce_request_in_ts_precision,
    force_durations_to_integer_range
)
from opmon_anonymizer.transformers import get_enabled_transformers


class TestReduceRequestInTsPrecision(unittest.TestCase):

    def test_removes_minutes_and_seconds_from_timestamp(self):
        """Timestamp with minutes and seconds should be rounded down to hour."""
        # 2022-06-15 16:35:47.500 (milliseconds)
        timestamp_ms = 1655310947500
        record = {'requestInTs': timestamp_ms}

        result = reduce_request_in_ts_precision(record)

        # Should round to 2022-06-15 14:00:00.000
        expected_timestamp_ms = int(datetime(2022, 6, 15, 16, 0, 0, tzinfo=timezone.utc).timestamp()) * 1000
        self.assertEqual(result['requestInTs'], expected_timestamp_ms)

    def test_preserves_exact_hour_boundary(self):
        """Timestamp already at hour boundary should remain unchanged."""
        # 2022-06-15 14:00:00.000
        timestamp_ms = int(datetime(2022, 6, 15, 14, 0, 0, tzinfo=timezone.utc).timestamp()) * 1000
        record = {'requestInTs': timestamp_ms}

        result = reduce_request_in_ts_precision(record)

        self.assertEqual(result['requestInTs'], timestamp_ms)

    def test_rounds_down_near_hour_end(self):
        """Timestamp near end of hour should round down to hour start."""
        # 2022-06-15 14:59:59.999
        timestamp_ms = int(datetime(2022, 6, 15, 14, 59, 59, tzinfo=timezone.utc).timestamp()) * 1000 + 999
        record = {'requestInTs': timestamp_ms}

        result = reduce_request_in_ts_precision(record)

        # Should round to 2022-06-15 14:00:00.000
        expected_timestamp_ms = int(datetime(2022, 6, 15, 14, 0, 0, tzinfo=timezone.utc).timestamp()) * 1000
        self.assertEqual(result['requestInTs'], expected_timestamp_ms)

    def test_handles_year_boundary(self):
        """Timestamp near year boundary should round correctly."""
        # 2021-12-31 23:30:45.000 should round to 2021-12-31 23:00:00
        timestamp_ms = int(datetime(2021, 12, 31, 23, 30, 45, tzinfo=timezone.utc).timestamp()) * 1000
        record = {'requestInTs': timestamp_ms}

        result = reduce_request_in_ts_precision(record)

        expected_timestamp_ms = int(datetime(2021, 12, 31, 23, 0, 0, tzinfo=timezone.utc).timestamp()) * 1000
        self.assertEqual(result['requestInTs'], expected_timestamp_ms)

    def test_returns_modified_record(self):
        """Transformer should return the modified record object."""
        record = {'requestInTs': 1655310947500}

        result = reduce_request_in_ts_precision(record)

        self.assertIs(result, record)

    def test_preserves_other_fields_in_record(self):
        """Transformer should not modify other fields in the record."""
        record = {
            'requestInTs': 1655310947500,
            'field1': 'value1',
            'field2': 12345,
            'field3': {'nested': 'value'}
        }

        result = reduce_request_in_ts_precision(record)

        self.assertEqual(result['field1'], 'value1')
        self.assertEqual(result['field2'], 12345)
        self.assertEqual(result['field3'], {'nested': 'value'})

    def test_raises_key_error_when_requestInTs_missing(self):
        """Should raise KeyError if requestInTs field is missing from record."""
        record = {'field1': 'value1', 'field2': 12345}

        with self.assertRaises(KeyError):
            reduce_request_in_ts_precision(record)


class TestForceDurationsToIntegerRange(unittest.TestCase):

    MAX_INT32 = 2**31 - 1
    MIN_INT32 = -(2**31 - 1)

    def test_clamps_large_positive_total_duration(self):
        """Large positive totalDuration should be clamped to max int32."""
        record = {
            'totalDuration': 2**32,  # Much larger than int32 max
            'producerDurationProducerView': 0
        }

        result = force_durations_to_integer_range(record)

        self.assertEqual(result['totalDuration'], self.MAX_INT32)

    def test_clamps_large_negative_total_duration(self):
        """Large negative totalDuration should be clamped to min int32."""
        record = {
            'totalDuration': -(2**32),
            'producerDurationProducerView': 0
        }

        result = force_durations_to_integer_range(record)

        self.assertEqual(result['totalDuration'], self.MIN_INT32)

    def test_clamps_large_positive_producer_duration(self):
        """Large positive producerDurationProducerView should be clamped to max int32."""
        record = {
            'totalDuration': 0,
            'producerDurationProducerView': 2**32
        }

        result = force_durations_to_integer_range(record)

        self.assertEqual(result['producerDurationProducerView'], self.MAX_INT32)

    def test_clamps_large_negative_producer_duration(self):
        """Large negative producerDurationProducerView should be clamped to min int32."""
        record = {
            'totalDuration': 0,
            'producerDurationProducerView': -(2**32)
        }

        result = force_durations_to_integer_range(record)

        self.assertEqual(result['producerDurationProducerView'], self.MIN_INT32)

    def test_preserves_small_positive_durations(self):
        """Small positive durations within int32 range should remain unchanged."""
        record = {
            'totalDuration': 1000,
            'producerDurationProducerView': 500
        }

        result = force_durations_to_integer_range(record)

        self.assertEqual(result['totalDuration'], 1000)
        self.assertEqual(result['producerDurationProducerView'], 500)

    def test_preserves_small_negative_durations(self):
        """Small negative durations within int32 range should remain unchanged."""
        record = {
            'totalDuration': -1000,
            'producerDurationProducerView': -500
        }

        result = force_durations_to_integer_range(record)

        self.assertEqual(result['totalDuration'], -1000)
        self.assertEqual(result['producerDurationProducerView'], -500)

    def test_handles_zero_total_duration(self):
        """Zero totalDuration should not be modified (falsy value skipped by if)."""
        record = {
            'totalDuration': 0,
            'producerDurationProducerView': 500
        }

        result = force_durations_to_integer_range(record)

        self.assertEqual(result['totalDuration'], 0)
        self.assertEqual(result['producerDurationProducerView'], 500)

    def test_handles_zero_producer_duration(self):
        """Zero producerDurationProducerView should not be modified (falsy value skipped by if)."""
        record = {
            'totalDuration': 500,
            'producerDurationProducerView': 0
        }

        result = force_durations_to_integer_range(record)

        self.assertEqual(result['totalDuration'], 500)
        self.assertEqual(result['producerDurationProducerView'], 0)

    def test_handles_none_total_duration(self):
        """None totalDuration should not be modified (falsy value skipped by if)."""
        record = {
            'totalDuration': None,
            'producerDurationProducerView': 500
        }

        result = force_durations_to_integer_range(record)

        self.assertIsNone(result['totalDuration'])
        self.assertEqual(result['producerDurationProducerView'], 500)

    def test_handles_none_producer_duration(self):
        """None producerDurationProducerView should not be modified (falsy value skipped by if)."""
        record = {
            'totalDuration': 500,
            'producerDurationProducerView': None
        }

        result = force_durations_to_integer_range(record)

        self.assertEqual(result['totalDuration'], 500)
        self.assertIsNone(result['producerDurationProducerView'])

    def test_both_durations_exceed_max_int32(self):
        """Both durations exceeding max int32 should both be clamped."""
        record = {
            'totalDuration': 2**32,
            'producerDurationProducerView': 2**32
        }

        result = force_durations_to_integer_range(record)

        self.assertEqual(result['totalDuration'], self.MAX_INT32)
        self.assertEqual(result['producerDurationProducerView'], self.MAX_INT32)

    def test_both_durations_exceed_min_int32(self):
        """Both durations exceeding min int32 should both be clamped."""
        record = {
            'totalDuration': -(2**32),
            'producerDurationProducerView': -(2**32)
        }

        result = force_durations_to_integer_range(record)

        self.assertEqual(result['totalDuration'], self.MIN_INT32)
        self.assertEqual(result['producerDurationProducerView'], self.MIN_INT32)

    def test_at_max_int32_boundary(self):
        """Duration exactly at max int32 should not be modified."""
        record = {
            'totalDuration': self.MAX_INT32,
            'producerDurationProducerView': self.MAX_INT32
        }

        result = force_durations_to_integer_range(record)

        self.assertEqual(result['totalDuration'], self.MAX_INT32)
        self.assertEqual(result['producerDurationProducerView'], self.MAX_INT32)

    def test_at_min_int32_boundary(self):
        """Duration exactly at min int32 should not be modified."""
        record = {
            'totalDuration': self.MIN_INT32,
            'producerDurationProducerView': self.MIN_INT32
        }

        result = force_durations_to_integer_range(record)

        self.assertEqual(result['totalDuration'], self.MIN_INT32)
        self.assertEqual(result['producerDurationProducerView'], self.MIN_INT32)

    def test_just_above_max_int32(self):
        """Duration just above max int32 should be clamped."""
        record = {
            'totalDuration': self.MAX_INT32 + 1,
            'producerDurationProducerView': 0
        }

        result = force_durations_to_integer_range(record)

        self.assertEqual(result['totalDuration'], self.MAX_INT32)

    def test_just_below_min_int32(self):
        """Duration just below min int32 should be clamped."""
        record = {
            'totalDuration': self.MIN_INT32 - 1,
            'producerDurationProducerView': 0
        }

        result = force_durations_to_integer_range(record)

        self.assertEqual(result['totalDuration'], self.MIN_INT32)

    def test_returns_modified_record(self):
        """Transformer should return the same record object."""
        record = {
            'totalDuration': 100,
            'producerDurationProducerView': 50
        }

        result = force_durations_to_integer_range(record)

        self.assertIs(result, record)

    def test_preserves_other_fields_in_record(self):
        """Transformer should not modify other fields in the record."""
        record = {
            'totalDuration': 100,
            'producerDurationProducerView': 50,
            'field1': 'value1',
            'field2': 12345,
            'field3': {'nested': 'value'}
        }

        result = force_durations_to_integer_range(record)

        self.assertEqual(result['field1'], 'value1')
        self.assertEqual(result['field2'], 12345)
        self.assertEqual(result['field3'], {'nested': 'value'})

    def test_raises_key_error_when_totalDuration_missing(self):
        """Should raise KeyError if totalDuration field is missing from record."""
        record = {'producerDurationProducerView': 50, 'field1': 'value1'}

        with self.assertRaises(KeyError):
            force_durations_to_integer_range(record)

    def test_raises_key_error_when_producerDurationProducerView_missing(self):
        """Should raise KeyError if producerDurationProducerView field is missing."""
        record = {'totalDuration': 100, 'field1': 'value1'}

        with self.assertRaises(KeyError):
            force_durations_to_integer_range(record)


class TestGetEnabledTransformers(unittest.TestCase):

    def test_returns_empty_list_when_all_disabled(self):
        """When all transformers are disabled, should return empty list."""
        settings = {
            'reduce-request-in-ts-precision': False,
            'force-durations-to-integer-range': False
        }

        transformers = get_enabled_transformers(settings)

        self.assertEqual(transformers, [])
        self.assertIsInstance(transformers, list)

    def test_returns_reduce_request_in_ts_precision_only(self):
        """When only reduce-request-in-ts-precision is enabled."""
        settings = {
            'reduce-request-in-ts-precision': True,
            'force-durations-to-integer-range': False
        }

        transformers = get_enabled_transformers(settings)

        self.assertEqual(len(transformers), 1)
        self.assertIs(transformers[0], reduce_request_in_ts_precision)

    def test_returns_force_durations_to_integer_range_only(self):
        """When only force-durations-to-integer-range is enabled."""
        settings = {
            'reduce-request-in-ts-precision': False,
            'force-durations-to-integer-range': True
        }

        transformers = get_enabled_transformers(settings)

        self.assertEqual(len(transformers), 1)
        self.assertIs(transformers[0], force_durations_to_integer_range)

    def test_returns_both_transformers_when_both_enabled(self):
        """When both transformers are enabled, should return both in correct order."""
        settings = {
            'reduce-request-in-ts-precision': True,
            'force-durations-to-integer-range': True
        }

        transformers = get_enabled_transformers(settings)

        self.assertEqual(len(transformers), 2)
        self.assertIs(transformers[0], reduce_request_in_ts_precision)
        self.assertIs(transformers[1], force_durations_to_integer_range)

    def test_order_of_transformers_is_preserved(self):
        """Transformers should be returned in consistent order regardless of setting values."""
        settings = {
            'reduce-request-in-ts-precision': True,
            'force-durations-to-integer-range': True
        }

        transformers1 = get_enabled_transformers(settings)
        transformers2 = get_enabled_transformers(settings)

        self.assertEqual(transformers1, transformers2)

    def test_handles_missing_settings_gracefully(self):
        """Should raise KeyError when required settings are missing."""
        settings = {'reduce-request-in-ts-precision': True}

        with self.assertRaises(KeyError):
            get_enabled_transformers(settings)

    def test_handles_none_boolean_values(self):
        """Should treat None as False for transformer settings."""
        settings = {
            'reduce-request-in-ts-precision': None,
            'force-durations-to-integer-range': False
        }

        transformers = get_enabled_transformers(settings)

        self.assertEqual(transformers, [])

    def test_handles_truthy_non_boolean_values(self):
        """Should treat truthy values (not just True) as enabled."""
        settings = {
            'reduce-request-in-ts-precision': 1,  # Truthy but not bool
            'force-durations-to-integer-range': 'yes'  # Truthy but not bool
        }

        transformers = get_enabled_transformers(settings)

        self.assertEqual(len(transformers), 2)
        self.assertIs(transformers[0], reduce_request_in_ts_precision)
        self.assertIs(transformers[1], force_durations_to_integer_range)

    def test_transformers_are_callable(self):
        """All returned transformers should be callable."""
        settings = {
            'reduce-request-in-ts-precision': True,
            'force-durations-to-integer-range': True
        }

        transformers = get_enabled_transformers(settings)

        for transformer in transformers:
            self.assertTrue(callable(transformer))

    def test_returns_new_list_each_time(self):
        """Should return a new list instance each time (not a cached reference)."""
        settings = {
            'reduce-request-in-ts-precision': True,
            'force-durations-to-integer-range': False
        }

        transformers1 = get_enabled_transformers(settings)
        transformers2 = get_enabled_transformers(settings)

        self.assertIsNot(transformers1, transformers2)
        self.assertEqual(transformers1, transformers2)


if __name__ == '__main__':
    unittest.main()
