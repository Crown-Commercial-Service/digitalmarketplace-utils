from datetime import date

import pytest
import mock

from wtforms.validators import ValidationError

import dmutils.forms.validators
from dmutils.forms.validators import (
    GreaterThan,
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
