from collections import OrderedDict

import pytest
import wtforms

import dmutils.forms.fields as fields
from dmutils.forms.errors import get_errors_from_wtform, govuk_errors


@pytest.mark.parametrize("dm_errors,expected_output", (
    ({}, OrderedDict()),
    (
        OrderedDict((
            ("haddock", {
                "input_name": "haddock",
                "question": "What was that, Joe?",
                "message": "Too numerous to be enumerated",
            },),
            ("pollock", {},),
            ("flounder", {
                "input_name": "flounder",
                "question": "Anything strange or wonderful, Joe?",
                "roach": "halibut",
            },),
        )),
        OrderedDict((
            ("haddock", {
                "input_name": "haddock",
                "question": "What was that, Joe?",
                "message": "Too numerous to be enumerated",
                "text": "Too numerous to be enumerated",
                "href": "#input-haddock",
                "errorMessage": {"text": "Too numerous to be enumerated"},
            },),
            ("pollock", {},),
            ("flounder", {
                "input_name": "flounder",
                "question": "Anything strange or wonderful, Joe?",
                "roach": "halibut",
                "text": "Anything strange or wonderful, Joe?",
                "href": "#input-flounder",
                "errorMessage": {"text": "Anything strange or wonderful, Joe?"},
            },),
        )),
    ),
))
def test_govuk_errors(dm_errors, expected_output):
    assert govuk_errors(dm_errors) == expected_output


class RadiosForm(wtforms.Form):
    radios = fields.DMRadioField(
        choices=[("Yes", "yes"), ("No", "no")],
        validators=[wtforms.validators.InputRequired()],
    )


class BooleanForm(wtforms.Form):
    boolean = fields.DMBooleanField(
        validators=[wtforms.validators.DataRequired()]
    )


class TextInputForm(wtforms.Form):
    text_input = fields.DMStringField(
        validators=[wtforms.validators.Length(max=5)]
    )


@pytest.mark.parametrize("form_class, data, expected_error", [
    (RadiosForm, {}, {"radios": {
        "href": "#input-radios-1",
        "text": "This field is required.",
        "errorMessage": {"text": "This field is required."},

        "input_name": "radios",
        "question": "Radios",
        "message": "This field is required.",
    }}),
    (BooleanForm, {"boolean": ""}, {"boolean": {
        "href": "#input-boolean-1",
        "text": "This field is required.",
        "errorMessage": {"text": "This field is required."},

        "input_name": "boolean",
        "question": "Boolean",
        "message": "This field is required.",
    }}),
    (TextInputForm, {"text_input": "Hello World"}, {"text_input": {
        "href": "#input-text_input",
        "text": "Field cannot be longer than 5 characters.",
        "errorMessage": {"text": "Field cannot be longer than 5 characters."},

        "input_name": "text_input",
        "question": "Text Input",
        "message": "Field cannot be longer than 5 characters.",
    }}),
])
def test_get_errors_from_wtform(form_class, data, expected_error):
    form = form_class(data=data)
    form.validate()
    assert get_errors_from_wtform(form) == expected_error
