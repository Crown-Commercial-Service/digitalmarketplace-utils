from datetime import datetime, timedelta
from workdays import workday

from .formats import dateformat, utctoshorttimelongdateformat


def get_publishing_dates(brief):
    APPLICATION_OPEN_DAYS = {'1 week': 7, '2 weeks': 14}
    QUESTIONS_OPEN_DAYS = {'1 week': 2, '2 weeks': 5}
    dates = {}

    if _brief_is_from_api_(brief):
        dates['published_date'] = _get_start_date_from_brief_api(brief)
    elif _brief_is_from_frontend_app_and_published_(brief):
        dates['published_date'] = _get_start_date_from_published_frontend_brief(brief)
    else:
        dates['published_date'] = _get_todays_date()

    length = _get_length_of_brief(brief)

    dates['closing_date'] = dates['published_date'] + timedelta(days=APPLICATION_OPEN_DAYS[length])
    dates['questions_close'] = workday(dates['published_date'], QUESTIONS_OPEN_DAYS[length])
    dates['answers_close'] = workday(dates['closing_date'], -1)
    dates['application_open_weeks'] = length
    dates['closing_time'] = '{d:%I:%M %p}'.format(d=dates['closing_date']).lower()

    return dates


def _brief_is_from_api_(brief):
    return brief.get('publishedAt') and isinstance(brief.get('publishedAt'), datetime)


def _brief_is_from_frontend_app_and_published_(brief):
    return brief.get('publishedAt') and isinstance(brief.get('publishedAt'), str)


def _get_start_date_from_brief_api(brief):
    return brief.get('publishedAt').replace(hour=23, minute=59, second=59, microsecond=0)


def _get_start_date_from_published_frontend_brief(brief):
    return datetime.strptime(brief['publishedAt'][0:10], '%Y-%m-%d') \
        .replace(hour=23, minute=59, second=59, microsecond=0)


def _get_todays_date():
    return datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=0)


def _get_length_of_brief(brief):
    return brief['requirementsLength'] if brief.get('requirementsLength') else '2 weeks'


def update_framework_with_formatted_dates(framework):
    """Takes a framework record (as returned by eg data_api_client.get_framework) and inserts new keys
    for any date/time values that should be displayed consistently on the frontends.

    This is currently used for important framework lifecycle/application dates."""
    framework.update({
        'clarificationsCloseAt': utctoshorttimelongdateformat(framework['clarificationsCloseAtUTC']),
        'clarificationsPublishAt': utctoshorttimelongdateformat(framework['clarificationsPublishAtUTC']),
        'applicationsCloseAt': utctoshorttimelongdateformat(framework['applicationsCloseAtUTC']),
        'intentionToAwardAt': dateformat(framework['intentionToAwardAtUTC']),
        'frameworkLiveAt': dateformat(framework['frameworkLiveAtUTC']),
        'frameworkExpiresAt': dateformat(framework['frameworkExpiresAtUTC']),
    })
