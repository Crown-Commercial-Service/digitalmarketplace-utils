import pytest
import wtforms

import dmutils.forms.fields
from dmutils.forms.fields import DMDateField


@pytest.fixture(params=dmutils.forms.fields.__all__)
def field_class(request):
    return getattr(dmutils.forms.fields, request.param)


def test_field_can_be_class_property(field_class):
    class TestForm(wtforms.Form):
        field = field_class()

    assert TestForm()


def test_field_has_hint_property(field_class):
    class TestForm(wtforms.Form):
        field = field_class(hint='Hint text.')

    form = TestForm()
    assert form.field.hint == 'Hint text.'


def test_field_class_can_have_default_hint():
    class TestField(dmutils.forms.fields.DMFieldMixin, wtforms.Field):
        hint = "Hint text."

    class TestForm(wtforms.Form):
        field = TestField()

    form = TestForm()
    assert form.field.hint == "Hint text."


def test_field_has_question_advice_property(field_class):
    class TestForm(wtforms.Form):
        field = field_class(question_advice="Advice text.")

    form = TestForm()
    assert form.field.question_advice == "Advice text."


def test_field_class_can_have_default_question_advice():
    class TestField(dmutils.forms.fields.DMFieldMixin, wtforms.Field):
        question_advice = "Advice text."

    class TestForm(wtforms.Form):
        field = TestField()

    form = TestForm()
    assert form.field.question_advice == "Advice text."


def test_field_class_can_have_type():
    class TestField(dmutils.forms.fields.DMFieldMixin, wtforms.Field):
        type = "test_field"

    class TestForm(wtforms.Form):
        field = TestField()

    form = TestForm()
    assert form.field.type == "test_field"


def test_field_href_is_prefixed_with_input_prefix(field_class):
    class TestForm(wtforms.Form):
        field = field_class()

    form = TestForm()

    assert form.field.href.startswith("input-")


def test_field_href_is_not_prefixed_with_input_prefix_if_specified(field_class):
    class TestForm(wtforms.Form):
        field = field_class(id="field")

    form = TestForm()

    assert form.field.href == "field"


def test_date_field_href_is_suffixed_with_first_field_if_no_error():
    class TestForm(wtforms.Form):
        field = DMDateField()

    form = TestForm()

    assert form.field.href == "input-field-day"


@pytest.mark.parametrize("field_class", (
    dmutils.forms.fields.DMRadioField, dmutils.forms.fields.DMBooleanField
))
def test_selection_field_href_is_suffixed_with_number(field_class):
    class TestForm(wtforms.Form):
        field = field_class()

    form = TestForm()

    assert form.field.href == "input-field-1"


@pytest.mark.parametrize("field_class", (
    dmutils.forms.fields.DMRadioField, dmutils.forms.fields.DMBooleanField
))
def test_selection_field_href_is_not_suffixed_with_number_if_id_is_specified(field_class):
    class TestForm(wtforms.Form):
        field = field_class(id="field")

    form = TestForm()

    assert form.field.href == "field"


def test_dm_date_field_proxies_access_to_form_field_fields():
    class TestForm(wtforms.Form):
        date = DMDateField("Date")

    field = TestForm().date

    assert field.day == field.form_field.day
    assert field.month == field.form_field.month
    assert field.year == field.form_field.year


def test_dm_date_field_copies_errors_to_form_field_fields():
    from wtforms.validators import ValidationError

    def test_validator(form, field):
        raise ValidationError("Validation error")

    class TestForm(wtforms.Form):
        date = DMDateField("Date", validators=[test_validator])

    form = TestForm()
    form.validate()

    assert "Validation error" in form.date.day.errors
    assert "Validation error" in form.date.month.errors
    assert "Validation error" in form.date.year.errors
