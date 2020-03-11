# -*- coding: utf-8 -*-
from datetime import datetime
import re
from typing import Union

import pytz

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
DATE_FORMAT = "%Y-%m-%d"
DISPLAY_MONTH_YEAR_FORMAT = "%B %Y"
DISPLAY_SHORT_DATE_FORMAT = '%-d %B'
DISPLAY_NO_DAY_DATE_FORMAT = '%-d %B %Y'
DISPLAY_DATE_FORMAT = '%A %-d %B %Y'
DISPLAY_TIME_FORMAT = '%H:%M:%S'
DISPLAY_TIME_TZ_FORMAT = '%-I:%M%p %Z'
DISPLAY_DATETIME_FORMAT = '%A %-d %B %Y at %I:%M%p %Z'
DISPLAY_SHORTTIME_LONGDATE_FORMAT = '%-I%p %Z, %A %-d %B %Y'


def timeformat(value, default_value=None):
    """
    Example value: datetime.strptime("2018-07-25 10:15:00", "%Y-%m-%d %H:%M:%S")
    Example output: '11:15:00'

    "timeformat" is used in summary tables where space is tight and times are shown on their own line.
    Currently (Jan 2018) only used in admin app tables.
    """
    return _format_date(value, default_value, DISPLAY_TIME_FORMAT, localize=False)


def displaytimeformat(value, default_value=None):
    """
    Example value: datetime.strptime("2018-07-25 08:15:00", "%Y-%m-%d %H:%M:%S")
    Example output: '9:15am BST'

    "timeformat_with_tz" is used for events which are less than a few hours away.
    Currently (Mar 2019) only used in timeout warnings to users.
    """
    return _format_date(value, default_value, DISPLAY_TIME_TZ_FORMAT, localize=True)


def shortdateformat(value, default_value=None):
    """
    Example value: datetime.strptime("2018-07-25 10:15:00", "%Y-%m-%d %H:%M:%S")
    Example output: '25 July'

    "shortdateformat" was designed for use in summary tables where space is tight and dates are shown on their own line.
    The original intended use was in conjunction with "timeformat" in admin app summary tables.
    It is now (Jan 2018) also used in briefs-frontend on the "Publish your requirements" page only.

    ** USE OUR STANDARD dateformat RATHER THAN THIS UNLESS THERE IS A GOOD REASON NOT TO **
    """
    return _format_date(value, default_value, DISPLAY_SHORT_DATE_FORMAT, localize=False)


def nodaydateformat(value, default_value=None):
    """
    Example value: datetime.strptime("2018-07-25 10:15:00", "%Y-%m-%d %H:%M:%S")
    Example output: '25 July 2018'

    `nodaydateformat` is used *only* when generating framework agreement signature pages. If you're thinking about
    using this, you probably want to use `dateformat` instead.
    """
    return _format_date(value, default_value, DISPLAY_NO_DAY_DATE_FORMAT, localize=False)


def dateformat(value, default_value=None):
    """
    Example value: datetime.strptime("2018-07-25 10:15:00", "%Y-%m-%d %H:%M:%S")
    Example output: 'Wednesday 25 July 2018'

    "dateformat" is the standard format used for dates in our frontend apps.
    If you're displaying a date on a page then this is probably the one you want.
    Examples of use:
      * dates that opportunities are created/published/closing/closed/withdrawn
      * dates that framework communication files were published
      * dates of revisions made to services (shown to admin users)
    """
    return _format_date(value, default_value, DISPLAY_DATE_FORMAT, localize=False)


def monthyearformat(value, default_value=None):
    """
    Example value: datetime.strptime("2018-07-25 10:15:00", "%Y-%m-%d %H:%M:%S") OR "2010-01-01T13:00:00.000000Z"
    Example output: 'July 2018'

    This is used when precision is not required and we are trying to remind a user roughly when a historical event
    occurred. The only place this is currently used is when offering a supplier the ability to reuse their declaration
    from a previous framework and we want to remind them roughly when those answers were provided.
    """
    return _format_date(value, default_value, DISPLAY_MONTH_YEAR_FORMAT, localize=False)


def datetimeformat(value, default_value=None, localize=True):
    """
    Example value: datetime.strptime("2018-07-25 23:59:59", "%Y-%m-%d %H:%M:%S")
    Example output: 'Thursday 26 July 2018 at 12:59am BST'
    Example output (localize=False): 'Wednesday 25 July 2018 at 11:59pm UTC'

    "datetimeformat" is the standard format used for timestamps (i.e. date and time) in our frontend apps.
    If you're displaying a date and time on a page then this is probably the one you want (unless it is a
    brief closing date, in which case use "utcdatetimeformat" below).
    Examples of use:
      * dates that opportunities are created/published/closing/closed/withdrawn
      * dates that framework communication files were published
      * dates of revisions made to services (shown to admin users)
    """
    return _format_date(value, default_value, DISPLAY_DATETIME_FORMAT, localize=localize)


def iso_datetime_format(value, default_value=None):
    """
    Example value: datetime.strptime("2018-07-25 23:59:59", "%Y-%m-%d %H:%M:%S")
    Example output: '2018-07-25T23:59:59.000000Z'
    :param value: some datetime that you want to format using ISO 8601 formatting
    :param default_value: default to return if value is None
    :return: string formatted per ISO 8601 in UTC, assuming the datetime passed in was UTC
    """
    return _format_date(value, default_value, DATETIME_FORMAT, localize=False)


def utctoshorttimelongdateformat(value, default_value=None, localize=True):
    """
    Example value: datetime.strptime("2010-01-01 13:00:00", "%Y-%m-%d %H:%M:%S") OR "2010-01-01T13:00:00.000000Z"
    Example output: '1pm GMT, Friday 1 January 2010'

    "utctoshorttimelongdateformat" takes a datetime object or ISO8601 datetime string, localizes it to GMT/BST (as
    appropriate), and then outputs a string with a short time description followed by a long date description including
    the day of the week.

    By default, this will localize the output string so that it shows GMT/BST as appropriate for the target datetime.

    This is primarily used for important framework lifecycle events during the application process.
    """
    formatted_datetime = _format_date(value, default_value, DISPLAY_SHORTTIME_LONGDATE_FORMAT, localize=localize)
    return formatted_datetime


def utcdatetimeformat(value, default_value=None):
    """
    Example value: datetime.strptime("2018-07-25 23:59:59", "%Y-%m-%d %H:%M:%S")
    Example output: 'Wednesday 25 July 2018 at 11:59pm GMT'

    "utcdatetimeformat" forces the timestamp to be output to be in GMT, no matter what the local time is.

    This is intended *ONLY* to be used for *DEADLINES* that are stored in the database as 23:59:59 (UTC+00).
    In this case localisation would display the date as 12.59am on the next day (due to daylight saving),
    potentially causing confusion for buyers/suppliers.
    This is currently (Jan 2018) used wherever we show the closing date for briefs or brief clarification questions.
    """
    local_format = datetimeformat(value, default_value)
    if local_format:
        if "11:59pm" not in local_format:
            # Force UTC+00 if the date has rolled over to the next day and append timezone
            return _use_gmt_timezone(datetimeformat(value, default_value, localize=False))
        return _use_gmt_timezone(local_format)
    return None


def datetodatetimeformat(value):
    """
    Example value: "2018-07-25"
    Example output: 'Wednesday 25 July 2018'

    "datetodatetimeformat" is a convenience function to convert a date *STRING* from one format to another.
    This is currently (Jan 2018) only used to reformat the "startDate" from briefs, which is submitted by
    buyers in DATE_FORMAT but that we want to show to other users of the site in our standard DISPLAY_DATE_FORMAT.

    :param value: a STRING that matches our DATE_FORMAT (eg "2018-01-25")
    :return: a STRING for the same DATE that matches our DISPLAY_DATE_FORMAT (eg "Thursday 25 January 2018")
    """
    try:
        date = datetime.strptime(value, DATE_FORMAT)
        return dateformat(date)
    except ValueError:
        return value


EUROPE_LONDON = pytz.timezone("Europe/London")


def _use_gmt_timezone(date_string):
    return re.sub(r"UTC|BST", "GMT", date_string)


def get_localized_datetime(value: Union[str, datetime], localize: bool = True) -> datetime:
    """
    Given a datetime or an ISO timestamp, will return a London-timezone-localized datetime
    """
    if not isinstance(value, datetime):
        value = datetime.strptime(value, DATETIME_FORMAT)

    if value.tzinfo is None:
        # assume naive datetimes are UTC
        value = pytz.utc.localize(value)

    if localize:
        value = value.astimezone(EUROPE_LONDON)

    return value


def _format_date(value, default_value, fmt, localize=True):
    if not value:
        return default_value

    value = get_localized_datetime(value, localize=localize).strftime(fmt)

    # en_GB locale uses uppercase AM/PM which contravenes our style guide
    value = value.replace('AM', 'am').replace('PM', 'pm').replace(" 0", " ")

    return value
