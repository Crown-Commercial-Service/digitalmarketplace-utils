from itertools import product

from flask.ext.wtf import Form
from wtforms.validators import DataRequired, Optional
from werkzeug.datastructures import ImmutableMultiDict
import pytest

from dmutils.forms import EmailField


class EmailFieldFormatTestForm(Form):
    test_email = EmailField("An Electronic Mailing Address")


class TestEmailFieldFormat(object):
    @pytest.mark.parametrize("email_address", (
        "oiufewnew",
        "",
        None,
        "cissy@edy@how.th",
        "@major.tweedy",
        "ned.l?mbert@x.",
        "bu ck@41.com",
        "malachi@.o.flynn.net",
        "@",
        "first.w@t.ch.",
        "second.w@t..h",
    ))
    def test_invalid_emails(self, app, email_address):
        with app.app_context():
            form = EmailFieldFormatTestForm(
                formdata=ImmutableMultiDict((
                    ("test_email", email_address,),
                )),
                csrf_enabled=False,
            )

            assert form.validate() is False
            assert "test_email" in form.errors

    @pytest.mark.parametrize("email_address", (
        "x@y.z",
        "-second@wat.ch",
        "123@321.12",
        "   helter-Skelter_pelter-Welter@Who.do-you.call.him\t",
        "a..............b@strangeface.fellowthatsolike_sawhimbefore.Chapwithawen",
        ".man_in_the_street.@other.man.in.the.street   \n",
        "-@-.-",  # probably not actually valid
    ))
    def test_valid_emails(self, app, email_address):
        with app.app_context():
            form = EmailFieldFormatTestForm(
                formdata=ImmutableMultiDict((
                    ("test_email", email_address,),
                )),
                csrf_enabled=False,
            )

            assert form.validate()
            assert form.data["test_email"] == email_address.strip()


class EmailFieldCombinationTestForm(Form):
    required_email = EmailField(
        "Required Electronic Mailing Address",
        validators=[DataRequired(message="No really, we want this")],
    )
    optional_email = EmailField(
        "Optional Electronic Mailing Address",
        validators=[Optional()],
    )
    unspecified_email = EmailField("Voluntary Electronic Mailing Address")


class TestEmailFieldCombination(object):
    _invalid_address = "@inv@li..d.."
    _valid_address = "v@li.d"

    _possibilities = (_valid_address, _invalid_address, "")

    @pytest.mark.parametrize(
        "required_field_email,optional_field_email,unspecified_field_email",
        product(_possibilities, repeat=3),
    )
    def test(self, app, required_field_email, optional_field_email, unspecified_field_email):
        with app.app_context():
            form = EmailFieldCombinationTestForm(
                formdata=ImmutableMultiDict((
                    ("required_email", required_field_email,),
                    ("optional_email", optional_field_email,),
                    ("unspecified_email", unspecified_field_email,),
                )),
                csrf_enabled=False,
            )

            assert form.validate() is bool(
                required_field_email == self._valid_address and
                optional_field_email != self._invalid_address and
                unspecified_field_email == self._valid_address
            )

            if required_field_email == self._invalid_address:
                assert form.errors["required_email"] == ["Please enter a valid email address."]
            elif required_field_email == "":
                assert form.errors["required_email"] == ["No really, we want this"]

            if optional_field_email == self._invalid_address:
                assert form.errors["optional_email"] == ["Please enter a valid email address."]

            if unspecified_field_email in (self._invalid_address, ""):
                assert form.errors["unspecified_email"] == ["Please enter a valid email address."]
