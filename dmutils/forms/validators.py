
import re

from wtforms.validators import Regexp


class EmailValidator(Regexp):
    _email_re = re.compile(r"^[^@\s]+@[^@\.\s]+(\.[^@\.\s]+)+$")

    def __init__(self, **kwargs):
        kwargs.setdefault("message", "Please enter a valid email address.")
        super(EmailValidator, self).__init__(self._email_re, **kwargs)
