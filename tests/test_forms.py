from collections import OrderedDict
from itertools import product

from flask_wtf import FlaskForm
from wtforms.fields import StringField
from wtforms.validators import DataRequired, Length, Optional
from werkzeug.datastructures import ImmutableMultiDict
import pytest

from dmutils.forms import EmailField, remove_csrf_token, get_errors_from_wtform


class EmailFieldFormatTestForm(FlaskForm):
    test_email = EmailField("An Electronic Mailing Address")


class MultipleFieldFormatTestForm(FlaskForm):
    test_one = EmailField("Email address")
    test_two = StringField("Test Two", validators=[DataRequired(message="Enter text.")])
    test_three = StringField("Test Three", validators=[Length(min=100, max=100, message="Bad length.")])
    test_four = StringField("Test Four", validators=[DataRequired(message="Enter text.")])


email_address_parametrization = ("email_address", (
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
    "a.b@strangeface.fellowthatsolike_sawhimbefore.chapwithawen",
    "-@-.-",
    "123@321.12",
    "x@y.z",
))


class TestEmailFieldFormat(object):
    @pytest.mark.parametrize(*email_address_parametrization)
    def test_invalid_emails(self, app, email_address):
        with app.app_context():
            form = EmailFieldFormatTestForm(
                formdata=ImmutableMultiDict((
                    ("test_email", email_address,),
                )),
                meta={'csrf': False},
            )

            assert form.validate() is False
            assert "test_email" in form.errors

    @pytest.mark.parametrize("email_address", (
        "x@y.zz",
        "-second@wat.ch",
        "123@321.go",
        "   helter-Skelter_pelter-Welter@Who.do-you.call.him\t",
        "a..............b@strangeface.fellowthatsolike-sawhimbefore.Chapwithawen",
        ".man_in_the_street.@other.man.in.the.street   \n",
    ))
    def test_valid_emails(self, app, email_address):
        with app.app_context():
            form = EmailFieldFormatTestForm(
                formdata=ImmutableMultiDict((
                    ("test_email", email_address,),
                )),
                meta={'csrf': False},
            )

            assert form.validate()
            assert form.data["test_email"] == email_address.strip()

    def test_default_email_length(self, app):
        email_address = 'r' + 'e' * 498 + 'ally@long.com'  # 512 chars long
        with app.app_context():
            form = EmailFieldFormatTestForm(
                formdata=ImmutableMultiDict((
                    ("test_email", email_address,),
                )),
                meta={'csrf': False},
            )

            assert not form.validate()
            assert form.errors == {'test_email': ['Please enter an email address under 512 characters.']}

    def test_default_length_and_message_can_be_overridden(self, app):
        class OverrideDefaultValidatorTestForm(FlaskForm):
            test_email = EmailField(
                "An Electronic Mailing Address",
                validators=[Length(max=11, message='Only really short emails please')]
            )

        email_address = 'rlly@shrt.cm'  # 12 chars long
        with app.app_context():
            form = OverrideDefaultValidatorTestForm(
                formdata=ImmutableMultiDict((
                    ("test_email", email_address,),
                )),
                meta={'csrf': False},
            )

            assert not form.validate()
            assert form.errors == {'test_email': ['Only really short emails please']}


class EmailFieldCombinationTestForm(FlaskForm):
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
    _valid_address = "v@l.id"

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
                meta={'csrf': False},
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


class TestRemoveCsrfToken:
    def test_csrf_token_removed_if_present(self):
        data = {'key': 'value', 'key2': 'value2', 'csrf_token': '123tgredsca2345ywt34rwe'}
        cleaned_data = remove_csrf_token(data)
        assert 'csrf_token' not in cleaned_data

    def test_original_data_not_mutated_by_remove_csrf_token(self):
        data = {'key': 'value', 'key2': 'value2', 'csrf_token': '123tgredsca2345ywt34rwe'}
        remove_csrf_token(data)
        assert 'csrf_token' in data

    def test_silently_passes_if_csrf_token_not_present(self):
        data = {'key': 'value', 'key2': 'value2'}
        cleaned_data = remove_csrf_token(data)
        assert cleaned_data == data


class TestFormatWTFormErrors:
    def test_empty_list_if_no_errors(self, app):
        with app.app_context():
            form = EmailFieldFormatTestForm(
                formdata=ImmutableMultiDict((
                    ("test_email", 'test@email.com',),
                )),
                meta={'csrf': False},
            )

            assert form.validate() is True
            assert not form.errors
            assert get_errors_from_wtform(form) == OrderedDict()

    @pytest.mark.parametrize(*email_address_parametrization)
    def test_errors_are_formatted(self, app, email_address):
        with app.app_context():
            form = EmailFieldFormatTestForm(
                formdata=ImmutableMultiDict((
                    ("test_email", email_address,),
                )),
                meta={'csrf': False},
            )

            assert form.validate() is False
            assert form.errors
            assert get_errors_from_wtform(form) == OrderedDict([(
                'test_email',
                {
                    'input_name': 'test_email',
                    'question': "An Electronic Mailing Address",
                    'message': 'Please enter a valid email address.'
                }
            )])

    def test_errors_retain_ordering(self, app):
        with app.app_context():
            form = MultipleFieldFormatTestForm(
                formdata=ImmutableMultiDict((
                    ('test_email', 'my bad email',),
                    ('test_two', 'some text, good'),
                    ('test_three', 'not enough text'),
                    ('test_four', ''),
                )),
                meta={'csrf': False},
            )

            assert form.validate() is False
            assert form.errors
            assert get_errors_from_wtform(form) == OrderedDict(
                [
                    ('test_one', {'input_name': 'test_one', 'question': "Email address",
                                  'message': 'Please enter a valid email address.'}),
                    ('test_three', {'input_name': 'test_three', 'question': "Test Three", 'message': 'Bad length.'}),
                    ('test_four', {'input_name': 'test_four', 'question': "Test Four", 'message': 'Enter text.'}),
                ]
            )
