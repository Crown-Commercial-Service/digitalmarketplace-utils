import pytest

import wtforms

from dmutils.forms.fields import DMRadioField

_options = [
    {
        "label": "Yes",
        "value": "yes",
        "description": "A positive response."
    },
    {
        "label": "No",
        "value": "no",
        "description": "A negative response."
    }
]


class RadioForm(wtforms.Form):
    field = DMRadioField(options=_options)


@pytest.fixture
def form():
    return RadioForm()


def test_dm_radio_field_has_options_property(form):
    assert form.field.options


def test_options_is_a_list_of_dicts(form):
    assert isinstance(form.field.options, list)
    assert all(isinstance(option, dict) for option in form.field.options)


def test_an_option_can_have_a_description(form):
    assert form.field.options[0]['description']


def test_constructor_accepts_choices_parameter():
    class RadioForm(wtforms.Form):
        field = DMRadioField(choices=[("yes", "Yes"), ("no", "No")])

    form = RadioForm()

    assert form.field.choices


def test_iter_choices(form):
    assert list(form.field.iter_choices()) == [("yes", "Yes", False), ("no", "No", False)]
