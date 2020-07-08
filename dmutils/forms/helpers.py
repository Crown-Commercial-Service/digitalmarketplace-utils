
# allow importing from dmutils.forms.helpers for backwards compatibility
from .errors import get_errors_from_wtform  # noqa: F401

import typing


def remove_csrf_token(data):
    """Flask-WTF==0.14.2 now includes `csrf_token` in `form.data`, whereas previously wtforms explicitly didn't do
    this. When we pass form data straight through to the API, the API often carries out strict validation and doesn't
    like to see `csrf_token` in the input. So this helper will strip it out of a dict, if it's present.

    Example:
    >>> remove_csrf_token(form.data)
    """
    cleaned_data = {**data}

    if 'csrf_token' in data:
        del cleaned_data['csrf_token']

    return cleaned_data


def govuk_option(option: typing.Dict) -> typing.Dict:
    if option:
        # DMp's yml does not requires only labels, which is used as the value if none is provided
        item = {
            "value": option.get('value', option['label']),
            "text": option['label'],
        }
        if "description" in option:
            item.update({"hint": {"text": option["description"]}})
        return item
    else:
        return {}


def govuk_options(options: typing.List[typing.Dict]) -> typing.List[typing.Dict]:
    return [govuk_option(option) for option in options]
