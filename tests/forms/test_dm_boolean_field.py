import pytest

import wtforms

from dmutils.forms.fields import DMBooleanField


class BooleanForm(wtforms.Form):
    field = DMBooleanField()


@pytest.fixture
def form():
    return BooleanForm()


def test_value_is_a_list(form):
    assert isinstance(form.field.value, list)


def test_value_is_empty_list_if_there_is_no_selection(form):
    assert form.field.value == []
