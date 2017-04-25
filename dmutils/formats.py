# -*- coding: utf-8 -*-
from datetime import datetime
import pytz

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
DATE_FORMAT = "%Y-%m-%d"
DISPLAY_SHORT_DATE_FORMAT = '%-d %B'
DISPLAY_DATE_FORMAT = '%A %-d %B %Y'
DISPLAY_TIME_FORMAT = '%H:%M:%S'
DISPLAY_DATETIME_FORMAT = '%A %-d %B %Y at %H:%M'

LOTS = [
    {
        'lot': 'saas',
        'lot_case': 'SaaS',
        'label': u'Software as a Service',
    },
    {
        'lot': 'paas',
        'lot_case': 'PaaS',
        'label': u'Platform as a Service',
    },
    {
        'lot': 'iaas',
        'lot_case': 'IaaS',
        'label': u'Infrastructure as a Service',
    },
    {
        'lot': 'scs',
        'lot_case': 'SCS',
        'label': u'Specialist Cloud Services',
    },
]


def timeformat(value, default_value=None):
    return _format_date(value, default_value, DISPLAY_TIME_FORMAT)


def shortdateformat(value, default_value=None):
    return _format_date(value, default_value, DISPLAY_SHORT_DATE_FORMAT, localize=False)


def dateformat(value, default_value=None):
    return _format_date(value, default_value, DISPLAY_DATE_FORMAT, localize=False)


def datetimeformat(value, default_value=None):
    return _format_date(value, default_value, DISPLAY_DATETIME_FORMAT)


def datetodatetimeformat(value):
    try:
        date = datetime.strptime(value, DATE_FORMAT)
        return dateformat(date)
    except ValueError:
        return value


EUROPE_LONDON = pytz.timezone("Europe/London")


def _format_date(value, default_value, fmt, localize=True):
    if not value:
        return default_value
    if not isinstance(value, datetime):
        value = datetime.strptime(value, DATETIME_FORMAT)
    if value.tzinfo is None:
        value = pytz.utc.localize(value)
    if localize:
        return value.astimezone(EUROPE_LONDON).strftime(fmt)
    else:
        return value.strftime(fmt)


def lot_to_lot_case(lot_to_check):
    lot_i_found = [lot for lot in LOTS if lot['lot'] == lot_to_check]
    if lot_i_found:
        return lot_i_found[0]['lot_case']
    return None


def get_label_for_lot_param(lot_to_check):
    lot_i_found = [lot for lot in LOTS if lot['lot'] == lot_to_check]
    if lot_i_found:
        return lot_i_found[0]['label']
    return None
