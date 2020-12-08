"""
Validators for WTForms used in the Digital Marketplace frontend

EmailValidator -- validate that a string is a valid email address
GreaterThan -- compare the values of two fields
FourDigitYear -- validate that a four digit year value is provided
DateValidator -- Error messages for a date input
"""

import datetime
from typing import Any, Dict, Optional

from wtforms.validators import StopValidation, ValidationError

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


class DateValidator:
    """Error messages for a date input

    Implements the guidance in [1].

    Instead of taking a `message` DateValidator has two properties,
    `whatever_it_is` and `Whatever_it_is`, which are stand-ins for whatever it
    is the question is asking the user for. `whatever_it_is` is used in the
    middle of a sentence, and should include a participle: for instance, if you
    are asking for the date when a buyer needs a supplier to start work,
    `whatever_it_is` should be `the start date`. `Whatever_it_is` (with a
    capital 'W') is used at the beginning of the sentence, and should not
    include a participle. If `Whatever_it_is` is not provided it will be
    generated from `whatever_it_is` by dropping the first word and then
    capitalising the first letter; in our previous example, for instance,
    `Whatever_it_is` would be `Start date`.

    Alternatively you can provide the error messages desired directly; there
    are three different error messages that can be raised by this validator:

    - nothing_is_entered_error_message
    - date_is_incomplete_error_message
    - date_entered_cant_be_correct_error_message

    The string for `date_is_incomplete_error_message` also includes a
    placeholder for `whatever_is_missing`, in format string syntax.

    [1]:  https://design-system.service.gov.uk/components/date-input/#error-messages
    """

    def __init__(
        self,
        whatever_it_is,
        Whatever_it_is=None,
        *,
        nothing_is_entered_error_message=None,
        date_is_incomplete_error_message=None,
        date_entered_cant_be_correct_error_message=None,
    ):
        self.whatever_it_is = whatever_it_is
        if whatever_it_is and not Whatever_it_is:
            _, rest = whatever_it_is.split(maxsplit=1)
            self.Whatever_it_is = rest[0].upper() + rest[1:]
        else:
            self.Whatever_it_is = Whatever_it_is

        self.nothing_is_entered_error_message = (
            nothing_is_entered_error_message or "Enter {whatever_it_is}"
        )
        self.date_is_incomplete_error_message = (
            date_is_incomplete_error_message
            or "{Whatever_it_is} must include a {whatever_is_missing}"
        )
        self.date_entered_cant_be_correct_error_message = (
            date_entered_cant_be_correct_error_message
            or "{Whatever_it_is} must be a real date"
        )

    def _error(self, error, fields, **kwargs):
        e = ValueError(self.format_error_message(error, **kwargs))
        e.error = error

        # Design System guidance is that if more than one field has an error
        # we should highlight all fields.
        if len(fields) > 1:
            e.fields = {"year", "month", "day"}
        else:
            e.fields = fields

        return e

    def format_error_message(self, error, **kwargs):
        return getattr(self, error + "_error_message").format(
            whatever_it_is=self.whatever_it_is,
            Whatever_it_is=self.Whatever_it_is,
            **kwargs,
        )

    def validate_input(self, raw_data: Dict[str, Any]):
        """Check that year month and day are in `raw_data` and are all integers

        :raises ValueError:
        """
        if not any(raw_data.values()):
            raise self._error(
                "nothing_is_entered",
                set(raw_data.keys()),
            )
        elif not all(raw_data.values()):
            missing = list(sorted(
                name
                for name, value in raw_data.items()
                if not value
            ))
            whatever_is_missing = " and ".join(missing)
            raise self._error(
                "date_is_incomplete",
                set(missing),
                whatever_is_missing=whatever_is_missing,
            )

        def int_or_none(s: Any) -> Optional[int]:
            if not s:
                return None
            try:
                return int(s)
            except ValueError:
                return None

        data = {name: int_or_none(value) for name, value in raw_data.items()}

        if not all(data.values()):
            raise self._error(
                "nothing_is_entered",
                {k for k, v in data.items() if v is None},
            )

    def validate_data(self, data: Dict[str, int]):
        """Check that year month and day in `data` make a valid date

        :raises ValueError:
        """
        year, month, day = data["year"], data["month"], data["day"]

        invalid = set()
        if not (1 <= day and day <= 31):
            invalid.add("day")
        if not (1 <= month and month <= 12):
            invalid.add("month")
        if not (datetime.MINYEAR <= year and year <= datetime.MAXYEAR):
            invalid.add("year")

        if not invalid:
            try:
                datetime.date(year, month, day)
            except ValueError:
                # assume that since we've eliminated other possibilities
                # above it must be that the day given is outside the number
                # of days in the given month and year
                # see https://docs.python.org/3.6/library/datetime.html#datetime.date
                invalid.add("day")

        if invalid:
            raise self._error(
                "date_entered_cant_be_correct",
                invalid,
            )

    def validate_date(self, year, month, day):
        self.validate_input({"year": year, "month": month, "day": day})
        self.validate_data({"year": int(year), "month": int(month), "day": int(day)})

    def __call__(self, form, field):
        """WTForms date validator for DMDateField"""
        try:
            self.validate_date(
                field.form_field.year.data,
                field.form_field.month.data,
                field.form_field.day.data,
            )
        except ValueError as e:
            error_message = str(e)
            error_fields = getattr(e, "fields", {"year", "month", "day"})

            # remove processing errors from field
            field.errors[:] = []

            # add errors to specific form field fields
            for form_field_field in error_fields:
                getattr(field.form_field, form_field_field).errors = [error_message]

            validation_error = StopValidation(error_message)
            validation_error.fields = error_fields
            raise validation_error
