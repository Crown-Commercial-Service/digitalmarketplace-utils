import pytest

import wtforms

from dmutils.forms.fields import DMBooleanField
from dmutils.forms.widgets import DMSelectionButtonBase


class BooleanForm(wtforms.Form):
    field = DMBooleanField()


@pytest.fixture
def form():
    return BooleanForm()


def test_value_is_a_list(form):
    assert isinstance(form.field.value, list)


def test_value_is_empty_list_if_there_is_no_selection(form):
    assert form.field.value == []


def test_can_be_used_with_a_different_kind_of_selection_button():
    class BooleanForm(wtforms.Form):
        field = DMBooleanField(widget=DMSelectionButtonBase(type="boolean"))

    form = BooleanForm()

    assert form.field.widget.type == "boolean"
