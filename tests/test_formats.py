# -*- coding: utf-8 -*-
from dmutils.formats import (
    get_label_for_lot_param, lot_to_lot_case,
    format_price, format_service_price,
    timeformat, shortdateformat, dateformat, datetimeformat,
    chunk_service_id
)
import pytz
from datetime import datetime
import pytest


class TestFormats(object):

    def test_returns_lot_in_lot_case(self):

        cases = [
            ("saas", "SaaS"),
            ("iaas", "IaaS"),
            ("paas", "PaaS"),
            ("scs", "SCS"),
            ("dewdew", None),
        ]

        for example, expected in cases:
            assert lot_to_lot_case(example) == expected

    def test_returns_label_for_lot(self):

        cases = [
            ("saas", "Software as a Service"),
            ("iaas", "Infrastructure as a Service"),
            ("paas", "Platform as a Service"),
            ("scs", "Specialist Cloud Services"),
            ("dewdew", None),
        ]

        for example, expected in cases:
            assert get_label_for_lot_param(example) == expected


def test_format_service_price():
    service = {
        'priceMin': '12.12',
        'priceMax': '13.13',
        'priceUnit': 'Unit',
        'priceInterval': 'Second',
    }

    cases = [
        ('12.12', u'£12.12 to £13.13 per unit per second'),
        ('', ''),
        (None, ''),
    ]

    def check_service_price_formatting(price_min, formatted_price):
        service['priceMin'] = price_min
        assert format_service_price(service) == formatted_price

    for price_min, formatted_price in cases:
        yield check_service_price_formatting, price_min, formatted_price


def test_format_price():
    cases = [
        ((u'12', None, 'Unit', None), u'£12 per unit'),
        (('12', '13', 'Unit', None), u'£12 to £13 per unit'),
        (('12', '13', 'Unit', 'Second'), u'£12 to £13 per unit per second'),
        (('12', None, 'Unit', 'Second'), u'£12 per unit per second'),
    ]

    def check_price_formatting(args, formatted_price):
        assert format_price(*args) == formatted_price

    for args, formatted_price in cases:
        yield check_price_formatting, args, formatted_price


def test_format_price_errors():
    cases = [
        ('12', None, None, None),
        (None, None, None, None),
    ]

    def check_price_formatting(case):
        with pytest.raises((TypeError, AttributeError)):
            format_price(*case)

    for case in cases:
        yield check_price_formatting, case


def test_timeformat():
    cases = [
        (datetime(2012, 11, 10, 9, 8, 7, 6), "09:08:07"),
        ("2012-11-10T09:08:07.0Z", "09:08:07"),
        (datetime(2012, 8, 10, 9, 8, 7, 6), "10:08:07"),
        ("2012-08-12T12:12:12.0Z", "13:12:12"),
        (datetime(2012, 8, 10, 9, 8, 7, 6, tzinfo=pytz.utc), "10:08:07"),
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
    ]

    def check_datetimeformat(dt, formatted_datetime):
        assert datetimeformat(dt) == formatted_datetime

    for dt, formatted_datetime in cases:
        yield check_datetimeformat, dt, formatted_datetime


def test_chunk_service_id():
    cases = [
        (12345678, ['1234', '5678']),
        ('12345678', ['1234', '5678']),
        ('A1234567', ['A1234567']),
    ]

    def check_chunked_service_id(service_id, chunked_service_id):
        assert chunk_service_id(service_id) == chunked_service_id

    for service_id, chunked_service_id in cases:
        yield check_chunked_service_id, service_id, chunked_service_id
