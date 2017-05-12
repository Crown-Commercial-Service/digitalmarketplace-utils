# -*- coding: utf-8 -*-
from dmutils.formats import (
    timeformat, shortdateformat, dateformat, datetimeformat, datetodatetimeformat
)
import pytz
from datetime import datetime
import pytest


def test_timeformat():
    cases = [
        (datetime(2012, 11, 10, 9, 8, 7, 6), "09:08:07"),
        ("2012-11-10T09:08:07.0Z", "09:08:07"),
        (datetime(2012, 8, 10, 9, 8, 7, 6), "10:08:07"),
        ("2012-08-12T12:12:12.0Z", "13:12:12"),
        (datetime(2012, 8, 10, 9, 8, 7, 6, tzinfo=pytz.utc), "10:08:07"),
        (datetime(2012, 8, 10, 0, 8, 7, 6, tzinfo=pytz.utc), "01:08:07"),
    ]

    def check_timeformat(dt, formatted_time):
        assert timeformat(dt) == formatted_time

    for dt, formatted_time in cases:
        yield check_timeformat, dt, formatted_time


def test_shortdateformat():
    cases = [
        (datetime(2012, 11, 10, 9, 8, 7, 6), "10 November"),
        ("2012-11-10T09:08:07.0Z", "10 November"),
        (datetime(2012, 8, 10, 9, 8, 7, 6), "10 August"),
        ("2012-08-10T09:08:07.0Z", "10 August"),
        (datetime(2012, 8, 10, 9, 8, 7, 6, tzinfo=pytz.utc), "10 August"),
        ("2016-04-27T23:59:59.0Z", "27 April"),
        (datetime(2016, 4, 27, 23, 59, 59, 0, tzinfo=pytz.utc), "27 April"),
        (datetime(2012, 8, 1, 9, 8, 7, 6, tzinfo=pytz.utc), "1 August"),
    ]

    def check_shortdateformat(dt, formatted_date):
        assert shortdateformat(dt) == formatted_date

    for dt, formatted_date in cases:
        yield check_shortdateformat, dt, formatted_date


def test_dateformat():
    cases = [
        (datetime(2012, 11, 10, 9, 8, 7, 6), "Saturday 10 November 2012"),
        ("2012-11-10T09:08:07.0Z", "Saturday 10 November 2012"),
        (datetime(2012, 8, 10, 9, 8, 7, 6), "Friday 10 August 2012"),
        ("2012-08-10T09:08:07.0Z", "Friday 10 August 2012"),
        (datetime(2012, 8, 10, 9, 8, 7, 6, tzinfo=pytz.utc), "Friday 10 August 2012"),
        ("2016-04-27T23:59:59.0Z", "Wednesday 27 April 2016"),
        (datetime(2016, 4, 27, 23, 59, 59, 0), "Wednesday 27 April 2016"),
        (datetime(2012, 8, 1, 9, 8, 7, 6, tzinfo=pytz.utc), "Wednesday 1 August 2012"),
    ]

    def check_dateformat(dt, formatted_date):
        assert dateformat(dt) == formatted_date

    for dt, formatted_date in cases:
        yield check_dateformat, dt, formatted_date


def test_datetimeformat():
    cases = [
        (datetime(2012, 11, 10, 9, 8, 7, 6), "Saturday 10 November 2012 at 09:08"),
        ("2012-11-10T09:08:07.0Z", "Saturday 10 November 2012 at 09:08"),
        (datetime(2012, 8, 10, 9, 8, 7, 6), "Friday 10 August 2012 at 10:08"),
        ("2012-08-10T09:08:07.0Z", "Friday 10 August 2012 at 10:08"),
        (datetime(2012, 8, 10, 9, 8, 7, 6, tzinfo=pytz.utc), "Friday 10 August 2012 at 10:08"),
        (datetime(2012, 8, 1, 9, 8, 7, 6, tzinfo=pytz.utc), "Wednesday 1 August 2012 at 10:08"),
    ]

    def check_datetimeformat(dt, formatted_datetime):
        assert datetimeformat(dt) == formatted_datetime

    for dt, formatted_datetime in cases:
        yield check_datetimeformat, dt, formatted_datetime


@pytest.mark.parametrize(
    ("date", "expected_formatted_date"),
    (('foo', 'foo'), ('2017-04-25', 'Tuesday 25 April 2017'), ('2017-4-25', 'Tuesday 25 April 2017'))
)
def test_datetodatetimeformat(date, expected_formatted_date):
    assert datetodatetimeformat(date) == expected_formatted_date
