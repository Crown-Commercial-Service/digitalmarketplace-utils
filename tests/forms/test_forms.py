"""Test things in dmutils.forms working together"""

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
