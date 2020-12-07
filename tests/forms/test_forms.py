"""Test tools in this module working together"""

import pytest
import wtforms
from werkzeug.datastructures import MultiDict

from dmutils.forms.fields import DMDateField
from dmutils.forms.validators import DateValidator


def test_dm_date_field_with_date_validator():
    class TestForm(wtforms.Form):
        date = DMDateField("Date", validators=[DateValidator("a date")])

    form = TestForm()

    assert form.validate() is False
    assert form.date.errors == ["Enter a date"]

    form = TestForm(MultiDict({"date-year": "2020", "date-month": "01", "date-day": "26"}))

    assert form.validate() is True
    assert not form.date.errors


def test_dm_date_field_with_date_validator_includes_error_on_specific_fields():
    class TestForm(wtforms.Form):
        date = DMDateField("Date", validators=[DateValidator("a date")])

    form = TestForm(MultiDict({"date-year": "2020", "date-month": "01", "date-day": "33"}))

    assert form.validate() is False
    assert form.date.errors == ["Date must be a real date"]
    assert form.date.day.errors


@pytest.mark.parametrize("data, error_field", (
    ({"day": "01", "year": "2020"}, "month"),
    ({"day": "01", "month": "13"}, "month"),
    ({"day": "01", "month": "12"}, "year"),
    ({"day": "2", "month": "2", "year": "-1"}, "day"),
    ({"day": "30", "month": "2", "year": "2020"}, "day"),
    ({"day": "31", "month": "13", "year": "2020"}, "month"),
))
def test_date_field_href_is_suffixed_with_first_field_with_error_when_using_date_validator(
    data, error_field
):
    # this probably won't work with other validators

    class TestForm(wtforms.Form):
        field = DMDateField(validators=[DateValidator("a date")])

    form = TestForm(MultiDict({"field-day": "01", "field-year": "2020"}))
    form.validate()

    assert form.field.href == "input-field-month"
