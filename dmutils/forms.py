from itertools import chain
import re

from wtforms import StringField
from wtforms.validators import Regexp


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
    _email_re = re.compile(r"^[^@\s]+@[^@\.\s]+(\.[^@\.\s]+)+$")

    def __init__(self, label=None, **kwargs):
        kwargs["validators"] = tuple(chain(
            kwargs.pop("validators", ()),
            (
                Regexp(self._email_re, message="Please enter a valid email address"),
            ),
        ))
        super(EmailField, self).__init__(label, **kwargs)


def strip_whitespace(value):
    if value is not None and hasattr(value, 'strip'):
        return value.strip()
    return value
