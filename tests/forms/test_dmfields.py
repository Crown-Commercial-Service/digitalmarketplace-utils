
import pytest

import wtforms

import dmutils.forms.fields as dm_fields


@pytest.fixture(params=dm_fields.__all__)
def field_class(request):
    return getattr(dm_fields, request.param)


def test_field_can_be_class_property(field_class):
    class TestForm(wtforms.Form):
        field = field_class()

    assert TestForm()


def test_field_has_hint_property(field_class):
    class TestForm(wtforms.Form):
        field = field_class(hint='Hint text.')

    form = TestForm()
    assert form.field.hint == 'Hint text.'


def test_field_has_question_advice_property(field_class):
    class TestForm(wtforms.Form):
        field = field_class(question_advice="Advice text.")

    form = TestForm()
    assert form.field.question_advice == "Advice text."
