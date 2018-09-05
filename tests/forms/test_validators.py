
import pytest
import mock

from wtforms.validators import ValidationError

import dmutils.forms.validators


@pytest.fixture
def form():
    return mock.Mock()


@pytest.fixture
def field():
    return mock.Mock()


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
