# -*- coding: utf-8 -*-
from dmutils.formats import (
    dateformat,
    datetimeformat,
    displaytimeformat,
    iso_datetime_format,
    datetodatetimeformat,
    monthyearformat,
    nodaydateformat,
    shortdateformat,
    timeformat,
    utcdatetimeformat,
    utctoshorttimelongdateformat,
)
import pytz
from datetime import datetime
import pytest


@pytest.mark.parametrize("dt, formatted_time", (
    (datetime(2012, 11, 10, 9, 8, 7, 6), "09:08:07"),
    ("2012-11-10T09:08:07.0Z", "09:08:07"),
    (datetime(2012, 8, 10, 9, 8, 7, 6), "09:08:07"),  # Time is UTC/GMT despite it being summer time
    ("2012-08-12T12:12:12.0Z", "12:12:12"),  # Time is UTC/GMT despite it being summer time
    (datetime(2012, 8, 10, 9, 8, 7, 6, tzinfo=pytz.utc), "09:08:07"),  # Time is UTC/GMT despite it being summer time
    (datetime(2012, 8, 10, 0, 8, 7, 6, tzinfo=pytz.utc), "00:08:07"),  # Time is UTC/GMT despite it being summer time
))
def test_timeformat(dt, formatted_time):
    assert timeformat(dt) == formatted_time


@pytest.mark.parametrize("dt, formatted_date", (
    (datetime(2012, 11, 10, 9, 8, 7, 6), "10 November"),
    ("2012-11-10T09:08:07.0Z", "10 November"),
    (datetime(2012, 8, 10, 9, 8, 7, 6), "10 August"),
    ("2012-08-10T09:08:07.0Z", "10 August"),
    (datetime(2012, 8, 10, 9, 8, 7, 6, tzinfo=pytz.utc), "10 August"),
    ("2016-04-27T23:59:59.0Z", "27 April"),
    (datetime(2016, 4, 27, 23, 59, 59, 0, tzinfo=pytz.utc), "27 April"),
    (datetime(2012, 8, 1, 9, 8, 7, 6, tzinfo=pytz.utc), "1 August"),
))
def test_shortdateformat(dt, formatted_date):
    assert shortdateformat(dt) == formatted_date


@pytest.mark.parametrize("dt, formatted_date", (
    (datetime(2012, 11, 10, 9, 8, 7, 6), "10 November 2012"),
    ("2012-11-10T09:08:07.0Z", "10 November 2012"),
    (datetime(2012, 8, 10, 9, 8, 7, 6), "10 August 2012"),
    ("2012-08-10T09:08:07.0Z", "10 August 2012"),
    (datetime(2012, 8, 10, 9, 8, 7, 6, tzinfo=pytz.utc), "10 August 2012"),
    ("2016-04-27T23:59:59.0Z", "27 April 2016"),
    (datetime(2016, 4, 27, 23, 59, 59, 0), "27 April 2016"),
    (datetime(2012, 8, 1, 9, 8, 7, 6, tzinfo=pytz.utc), "1 August 2012"),
))
def test_nodaydateformat(dt, formatted_date):
    assert nodaydateformat(dt) == formatted_date


@pytest.mark.parametrize("dt, formatted_date", (
    (datetime(2012, 11, 10, 9, 8, 7, 6), "Saturday 10 November 2012"),
    ("2012-11-10T09:08:07.0Z", "Saturday 10 November 2012"),
    (datetime(2012, 8, 10, 9, 8, 7, 6), "Friday 10 August 2012"),
    ("2012-08-10T09:08:07.0Z", "Friday 10 August 2012"),
    (datetime(2012, 8, 10, 9, 8, 7, 6, tzinfo=pytz.utc), "Friday 10 August 2012"),
    ("2016-04-27T23:59:59.0Z", "Wednesday 27 April 2016"),
    (datetime(2016, 4, 27, 23, 59, 59, 0), "Wednesday 27 April 2016"),
    (datetime(2012, 8, 1, 9, 8, 7, 6, tzinfo=pytz.utc), "Wednesday 1 August 2012"),
))
def test_dateformat(dt, formatted_date):
    assert dateformat(dt) == formatted_date


@pytest.mark.parametrize("dt, default_value, formatted_date", (
    (datetime(2012, 11, 10, 9, 8, 7, 6), None, "November 2012"),
    ("2012-11-10T09:08:07.0Z", None, "November 2012"),
    (datetime(2012, 8, 10, 9, 8, 7, 6), None, "August 2012"),
    ("2012-08-10T09:08:07.0Z", None, "August 2012"),
    (datetime(2012, 8, 10, 9, 8, 7, 6, tzinfo=pytz.utc), None, "August 2012"),
    ("2016-04-27T23:59:59.0Z", None, "April 2016"),
    (datetime(2016, 4, 27, 23, 59, 59, 0), None, "April 2016"),
    (datetime(2012, 8, 1, 9, 8, 7, 6, tzinfo=pytz.utc), None, "August 2012"),

    # Check fall back to default_value if no date provided
    (None, 'default-value', 'default-value')
))
def test_monthyearformat(dt, default_value, formatted_date):
    assert monthyearformat(dt, default_value=default_value) == formatted_date


@pytest.mark.parametrize("dt, formatted_datetime", (
    (datetime(2012, 11, 10, 9, 8, 7, 6), "Saturday 10 November 2012 at 9:08am GMT"),
    ("2012-11-10T09:08:07.0Z", "Saturday 10 November 2012 at 9:08am GMT"),
    (datetime(2012, 8, 10, 9, 8, 7, 6), "Friday 10 August 2012 at 10:08am BST"),
    ("2012-08-10T09:08:07.0Z", "Friday 10 August 2012 at 10:08am BST"),
    (datetime(2012, 8, 10, 9, 8, 7, 6, tzinfo=pytz.utc), "Friday 10 August 2012 at 10:08am BST"),
    (datetime(2012, 8, 1, 9, 8, 7, 6, tzinfo=pytz.utc), "Wednesday 1 August 2012 at 10:08am BST"),
    (datetime(2012, 8, 1, 22, 59, 7, 6, tzinfo=pytz.utc), "Wednesday 1 August 2012 at 11:59pm BST"),
    # Daylight savings edge case
    (datetime(2012, 3, 25, 0, 59, 7, 6, tzinfo=pytz.utc), "Sunday 25 March 2012 at 12:59am GMT"),
    (datetime(2012, 3, 25, 1, 59, 7, 6, tzinfo=pytz.utc), "Sunday 25 March 2012 at 2:59am BST"),
    # Fall back to default if no valid date supplied
    (None, None),
))
def test_datetimeformat(dt, formatted_datetime):
    assert datetimeformat(dt) == formatted_datetime


@pytest.mark.parametrize("dt, formatted_time", (
    (datetime(2012, 11, 10, 9, 8, 7, 6), "9:08am GMT"),
    ("2012-11-10T09:08:07.0Z", "9:08am GMT"),
    (datetime(2012, 8, 10, 9, 8, 7, 6), "10:08am BST"),
    ("2012-08-10T09:08:07.0Z", "10:08am BST"),
    (datetime(2012, 8, 10, 9, 8, 7, 6, tzinfo=pytz.utc), "10:08am BST"),
    (datetime(2012, 8, 1, 9, 8, 7, 6, tzinfo=pytz.utc), "10:08am BST"),
    (datetime(2012, 8, 1, 22, 59, 7, 6, tzinfo=pytz.utc), "11:59pm BST"),
    # Daylight savings edge case
    (datetime(2012, 3, 25, 0, 59, 7, 6, tzinfo=pytz.utc), "12:59am GMT"),
    (datetime(2012, 3, 25, 1, 59, 7, 6, tzinfo=pytz.utc), "2:59am BST"),
    # Fall back to default if no valid date supplied
    (None, None),
))
def test_displaytimeformat(dt, formatted_time):
    assert displaytimeformat(dt) == formatted_time


@pytest.mark.parametrize("dt, formatted_datetime", (
    (datetime(2012, 11, 10, 9, 8, 7, 6), "2012-11-10T09:08:07.000006Z"),
    ("2012-11-10T09:08:07.0Z", "2012-11-10T09:08:07.000000Z"),
    (datetime(2012, 8, 10, 9, 8, 7, 6), "2012-08-10T09:08:07.000006Z"),
    ("2012-08-10T09:08:07.0Z", "2012-08-10T09:08:07.000000Z"),
    # Fall back to default if no valid date supplied
    (None, 'my_default'),
))
def test_iso_datetime_format(dt, formatted_datetime):
    assert iso_datetime_format(dt, 'my_default') == formatted_datetime


@pytest.mark.parametrize("dt, localize, default_value, formatted_datetime", (
    (datetime(2012, 11, 10, 9, 8, 7, 6), True, None, "9am GMT, Saturday 10 November 2012"),
    ("2012-11-10T09:08:07.0Z", True, None, "9am GMT, Saturday 10 November 2012"),
    (datetime(2012, 8, 10, 9, 8, 7, 6), True, None, "10am BST, Friday 10 August 2012"),
    ("2012-08-10T09:08:07.0Z", True, None, "10am BST, Friday 10 August 2012"),
    (datetime(2012, 8, 10, 9, 8, 7, 6, tzinfo=pytz.utc), True, None, "10am BST, Friday 10 August 2012"),
    (datetime(2012, 8, 1, 9, 8, 7, 6, tzinfo=pytz.utc), True, None, "10am BST, Wednesday 1 August 2012"),
    (datetime(2012, 8, 1, 22, 59, 7, 6, tzinfo=pytz.utc), True, None, "11pm BST, Wednesday 1 August 2012"),

    # Daylight savings edge case
    (datetime(2012, 3, 25, 0, 59, 7, 6, tzinfo=pytz.utc), True, None, "12am GMT, Sunday 25 March 2012"),
    (datetime(2012, 3, 25, 1, 59, 7, 6, tzinfo=pytz.utc), True, None, "2am BST, Sunday 25 March 2012"),

    # Check localization can be disabled
    (datetime(2012, 8, 1, 9, 8, 7, 6, tzinfo=pytz.utc), False, None, "9am UTC, Wednesday 1 August 2012"),

    # Check default_value returned if no value specified
    (datetime(2012, 8, 1, 9, 8, 7, 6, tzinfo=pytz.utc), True, 'my-default-value', "10am BST, Wednesday 1 August 2012"),
    (None, False, 'my-default-value', "my-default-value"),

    # Fall back to default if no valid date supplied
    (None, True, None, None),
))
def test_utctoshorttimelongdateformat(dt, localize, default_value, formatted_datetime):
    assert utctoshorttimelongdateformat(dt, localize=localize, default_value=default_value) == formatted_datetime


@pytest.mark.parametrize("dt, formatted_datetime", (
    # UTC+00 date: display as normal
    (datetime(2012, 3, 24, 23, 59, 7, 6, tzinfo=pytz.utc), "Saturday 24 March 2012 at 11:59pm GMT"),
    # UTC+01 date: force to UTC+00 if date would rollover to the next day
    (datetime(2012, 3, 25, 23, 59, 7, 6, tzinfo=pytz.utc), "Sunday 25 March 2012 at 11:59pm GMT"),
    # Fall back to default if no valid date supplied
    (None, None),
))
def test_utcdatetimeformat(dt, formatted_datetime):
    assert utcdatetimeformat(dt) == formatted_datetime


@pytest.mark.parametrize(
    ("date", "expected_formatted_date"),
    (('foo', 'foo'), ('2017-04-25', 'Tuesday 25 April 2017'), ('2017-4-25', 'Tuesday 25 April 2017'))
)
def test_datetodatetimeformat(date, expected_formatted_date):
    assert datetodatetimeformat(date) == expected_formatted_date
