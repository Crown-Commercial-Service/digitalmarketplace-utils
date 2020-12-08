from datetime import date

import pytest
import mock

from wtforms.validators import StopValidation, ValidationError

import dmutils.forms.validators
from dmutils.forms.validators import (
    GreaterThan,
    DateValidator,
)


@pytest.fixture
def form():
    return mock.MagicMock()


@pytest.fixture
def field(form):
    return form.field


@pytest.mark.parametrize(
    "invalid_email_address", (
        None,
        "",
        "foobar",
        "bob@blob",
        "cecilia.payne@sub-domain..domain.example",
        "annie-jump-cannon@harvard-computers.example;henrietta-swan-leavitt@harvard-computers.example",
        "Please send emails to b o b at b l o b dot example",
    )
)
def test_email_validator_raises_validation_error_on_an_invalid_email_address(form, field, invalid_email_address):
    validator = dmutils.forms.validators.EmailValidator()
    field.data = invalid_email_address

    with pytest.raises(ValidationError):
        validator(form, field)


@pytest.mark.parametrize(
    "email_address", (
        "bob@blob.com",
        "test@example.com",
        "user@user.marketplace.team",
        "annie.j.easley@example.test",
        "books@bücher.example",
        "मीनाक्षी@email.example",
        "我買@屋企.香港",
    )
)
def test_email_validator_does_not_raise_on_a_valid_email_address(form, field, email_address):
    validator = dmutils.forms.validators.EmailValidator()
    field.data = email_address

    validator(form, field)


class TestGreaterThan:
    @pytest.fixture
    def form(self, form):
        form.other = form["other"]
        return form

    @pytest.fixture
    def validator(self):
        return GreaterThan("other")

    @pytest.mark.parametrize("a, b", (
        # a should be less than b
        # this test will test both ways round
        #
        (0, 1),
        (-1, 0),
        (10, 100),
        # doesn't have to be int or even number, any comparable will do
        (1.0, 1.1),
        (date(2000, 1, 1), date(2020, 1, 1)),
        ("2000-01-01", "2020-01-01"),
    ))
    def test_greater_than_raises_validation_error_if_field_data_is_not_greater_than_other(
        self, form, validator, a, b
    ):
        assert a < b, "this test expects a to be less than b"

        # if field data is less than other data raises ValidationError
        form.field.data = a
        form.other.data = b

        with pytest.raises(ValidationError):
            validator(form, form.field)

        # otherwise returns without error
        form.field.data = b
        form.other.data = a

        assert validator(form, form.field) is None

    @pytest.mark.parametrize("a, b", (
        (10, None),
        (None, 10),
        (None, None),
    ))
    def test_returns_if_field_or_other_are_none(
        self, form, validator, a, b,
    ):
        form.field.data = a
        form.other.data = b

        assert validator(form, form.field) is None


class TestDateValidator:
    @pytest.fixture
    def validate_date(self):
        return DateValidator("a date").validate_date

    @pytest.fixture
    def validator(self):
        return DateValidator("a date")

    def test_date_error_message_returns_none_for_valid_date(self, validate_date):
        assert validate_date(2020, 11, 27) is None
        assert validate_date(2004, 2, 29) is None

    @pytest.mark.parametrize("date", (
        ("2020", 1, 26),
        (2020, "1", 26),
        (2020, 1, "26"),
        ("2020", "1", "26"),
        ("2020", "01", "26"),
        ("2020", "01", "06"),
    ))
    def test_date_error_message_can_handle_strings(self, validate_date, date):
        assert validate_date(*date) is None

    @pytest.mark.parametrize("data, invalid_fields", (
        ((None, None, None), {"year", "month", "day"}),
        (("", "", ""), {"year", "month", "day"}),
        (("foo", "bar", "baz"), {"year", "month", "day"}),
        (("1.0", "1.0", "1.0"), {"year", "month", "day"}),
        (("2020", "1", "baz"), {"day"}),
        (("2020", "1", "1.0"), {"day"}),
    ))
    def test_date_error_message_raises_nothing_is_entered_message_if_data_is_empty_or_not_int(
        self, validate_date, data, invalid_fields
    ):
        with pytest.raises(ValueError) as e:
            validate_date(*data)

        assert str(e.value) == "Enter a date"
        assert e.value.error == "nothing_is_entered"
        assert e.value.fields == invalid_fields

    @pytest.mark.parametrize("data, invalid_fields, error_message", (
        # 'Highlight the day, month or year field where the information is missing'.
        ((2020, 1, ""), {"day"}, "Date must include a day"),
        ((2020, "", 1), {"month"}, "Date must include a month"),
        (("", 1, 1), {"year"}, "Date must include a year"),
        # 'If more than one field is missing information, highlight the date input as a whole'.
        ((2020, "", ""), {"day", "month", "year"}, "Date must include a day and month"),
        (("", 1, ""), {"day", "month", "year"}, "Date must include a day and year"),
        (("", "", 1), {"day", "month", "year"}, "Date must include a month and year"),
    ))
    def test_date_error_message_raises_date_is_incomplete_message_for_missing_data(
        self, validate_date, data, invalid_fields, error_message
    ):
        with pytest.raises(ValueError) as e:
            validate_date(*data)

        assert str(e.value) == error_message
        assert e.value.error == "date_is_incomplete"
        assert e.value.fields == invalid_fields

    @pytest.mark.parametrize("data, invalid_fields", (
        # 'Highlight the day, month or year field with the incorrect information'.
        ((2020, 13, 1), {"month"}),
        ((1999, 1, 310), {"day"}),
        ((2001, 2, 29), {"day"}),
        # 'Or highlight the date as a whole if there’s incorrect information in
        # more than one field, or it’s not clear which field is incorrect'.
        ((-19, 1, 310), {"day", "month", "year"}),
    ))
    def test_data_error_message_raises_date_entered_cant_be_correct_message_for_invalid_date(
        self, validate_date, data, invalid_fields
    ):
        with pytest.raises(ValueError) as e:
            validate_date(*data)

        assert str(e.value) == "Date must be a real date"
        assert e.value.error == "date_entered_cant_be_correct"
        assert e.value.fields == invalid_fields

    def test_raises_validation_error_for_invalid_data(self, form, field, validator):
        field.form_field.year.data = None
        field.form_field.month.data = None
        field.form_field.day.data = None
        field.errors = []

        with pytest.raises(StopValidation) as e:
            validator(form, field)

        assert str(e.value) == "Enter a date"
        assert e.value.fields == {"year", "month", "day"}

    def test_does_not_raise_validation_error_for_valid_data(self, form, field, validator):
        field.form_field.year.data = 2020
        field.form_field.month.data = 1
        field.form_field.day.data = 26

        validator(form, field)
