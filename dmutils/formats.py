# -*- coding: utf-8 -*-
from datetime import datetime
import pytz

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
DATE_FORMAT = "%Y-%m-%d"
DISPLAY_SHORT_DATE_FORMAT = '%d %B'
DISPLAY_DATE_FORMAT = '%A %d %B %Y'
DISPLAY_TIME_FORMAT = '%H:%M:%S'
DISPLAY_DATETIME_FORMAT = '%A %d %B %Y at %H:%M'

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
    return _format_date(value, default_value, DISPLAY_SHORT_DATE_FORMAT)


def dateformat(value, default_value=None):
    return _format_date(value, default_value, DISPLAY_DATE_FORMAT)


def datetimeformat(value, default_value=None):
    return _format_date(value, default_value, DISPLAY_DATETIME_FORMAT)


EUROPE_LONDON = pytz.timezone("Europe/London")


def _format_date(value, default_value, fmt):
    if not value:
        return default_value
    if not isinstance(value, datetime):
        value = datetime.strptime(value, DATETIME_FORMAT)
    if value.tzinfo is None:
        value = pytz.utc.localize(value)
    return value.astimezone(EUROPE_LONDON).strftime(fmt)


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


def format_service_price(service):
    """Format a price string from a service dictionary

    :param service: a service dictionary as would be returned from the data API

    :return: a formatted price string if the required
             fields are set in the service dictionary.
    """
    if not service.get('priceMin'):
        return ''
    return format_price(
        service.get('priceMin'),
        service.get('priceMax'),
        service.get('priceUnit'),
        service.get('priceInterval'))


def format_price(min_price, max_price, unit, interval):
    """Format a price string"""
    formatted_price = u'£' + min_price
    if max_price:
        formatted_price += u' to £' + max_price
    formatted_price += ' per ' + unit.lower()
    if interval:
        formatted_price += ' per ' + interval.lower()
    return formatted_price
