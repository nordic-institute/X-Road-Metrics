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
import pytest
import datetime
from opmon_reports import time_date_tools


def test_datetime_to_string_happy_path():
    date_string = time_date_tools.datetime_to_modified_string(datetime.datetime(2007, 12, 6, 15, 29, 43, 79060))
    assert date_string == "2007-12-06_15-29-43-79060"

    date_string = time_date_tools.datetime_to_modified_string(datetime.datetime(2007, 12, 6, 15, 00, 00, 999999))
    assert date_string == "2007-12-06_15-0-0-999999"

    date_string = time_date_tools.datetime_to_modified_string(datetime.datetime(2007, 12, 6))
    assert date_string == "2007-12-06_0-0-0-0"


def test_datetime_to_string_wrong_input():
    pytest.raises(ValueError, time_date_tools.datetime_to_modified_string, "Wrong input")
    pytest.raises(ValueError, time_date_tools.datetime_to_modified_string, 5)
    pytest.raises(ValueError, time_date_tools.datetime_to_modified_string, [])
    pytest.raises(ValueError, time_date_tools.datetime_to_modified_string, ("a", "b"))


def test_string_to_date_happy_path():
    assert (time_date_tools.string_to_date("2017-01-03") == datetime.date(2017, 1, 3))
    assert (time_date_tools.string_to_date("2017-12-31") == datetime.date(2017, 12, 31))
    assert (time_date_tools.string_to_date("2017-06-01") == datetime.date(2017, 6, 1))


def test_string_to_date_wrong_input():
    pytest.raises(ValueError, time_date_tools.string_to_date, "Wrong input")
    pytest.raises(ValueError, time_date_tools.string_to_date, "999-01-01")
    pytest.raises(ValueError, time_date_tools.string_to_date, "1000-0-1")
    pytest.raises(ValueError, time_date_tools.string_to_date, "1000-1-0")
    pytest.raises(ValueError, time_date_tools.string_to_date, "10000-1-1")
    pytest.raises(ValueError, time_date_tools.string_to_date, "1000-13-1")
    pytest.raises(ValueError, time_date_tools.string_to_date, "1000-1-32")
    pytest.raises(ValueError, time_date_tools.string_to_date, datetime.date(2007, 12, 6))
    pytest.raises(ValueError, time_date_tools.string_to_date, 1493931600)
    pytest.raises(ValueError, time_date_tools.string_to_date, [])
    pytest.raises(ValueError, time_date_tools.string_to_date, ("a", "b"))


def test_date_to_timestamp_happy_path():
    assert time_date_tools.date_to_timestamp_milliseconds(datetime.date(2007, 12, 6)) == 1196899200000
    assert time_date_tools.date_to_timestamp_milliseconds(datetime.date(2007, 12, 6), False) == 1196985600000


def test_date_to_timestamp_wrong_input():
    pytest.raises(ValueError, time_date_tools.date_to_timestamp_milliseconds, "Wrong input")
    pytest.raises(ValueError, time_date_tools.date_to_timestamp_milliseconds, 5)
    pytest.raises(ValueError, time_date_tools.date_to_timestamp_milliseconds, [])
    pytest.raises(ValueError, time_date_tools.date_to_timestamp_milliseconds, ("a", "b"))
    pytest.raises(ValueError, time_date_tools.date_to_timestamp_milliseconds, "2017-05-01")
    pytest.raises(ValueError, time_date_tools.date_to_timestamp_milliseconds,
                  datetime.datetime(2007, 12, 6, 15, 29, 43, 79060))


def test_calculate_closing_date_happy_path():
    assert (time_date_tools.calculate_closing_date(datetime.date(2007, 12, 16), 10) == datetime.date(2007, 12, 6))
    assert (time_date_tools.calculate_closing_date(datetime.date(2017, 1, 1), 2) == datetime.date(2016, 12, 30))


def test_calculate_closing_date_wrong_input():
    pytest.raises(ValueError, time_date_tools.calculate_closing_date, 5, 1)
    pytest.raises(ValueError, time_date_tools.calculate_closing_date, [], 5)
    pytest.raises(ValueError, time_date_tools.calculate_closing_date, datetime.date(2007, 12, 16), "5")
    pytest.raises(ValueError, time_date_tools.calculate_closing_date,
                  datetime.datetime(2007, 12, 6, 15, 29, 43, 79060), 3)
    pytest.raises(ValueError, time_date_tools.calculate_closing_date, "2017-05-01", 2)


def test_get_previous_month_last_day_happy_path():
    assert (time_date_tools.get_previous_month_last_day(datetime.date(2007, 1, 31)) == datetime.date(2007, 1, 31))
    assert (time_date_tools.get_previous_month_last_day(datetime.date(2017, 1, 30)) == datetime.date(2016, 12, 31))
    assert (time_date_tools.get_previous_month_last_day(datetime.date(2017, 1, 1)) == datetime.date(2016, 12, 31))


def test_get_previous_month_first_day_happy_path():
    assert (time_date_tools.get_previous_month_first_day(datetime.date(2007, 1, 31)) == datetime.date(2007, 1, 1))
    assert (time_date_tools.get_previous_month_first_day(datetime.date(2017, 1, 30)) == datetime.date(2016, 12, 1))
    assert (time_date_tools.get_previous_month_first_day(datetime.date(2017, 1, 1)) == datetime.date(2016, 12, 1))


def test_get_previous_month_start_and_end_date_happy_path():
    dates = time_date_tools.get_previous_month_start_and_end_date(datetime.date(2007, 1, 31))
    assert dates == (datetime.date(2007, 1, 1), datetime.date(2007, 1, 31))

    dates = time_date_tools.get_previous_month_start_and_end_date(datetime.date(2007, 1, 30))
    assert dates == (datetime.date(2006, 12, 1), datetime.date(2006, 12, 31))

    dates = time_date_tools.get_previous_month_start_and_end_date(datetime.date(2007, 1, 1))
    assert dates == (datetime.date(2006, 12, 1), datetime.date(2006, 12, 31))


def test_next_weekday_happy_path():
    assert time_date_tools.next_weekday(datetime.date(2017, 7, 10), 0) == datetime.date(2017, 7, 10)
    assert time_date_tools.next_weekday(datetime.date(2017, 7, 11), 0) == datetime.date(2017, 7, 17)
    assert time_date_tools.next_weekday(datetime.date(2017, 7, 9), 0) == datetime.date(2017, 7, 10)


def test_get_previous_week_last_day_happy_path():
    assert time_date_tools.get_previous_week_last_day(datetime.date(2017, 7, 10)) == datetime.date(2017, 7, 9)
    assert time_date_tools.get_previous_week_last_day(datetime.date(2017, 7, 9)) == datetime.date(2017, 7, 9)
    assert time_date_tools.get_previous_week_last_day(datetime.date(2017, 7, 8)) == datetime.date(2017, 7, 2)


def test_get_previous_week_first_day_happy_path():
    assert time_date_tools.get_previous_week_first_day(datetime.date(2017, 7, 10)) == datetime.date(2017, 7, 3)
    assert time_date_tools.get_previous_week_first_day(datetime.date(2017, 7, 9)) == datetime.date(2017, 7, 3)
    assert time_date_tools.get_previous_week_first_day(datetime.date(2017, 7, 15)) == datetime.date(2017, 7, 3)


def test_get_previous_week_start_end_dates_happy_path():
    dates = time_date_tools.get_previous_week_start_end_dates(datetime.date(2017, 7, 10))
    assert dates == (datetime.date(2017, 7, 3), datetime.date(2017, 7, 9))

    dates = time_date_tools.get_previous_week_start_end_dates(datetime.date(2017, 7, 15))
    assert dates == (datetime.date(2017, 7, 3), datetime.date(2017, 7, 9))

    dates = time_date_tools.get_previous_week_start_end_dates(datetime.date(2017, 7, 9))
    assert dates == (datetime.date(2017, 7, 3), datetime.date(2017, 7, 9))


def test_get_next_week_first_day_happy_path():
    assert (time_date_tools.get_next_week_first_day(datetime.date(2017, 7, 10)) == datetime.date(2017, 7, 10))
    assert (time_date_tools.get_next_week_first_day(datetime.date(2017, 7, 11)) == datetime.date(2017, 7, 17))
    assert (time_date_tools.get_next_week_first_day(datetime.date(2017, 7, 9)) == datetime.date(2017, 7, 10))


def test_get_next_week_last_day_happy_path():
    assert (time_date_tools.get_next_week_last_day(datetime.date(2017, 7, 10)) == datetime.date(2017, 7, 16))
    assert (time_date_tools.get_next_week_last_day(datetime.date(2017, 7, 11)) == datetime.date(2017, 7, 23))
    assert (time_date_tools.get_next_week_last_day(datetime.date(2017, 7, 9)) == datetime.date(2017, 7, 16))


def test_get_next_week_start_end_dates_happy_path():
    dates = time_date_tools.get_next_week_start_end_dates(datetime.date(2017, 7, 10))
    assert dates == (datetime.date(2017, 7, 10), datetime.date(2017, 7, 16))

    dates = time_date_tools.get_next_week_start_end_dates(datetime.date(2017, 7, 11))
    assert dates == (datetime.date(2017, 7, 17), datetime.date(2017, 7, 23))

    dates = time_date_tools.get_next_week_start_end_dates(datetime.date(2017, 7, 9))
    assert dates == (datetime.date(2017, 7, 10), datetime.date(2017, 7, 16))
