from collections import OrderedDict
from itertools import chain
import re

from wtforms import StringField
from wtforms.validators import Regexp, Length


class StripWhitespaceStringField(StringField):
    def __init__(self, label=None, **kwargs):
        kwargs['filters'] = tuple(chain(
            kwargs.get('filters', ()),
            (
                strip_whitespace,
            ),
        ))
        super(StringField, self).__init__(label, **kwargs)


class EmailField(StripWhitespaceStringField):
    def __init__(self, label=None, **kwargs):
        kwargs["validators"] = tuple(chain(
            kwargs.pop("validators", ()),
            (
                EmailValidator(),
                Length(max=511, message="Please enter an email address under 512 characters."),
            ),
        ))
        super(EmailField, self).__init__(label, **kwargs)


def strip_whitespace(value):
    if value is not None and hasattr(value, 'strip'):
        return value.strip()
    return value


class EmailValidator(Regexp):
    _email_re = re.compile(r"^[^@\s]+@[^@\.\s]+(\.[^@\.\s]+)+$")

    def __init__(self, **kwargs):
        kwargs.setdefault("message", "Please enter a valid email address.")
        super(EmailValidator, self).__init__(self._email_re, **kwargs)


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


def get_errors_from_wtform(form):
    """Converts errors from a Flask-WTForm into the same format we generate from content-loader forms. This allows us
    to treat errors from both content-loader forms and wtforms the same way inside templates.
    :param form: A Flask-WTForm
    :return: A dict with three keys: `input_name`, `question`, and `message` suitable for passing into templates.
    """
    return OrderedDict(
        (key, {'input_name': key, 'question': form[key].label.text, 'message': form[key].errors[0]})
        for key in
        form.errors.keys()
    )
