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


@pytest.fixture(params=["yes", "no"])
def form_with_selection(request):
    return (RadioForm(data={"field": request.param}), request.param)


@pytest.fixture(params=["true", "false", "garbage", ""])
def form_with_invalid_selection(request):
    return (RadioForm(data={"field": request.param}), request.param)


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


def test_value_is_none_if_there_is_no_selection(form):
    assert form.field.value is None


def test_value_is_the_selected_radio_button(form_with_selection):
    form, selection = form_with_selection
    assert form.field.value == selection


def test_validation_succeeds_if_value_is_in_options(form_with_selection):
    form, _ = form_with_selection
    assert form.validate()


def test_validation_fails_if_value_is_not_in_options(form_with_invalid_selection):
    form, _ = form_with_invalid_selection
    assert not form.validate()


def test_iter_choices(form):
    assert list(form.field.iter_choices()) == [("yes", "Yes", False), ("no", "No", False)]


def test_iter_choices_with_selection():
    form = RadioForm(data={"field": "yes"})
    assert list(form.field.iter_choices()) == [("yes", "Yes", True), ("no", "No", False)]
    form = RadioForm(data={"field": "no"})
    assert list(form.field.iter_choices()) == [("yes", "Yes", False), ("no", "No", True)]
