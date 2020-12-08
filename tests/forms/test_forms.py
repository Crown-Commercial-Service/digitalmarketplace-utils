"""Test tools in this module working together"""

import pytest
import wtforms
from werkzeug.datastructures import MultiDict

from dmutils.forms.fields import DMDateField
from dmutils.forms.validators import DateValidator, GreaterThan


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


@pytest.mark.parametrize("start_date, end_date, validates, greater_than_error", (
    ((2020, 1, 1), (2001, 1, 1), False, True),
    (("", "", ""), (2020, 12, 1), False, False),
    ((2020, 1, 1), ("", "", ""), False, False),
    (("", "", ""), ("", "", ""), False, False),
    ((2020, 1, 1), (2021, 1, 1), True, False),
    ((2020, 1, 1), (2020, 12, 1), True, False),
))
def test_dm_date_field_with_greater_than_validator(
    start_date, end_date, validates, greater_than_error
):
    class TestForm(wtforms.Form):
        start_date = DMDateField("Start date")
        end_date = DMDateField("End date", validators=[GreaterThan("start_date")])

    form = TestForm(MultiDict({
        "start_date-year": str(start_date[0]),
        "start_date-month": str(start_date[1]),
        "start_date-day": str(start_date[2]),
        "end_date-year": str(end_date[0]),
        "end_date-month": str(end_date[1]),
        "end_date-day": str(end_date[2]),
    }))

    assert form.validate() is validates

    assert (
        "Field must be greater than start_date." in form.end_date.errors
    ) == greater_than_error

    for subfield in form.end_date.form_field:
        assert (
            "Field must be greater than start_date." in subfield.errors
        ) == greater_than_error, (
            f"date input field '{subfield.name}' {'is missing' if greater_than_error else 'has unexpected'} errors"
        )
