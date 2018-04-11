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
