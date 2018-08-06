
import pytest

from werkzeug.datastructures import MultiDict
from wtforms import Form
from wtforms.validators import DataRequired, InputRequired

from dmutils.forms.fields import DMDateField
from dmutils.forms.validators import GreaterThan, FourDigitYear

import datetime


class DateForm(Form):
    date = DMDateField()


def _data_fromtuple(t, prefix='date'):
    keys = ('year', 'month', 'day')
    if prefix:
        keys = [f'{prefix}-{k}' for k in keys]
    return MultiDict(zip(keys, t))


def _data_fromdate(date, prefix='date'):
    t = date.isoformat().split('-')
    return _data_fromtuple(t, prefix)


@pytest.fixture(params=(
    ('2020', '12', '31'),
    ('1999', '12', '01'),
    ('2000', '01', '31'),
    ('2999', '01', '01'),
    ('2004', '2', '29'),
    ('0002', '02', '02'),
    ('0999', '01', '01'),
))
def valid_data(request):
    return _data_fromtuple(request.param)


@pytest.fixture(params=(
    _data_fromtuple(('year', 'month', 'day')),
    _data_fromtuple(('2020', '12', 'day')),
    _data_fromtuple(('2020', 'month', '31')),
    _data_fromtuple(('year', '12', '31')),
    _data_fromtuple(('2020', '2', '31')),
    _data_fromtuple(('31', '1', '2020')),
    _data_fromtuple(('2017', '2', '29')),
    _data_fromtuple(('2020', '2', '31')),
    _data_fromtuple(('1992', '', '26')),
    _data_fromtuple(('2020', '1', '')),
    _data_fromtuple(('', '01', '26')),
))
def invalid_data(request):
    return request.param


def test_create_date_field_with_validators():
    assert DMDateField(validators=[InputRequired(), DataRequired()])


def test_date_field_has__value_method():
    assert DMDateField._value


def test_date_field__value_method_returns_raw_data(invalid_data):
    form = DateForm(invalid_data)
    form.validate()
    assert form.date._value() == invalid_data.to_dict()


def test_date_field_data_is_date(valid_data):
    form = DateForm(valid_data)
    form.validate()
    assert isinstance(form.date.data, datetime.date)


def test_date_field_data_is_none_for_invalid_data(invalid_data):
    form = DateForm(invalid_data)
    form.validate()
    assert form.date.data is None


def test_valid_date_has_no_errors(valid_data):
    form = DateForm(valid_data)
    assert form.validate()
    assert form.errors == {}


def test_invalid_data_has_errors(invalid_data):
    form = DateForm(invalid_data)
    assert not form.validate()
    assert form.errors


def test_field_errors_is_list_of_strings(invalid_data):
    form = DateForm(invalid_data)
    form.validate()
    assert isinstance(form.date.errors, list)

    def isstr(x):
        return isinstance(x, str) and len(x) > 1

    assert all(map(isstr, form.date.errors))


def test_field_errors_before_validation_is_empty_collection():
    form = DateForm()
    assert len(form.date.errors) == 0


def test_field__value_before_input_is_empty_dict():
    form = DateForm()
    assert form.date._value() == {}


@pytest.mark.parametrize('message', (
    ('Not a valid date value'),
    ('You must answer this question with a valid date.'),
))
def test_data_required_error_message_matches_validation_message(invalid_data, message):
    class DateForm(Form):
        date = DMDateField(validators=[DataRequired(message)])

    form = DateForm(invalid_data)
    form.validate()
    assert form.date.errors[0] == message


@pytest.mark.parametrize('message', (
    ('This field is required.'),
    ('You must answer this question.'),
))
@pytest.mark.parametrize('empty', (
    _data_fromtuple(('', '', ''), prefix='invalid_prefix'),
    _data_fromtuple(('', '', '')),
    {},
))
def test_input_required_error_message_matches_validation_message(message, empty):
    class DateForm(Form):
        date = DMDateField(validators=[InputRequired(message)])

    empty = MultiDict(empty)
    form = DateForm(empty)
    form.validate()
    assert form.date.errors[0] == message


@pytest.mark.parametrize('message', (
    ('Not a valid date value'),
    ('You must answer this question with a valid date.'),
))
def test_error_message_with_multiple_validators(invalid_data, message):
    class DateForm(Form):
        date = DMDateField(validators=[InputRequired(), DataRequired(message)])

    form = DateForm(invalid_data)
    form.validate()
    assert form.date.errors[0] == message


def test_date_field_with_input_required_validator(valid_data):
    class DateForm(Form):
        date = DMDateField(validators=[InputRequired()])

    form = DateForm(valid_data)
    assert form.validate()


def test_date_field_with_data_required_validator(valid_data):
    class DateForm(Form):
        date = DMDateField(validators=[DataRequired()])

    form = DateForm(valid_data)
    assert form.validate()


@pytest.mark.parametrize('timedelta', (
    (datetime.timedelta()),
    (datetime.timedelta(days=1)),
    (datetime.timedelta(weeks=4)),
    (datetime.timedelta(days=30)),
    (datetime.timedelta(weeks=52)),
    (datetime.timedelta(days=365)),
))
def test_date_field_with_greater_than_validator(valid_data, timedelta):
    class DateForm(Form):
        past = DMDateField()
        date = DMDateField(validators=[GreaterThan('past')])

    # test validator being triggered
    future = DateForm(valid_data).date.data + timedelta
    future_data = _data_fromdate(future, 'past')
    invalid_data = valid_data.copy()
    invalid_data.update(future_data)

    form = DateForm(invalid_data)
    assert form.validate() is False
    assert form.errors

    if not timedelta:
        return

    # test validator not being triggered
    past = DateForm(valid_data).date.data - timedelta
    past_data = _data_fromdate(past, 'past')
    valid_data.update(past_data)

    form = DateForm(valid_data)
    assert form.validate()


def test_date_field_with_greater_than_validator_missing_past(valid_data):
    class DateForm(Form):
        past = DMDateField()
        date = DMDateField(validators=[GreaterThan('invalid_key')])

    form = DateForm(valid_data)
    assert not form.validate()
    assert form.date.errors


def test_date_field_with_greater_than_validator_key_error(valid_data):
    class DateForm(Form):
        past = DMDateField()
        date = DMDateField(validators=[GreaterThan('invalid_key')])

    future = DateForm(valid_data).date.data - datetime.timedelta(days=1)
    future_data = _data_fromdate(future, 'past')
    valid_data.update(future_data)

    form = DateForm(valid_data)
    assert not form.validate()
    assert form.errors


@pytest.mark.parametrize('two_digit_date', (
    ('00', '01', '01'),
    ('99', '12', '31'),
    ('20', '06', '26'),
))
def test_date_form_with_y2k_validator(two_digit_date):
    class DateForm(Form):
        date = DMDateField(validators=[FourDigitYear()])

    invalid_data = _data_fromtuple(two_digit_date)
    form = DateForm(invalid_data)
    assert not form.validate()
    assert form.errors


def test_date_form_with_y2k_validator_accepts_four_digit_dates(valid_data):
    class DateForm(Form):
        date = DMDateField(validators=[FourDigitYear()])

    form = DateForm(valid_data)
    assert form.validate()
    assert not form.errors
