'''
Validators for WTForms used in the Digital Marketplace frontend

EmailValidator -- validate that a string is a valid email address
GreaterThan -- compare the values of two fields
FourDigitYear -- validate that a four digit year value is provided
'''

import re

from wtforms.validators import ValidationError


class EmailValidator:
    # Largely copied from https://github.com/alphagov/notifications-utils/blob/\
    #   67889886ec1476136d12e7f32787a7dbd0574cc2/notifications_utils/recipients.py
    #
    # regexes for use in validate_email_address.
    # invalid local chars - whitespace, quotes and apostrophes, semicolons and colons, GBP sign
    # Note: Normal apostrophe eg `Firstname-o'surname@domain.com` is allowed.
    _INVALID_LOCAL_CHARS = r"\s\",;:@£“”‘’"
    _email_regex = re.compile(r'^[^{}]+@([^.@][^@]+)$'.format(_INVALID_LOCAL_CHARS))
    _hostname_part = re.compile(r'^(xn-|[a-z0-9]+)(-[a-z0-9]+)*$', re.IGNORECASE)
    _tld_part = re.compile(r'^([a-z]{2,63}|xn--([a-z0-9]+-)*[a-z0-9]+)$', re.IGNORECASE)

    def __init__(self, message="Please enter a valid email address."):
        self.message = message

    def __call__(self, form, field):
        # Largely a straight copy from https://github.com/alphagov/notifications-utils/blob/\
        #   67889886ec1476136d12e7f32787a7dbd0574cc2/notifications_utils/recipients.py#L439 onwards so that we have
        # validity-parity with Notify and minimise nasty surprises once we attempt to send an email to this address via
        # Notify and only find out it won't be accepted once it's too late to give the user a sane validation message

        # almost exactly the same as by https://github.com/wtforms/wtforms/blob/master/wtforms/validators.py,
        # with minor tweaks for SES compatibility - to avoid complications we are a lot stricter with the local part
        # than neccessary - we don't allow any double quotes or semicolons to prevent SES Technical Failures
        email_address = (field.data or "").strip()
        match = re.match(self._email_regex, email_address)

        # not an email
        if not match:
            raise ValidationError(self.message)

        hostname = match.group(1)
        # don't allow consecutive periods in domain names
        if '..' in hostname:
            raise ValidationError(self.message)

        # idna = "Internationalized domain name" - this encode/decode cycle converts unicode into its accurate ascii
        # representation as the web uses. '例え.テスト'.encode('idna') == b'xn--r8jz45g.xn--zckzah'
        try:
            hostname = hostname.encode('idna').decode('ascii')
        except UnicodeError:
            raise ValidationError(self.message)

        parts = hostname.split('.')

        if len(hostname) > 253 or len(parts) < 2:
            raise ValidationError(self.message)

        for part in parts:
            if not part or len(part) > 63 or not self._hostname_part.match(part):
                raise ValidationError(self.message)

        # if the part after the last . is not a valid TLD then bail out
        if not self._tld_part.match(parts[-1]):
            raise ValidationError(self.message)

        return


class GreaterThan:
    """
    Compares the values of two fields.

    :param fieldname:
        The name of the other field to compare to.

    :param message:
        Error message to raise in case of a validation error.
    """
    def __init__(self, fieldname, message=None):
        self.fieldname = fieldname
        self.message = message

    def __call__(self, form, field):
        try:
            other = form[self.fieldname]
        except KeyError:
            raise ValidationError(field.gettext("Invalid field name '%s'." % self.fieldname))
        if other.data and not field.data > other.data:
            d = {
                'other_label': hasattr(other, 'label') and other.label.text or self.fieldname,
                'other_name': self.fieldname
            }
            message = self.message
            if message is None:
                message = field.gettext('Field must be greater than %(other_name)s.')

            raise ValidationError(message % d)


class FourDigitYear:
    """
    Validates that a `DateField`'s year field has a four digit year value.

    :param message:
        Error message to raise in case of a validation error.
    """
    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        try:
            digits = len(field.form_field.year.raw_data[0])
        except IndexError:
            digits = 0

        if not digits == 4:
            message = self.message
            if message is None:
                message = field.gettext("Year must be YYYY.")

            raise ValidationError(message)
