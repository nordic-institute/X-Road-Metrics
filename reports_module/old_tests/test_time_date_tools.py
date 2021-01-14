import datetime
import unittest

from ..reportslib import time_date_tools


# To run the tests:
# python -m reports_module.tests.test_time_date_tools


class TestTimingMethods(unittest.TestCase):
    def test_datetime_to_string_happy_path(self):
        self.assertEqual(time_date_tools.datetime_to_modified_string(datetime.datetime(2007, 12, 6, 15, 29, 43, 79060)),
                         "2007-12-06_15-29-43-79060")
        self.assertEqual(
            time_date_tools.datetime_to_modified_string(datetime.datetime(2007, 12, 6, 15, 00, 00, 999999)),
            "2007-12-06_15-0-0-999999")
        self.assertEqual(time_date_tools.datetime_to_modified_string(datetime.datetime(2007, 12, 6)),
                         "2007-12-06_0-0-0-0")

    def test_datetime_to_string_wrong_input(self):
        self.assertRaises(ValueError, time_date_tools.datetime_to_modified_string, "Wrong input")
        self.assertRaises(ValueError, time_date_tools.datetime_to_modified_string, 5)
        self.assertRaises(ValueError, time_date_tools.datetime_to_modified_string, [])
        self.assertRaises(ValueError, time_date_tools.datetime_to_modified_string, ("a", "b"))

    def test_string_to_date_happy_path(self):
        self.assertEqual(time_date_tools.string_to_date("2017-01-03"), datetime.date(2017, 1, 3))
        self.assertEqual(time_date_tools.string_to_date("2017-12-31"), datetime.date(2017, 12, 31))
        self.assertEqual(time_date_tools.string_to_date("2017-06-01"), datetime.date(2017, 6, 1))

    def test_string_to_date_wrong_input(self):
        self.assertRaises(ValueError, time_date_tools.string_to_date, "Wrong input")
        self.assertRaises(ValueError, time_date_tools.string_to_date, "999-01-01")
        self.assertRaises(ValueError, time_date_tools.string_to_date, "1000-0-1")
        self.assertRaises(ValueError, time_date_tools.string_to_date, "1000-1-0")
        self.assertRaises(ValueError, time_date_tools.string_to_date, "10000-1-1")
        self.assertRaises(ValueError, time_date_tools.string_to_date, "1000-13-1")
        self.assertRaises(ValueError, time_date_tools.string_to_date, "1000-1-32")
        self.assertRaises(ValueError, time_date_tools.string_to_date, datetime.date(2007, 12, 6))
        self.assertRaises(ValueError, time_date_tools.string_to_date, 1493931600)
        self.assertRaises(ValueError, time_date_tools.string_to_date, [])
        self.assertRaises(ValueError, time_date_tools.string_to_date, ("a", "b"))

    def test_date_to_timestamp_happy_path(self):
        self.assertEqual(time_date_tools.date_to_timestamp_milliseconds(datetime.date(2007, 12, 6)), 1196899200000)
        self.assertEqual(time_date_tools.date_to_timestamp_milliseconds(datetime.date(2007, 12, 6), False),
                         1196985600000)

    def test_date_to_timestamp_wrong_input(self):
        self.assertRaises(ValueError, time_date_tools.date_to_timestamp_milliseconds, "Wrong input")
        self.assertRaises(ValueError, time_date_tools.date_to_timestamp_milliseconds, 5)
        self.assertRaises(ValueError, time_date_tools.date_to_timestamp_milliseconds, [])
        self.assertRaises(ValueError, time_date_tools.date_to_timestamp_milliseconds, ("a", "b"))
        self.assertRaises(ValueError, time_date_tools.date_to_timestamp_milliseconds,
                          datetime.datetime(2007, 12, 6, 15, 29, 43, 79060))
        self.assertRaises(ValueError, time_date_tools.date_to_timestamp_milliseconds, "2017-05-01")

    def test_calculate_closing_date_happy_path(self):
        self.assertEqual(time_date_tools.calculate_closing_date(datetime.date(2007, 12, 16), 10),
                         datetime.date(2007, 12, 6))
        self.assertEqual(time_date_tools.calculate_closing_date(datetime.date(2017, 1, 1), 2),
                         datetime.date(2016, 12, 30))

    def test_calculate_closing_date_wrong_input(self):
        self.assertRaises(ValueError, time_date_tools.calculate_closing_date, 5, 1)
        self.assertRaises(ValueError, time_date_tools.calculate_closing_date, [], 5)
        self.assertRaises(ValueError, time_date_tools.calculate_closing_date, datetime.date(2007, 12, 16), "5")
        self.assertRaises(ValueError, time_date_tools.calculate_closing_date,
                          datetime.datetime(2007, 12, 6, 15, 29, 43, 79060), 3)
        self.assertRaises(ValueError, time_date_tools.calculate_closing_date, "2017-05-01", 2)

    def test_get_previous_month_last_day_happy_path(self):
        self.assertEqual(time_date_tools.get_previous_month_last_day(datetime.date(2007, 1, 31)),
                         datetime.date(2007, 1, 31))
        self.assertEqual(time_date_tools.get_previous_month_last_day(datetime.date(2017, 1, 30)),
                         datetime.date(2016, 12, 31))
        self.assertEqual(time_date_tools.get_previous_month_last_day(datetime.date(2017, 1, 1)),
                         datetime.date(2016, 12, 31))

    def test_get_previous_month_first_day_happy_path(self):
        self.assertEqual(time_date_tools.get_previous_month_first_day(datetime.date(2007, 1, 31)),
                         datetime.date(2007, 1, 1))
        self.assertEqual(time_date_tools.get_previous_month_first_day(datetime.date(2017, 1, 30)),
                         datetime.date(2016, 12, 1))
        self.assertEqual(time_date_tools.get_previous_month_first_day(datetime.date(2017, 1, 1)),
                         datetime.date(2016, 12, 1))

    def test_get_previous_month_start_and_end_date_happy_path(self):
        self.assertEqual(time_date_tools.get_previous_month_start_and_end_date(datetime.date(2007, 1, 31)),
                         (datetime.date(2007, 1, 1), datetime.date(2007, 1, 31)))
        self.assertEqual(time_date_tools.get_previous_month_start_and_end_date(datetime.date(2007, 1, 30)),
                         (datetime.date(2006, 12, 1), datetime.date(2006, 12, 31)))
        self.assertEqual(time_date_tools.get_previous_month_start_and_end_date(datetime.date(2007, 1, 1)),
                         (datetime.date(2006, 12, 1), datetime.date(2006, 12, 31)))

    def test_next_weekday_happy_path(self):
        self.assertEqual(time_date_tools.next_weekday(datetime.date(2017, 7, 10), 0), datetime.date(2017, 7, 10))
        self.assertEqual(time_date_tools.next_weekday(datetime.date(2017, 7, 11), 0), datetime.date(2017, 7, 17))
        self.assertEqual(time_date_tools.next_weekday(datetime.date(2017, 7, 9), 0), datetime.date(2017, 7, 10))

    def test_get_previous_week_last_day_happy_path(self):
        self.assertEqual(time_date_tools.get_previous_week_last_day(datetime.date(2017, 7, 10)),
                         datetime.date(2017, 7, 9))
        self.assertEqual(time_date_tools.get_previous_week_last_day(datetime.date(2017, 7, 9)),
                         datetime.date(2017, 7, 9))
        self.assertEqual(time_date_tools.get_previous_week_last_day(datetime.date(2017, 7, 8)),
                         datetime.date(2017, 7, 2))

    def test_get_previous_week_first_day_happy_path(self):
        self.assertEqual(time_date_tools.get_previous_week_first_day(datetime.date(2017, 7, 10)),
                         datetime.date(2017, 7, 3))
        self.assertEqual(time_date_tools.get_previous_week_first_day(datetime.date(2017, 7, 9)),
                         datetime.date(2017, 7, 3))
        self.assertEqual(time_date_tools.get_previous_week_first_day(datetime.date(2017, 7, 15)),
                         datetime.date(2017, 7, 3))

    def test_get_previous_week_start_end_dates_happy_path(self):
        self.assertEqual(time_date_tools.get_previous_week_start_end_dates(datetime.date(2017, 7, 10)),
                         (datetime.date(2017, 7, 3), datetime.date(2017, 7, 9)))
        self.assertEqual(time_date_tools.get_previous_week_start_end_dates(datetime.date(2017, 7, 15)),
                         (datetime.date(2017, 7, 3), datetime.date(2017, 7, 9)))
        self.assertEqual(time_date_tools.get_previous_week_start_end_dates(datetime.date(2017, 7, 9)),
                         (datetime.date(2017, 7, 3), datetime.date(2017, 7, 9)))

    def test_get_next_week_first_day_happy_path(self):
        self.assertEqual(time_date_tools.get_next_week_first_day(datetime.date(2017, 7, 10)),
                         datetime.date(2017, 7, 10))
        self.assertEqual(time_date_tools.get_next_week_first_day(datetime.date(2017, 7, 11)),
                         datetime.date(2017, 7, 17))
        self.assertEqual(time_date_tools.get_next_week_first_day(datetime.date(2017, 7, 9)),
                         datetime.date(2017, 7, 10))

    def test_get_next_week_last_day_happy_path(self):
        self.assertEqual(time_date_tools.get_next_week_last_day(datetime.date(2017, 7, 10)),
                         datetime.date(2017, 7, 16))
        self.assertEqual(time_date_tools.get_next_week_last_day(datetime.date(2017, 7, 11)),
                         datetime.date(2017, 7, 23))
        self.assertEqual(time_date_tools.get_next_week_last_day(datetime.date(2017, 7, 9)),
                         datetime.date(2017, 7, 16))

    def test_get_next_week_start_end_dates_happy_path(self):
        self.assertEqual(time_date_tools.get_next_week_start_end_dates(datetime.date(2017, 7, 10)),
                         (datetime.date(2017, 7, 10), datetime.date(2017, 7, 16)))
        self.assertEqual(time_date_tools.get_next_week_start_end_dates(datetime.date(2017, 7, 11)),
                         (datetime.date(2017, 7, 17), datetime.date(2017, 7, 23)))
        self.assertEqual(time_date_tools.get_next_week_start_end_dates(datetime.date(2017, 7, 9)),
                         (datetime.date(2017, 7, 10), datetime.date(2017, 7, 16)))


if __name__ == '__main__':
    unittest.main()
