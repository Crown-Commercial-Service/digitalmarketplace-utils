import pytest

import wtforms

from dmutils.forms.fields import DMRadioField

_choices = (
    ('yes', 'Yes', 'A positive response.'),
    ('no', 'No', 'A negative response.'),
)


class RadioForm(wtforms.Form):
    field = DMRadioField(choices=_choices)


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
