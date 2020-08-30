import calendar
import datetime


def string_to_date(string_date):
    """
    Converts string 'YYYY-MM-DD' into a datetime.date object.
    :param string_date: The date string ('YYYY-MM-DD').
    :return: Returns a datetime.date object if the string is valid.
    """
    if not isinstance(string_date, str):
        raise ValueError("The input must be of type string")

    try:
        date_object = datetime.datetime.strptime(string_date, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError("The input must use the following format: 'YYYY-MM-DD', not {0}".format(string_date))

    return date_object


def date_to_timestamp_milliseconds(date, start_date=True):
    """
    Converts datetime.date object into datetime.timestamp object.
    The resulting timestamp is created from the input date at 00:00:00 (local time).
    The resulting timestamp doesn't contain milliseconds.
    :param date: The date string ('YYYY-MM-DD').
    :param start_date: If the start_date boolean is set to true, nothing changes, but
    if it is set to false, then 24h is added to the timestamp.
    :return: Returns a datetime.timestamp object of the input date @ 00:00:00 (local time).
    """
    if type(date) is not datetime.date:
        raise ValueError("The input must be of type datetime.date")

    if start_date:
        return (datetime.datetime.utcfromtimestamp(calendar.timegm(date.timetuple()))).replace(
            tzinfo=datetime.timezone.utc).timestamp() * 1000
    else:
        return (datetime.datetime.utcfromtimestamp(calendar.timegm(date.timetuple())).replace(
            tzinfo=datetime.timezone.utc).timestamp() + 24 * 60 * 60) * 1000


def datetime_to_modified_string(datetime_input):
    """
    Convert YYYY-MM-DD HH:MM:SS.MS -> YYYY-MM-DD_HH-MM-SS-MS.
    :param datetime_input: The datetime.datetime object.
    :return: Returns a string with the following format: 'YYYY-MM-DD_HH-MM-SS-MS'.
    """
    if type(datetime_input) is not datetime.datetime:
        raise ValueError("The input must be of type datetime.datetime")

    current_date = datetime.datetime.strptime(datetime_input.date().strftime("%Y-%m-%d"), '%Y-%m-%d').strftime('%Y-%m-%d')

    return (current_date + "_" + str(datetime_input.hour) + "-" + str(datetime_input.minute) + "-" + str(
        datetime_input.second) + "-" + str(datetime_input.microsecond))


def calculate_closing_date(date, buffer_time):
    """
    Subtracts buffer_time (days) from the input datetime.date object ("YYYY-MM-DD").
    :param date: The date object (datetime.date).
    :param buffer_time: The buffer time in days (integer).
    :return: Returns a date object (datetime.date).
    """
    if type(buffer_time) is not int:
        raise ValueError("The input must be of type int, not {0}".format(type(buffer_time)))

    if type(date) is not datetime.date:
        raise ValueError("The input must be of type datetime.date")

    return date - datetime.timedelta(days=buffer_time)


def get_previous_month_last_day(date):
    """
    Returns the previous month's last day (datetime.date).
    NB: If current date is the last day of the current month, then it returns itself.
    :param date: The date object (datetime.date).
    :return: Returns a date object (datetime.date) of the previous month's last day.
    """
    current_month = date.month
    next_day = date + datetime.timedelta(days=1)

    # Last day of the month
    if next_day.month != current_month:
        return date
    else:
        first_day = date.replace(day=1)
        previous_month = first_day - datetime.timedelta(days=1)
        return previous_month


def get_previous_month_first_day(date):
    """
    Returns the previous month's first day (datetime.date).
    NB: If current date is the last day of the current month, then it returns this month's first day.
    :param date: The date object (datetime.date).
    :return: Returns a date object (datetime.date) of the previous month's first day.
    """
    return get_previous_month_last_day(date).replace(day=1)


def get_previous_month_start_and_end_date(current_date):
    """
    Returns the start and end date of the previous month.
    If the current date is the last day of the current month, it returns current month's first and last day.
    :param current_date: The date object (datetime.date).
    :return: Returns date objects (datetime.date) of the previous month's first day and last day.
    """
    return get_previous_month_first_day(current_date), get_previous_month_last_day(current_date)


def next_weekday(current_date, weekday):
    """
    Returns the next occurrence of a given weekday including today.
    For example, if today is Monday, 2017.7.10, then next Monday will be 2017.7.10.
    :param current_date: The date object (datetime.date).
    :param weekday: 0 = Monday, 6 = Sunday
    :return: Returns the next occurrence of a given weekday including today.
    """
    days_ahead = weekday - current_date.weekday()  # 0 = Monday
    if days_ahead < 0:  # Target day already happened this week
        days_ahead += 7
    return current_date + datetime.timedelta(days=days_ahead)


def get_previous_week_last_day(current_date):
    """
    Returns the date of the last Sunday.
    If today is Sunday, returns today.
    :param current_date: The date object (datetime.date).
    :return: Returns the date of the last Sunday.
    """
    last_sunday = next_weekday(current_date, 6)
    if last_sunday == current_date:
        return last_sunday
    else:
        return last_sunday - datetime.timedelta(days=7)


def get_previous_week_first_day(current_date):
    """
    Returns the date of the last Monday.
    If today is Sunday, returns this weeks Monday.
    :param current_date: The date object (datetime.date).
    :return: Returns the date of the last Monday.
    """
    return get_previous_week_last_day(current_date) - datetime.timedelta(days=6)


def get_previous_week_start_end_dates(current_date):
    """
    Returns the start and end date of the previous week.
    If the current date is the last day of the current week, it returns current week's first and last day.
    :param current_date: The date object (datetime.date).
    :return: Returns the start and end date of the previous week.
    """
    return get_previous_week_first_day(current_date), get_previous_week_last_day(current_date)


def get_next_week_first_day(current_date):
    """
    Returns the date of the next Monday.
    If today is Monday, returns today.
    :param current_date: The date object (datetime.date).
    :return: Returns the date of the next Monday.
    """
    return next_weekday(current_date, 0)


def get_next_week_last_day(current_date):
    """
    Returns the date of the next weeks Sunday.
    If today is Monday, returns this Sunday.
    :param current_date: The date object (datetime.date).
    :return: Returns the date of the next weeks Sunday.
    """
    return get_next_week_first_day(current_date) + datetime.timedelta(days=6)


def get_next_week_start_end_dates(current_date):
    """
    Returns the start and end date of the next week.
    If the current date is the first day of the current week, it returns current week's first and last day.
    :param current_date: The date object (datetime.date).
    :return: Returns the start and end date of the next week.
    """
    return get_next_week_first_day(current_date), get_next_week_last_day(current_date)
