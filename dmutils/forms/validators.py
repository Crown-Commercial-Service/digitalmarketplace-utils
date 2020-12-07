'''
Validators for WTForms used in the Digital Marketplace frontend

EmailValidator -- validate that a string is a valid email address
GreaterThan -- compare the values of two fields
FourDigitYear -- validate that a four digit year value is provided
'''

from wtforms.validators import ValidationError

from dmutils.email.helpers import validate_email_address


class EmailValidator:
    """
    Tests whether a string is a valid email address.

    :param message:
        Error message to raise in case of a validation error.
    """

    def __init__(self, message="Please enter a valid email address."):
        self.message = message

    def __call__(self, form, field):
        if not validate_email_address(field.data):
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
            raise ValidationError(
                field.gettext("Invalid field name '%s'." % self.fieldname)
            )
        if field.data is None or other.data is None:
            return
        elif field.data > other.data:
            return

        d = {
            "other_label": hasattr(other, "label")
            and other.label.text
            or self.fieldname,
            "other_name": self.fieldname,
        }
        message = self.message
        if message is None:
            message = field.gettext("Field must be greater than %(other_name)s.")

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
