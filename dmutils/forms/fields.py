'''
This module includes classes that should be used with WTForms within Digital Marketplace apps.

They extend the classes found in `wtforms.fields`, and should be used instead of those.
The advantage they provide is that they have been deliberately designed to be used with
the Digital Marketplace frontend toolkit macros. If a particular field is missing, it
should be added to this file.

The main functionality is provided by the mixin class, `DMFieldMixin`. When a derived class
includes `DMFieldMixin` in its base classes then the following extra features are provided:

        - a `hint` property that can be set in the initialiser
        - a `question` property that contains the label text
        - a `value` property for the data that is displayed
        - an `error` property for the field validation error

For more details on how `DMFieldMixin`, see the documentation in `dmutils/forms/mixins.py`.
'''

import datetime
from itertools import chain

import wtforms
import wtforms.fields
from wtforms.utils import unset_value
from wtforms.validators import Length

from .mixins import DMFieldMixin, DMSelectFieldMixin
from .widgets import (
    DMCheckboxInput,
    DMDateInput,
    DMRadioInput,
    DMTextInput,
    DMUnitInput,
)

from .filters import strip_whitespace
from .validators import EmailValidator


__all__ = ['DMBooleanField', 'DMDecimalField', 'DMHiddenField', 'DMIntegerField',
           'DMRadioField', 'DMStringField', 'DMEmailField', 'DMStripWhitespaceStringField',
           'DMDateField']


class DMBooleanField(DMFieldMixin, wtforms.fields.BooleanField):
    widget = DMCheckboxInput(hide_question=True)

    @property
    def href(self):
        # digitalmarketplace-frontend-toolkit suffixes the id with `-1`
        return self._href or super().href + "-1"

    @property
    def options(self):
        return [{"label": self.label.text, "value": self.data}]

    @property
    def value(self):
        if not self.data or self.data == "None":
            return []
        else:
            return [self.data]


class DMDecimalField(DMFieldMixin, wtforms.fields.DecimalField):
    pass


class DMPoundsField(DMDecimalField):
    widget = DMUnitInput()

    unit = "£"
    unit_in_full = "pounds"
    unit_position = "before"
    hint = "For example, 9900.95 for 9900 pounds and 95 pence"


class DMHiddenField(DMFieldMixin, wtforms.fields.HiddenField):
    pass


class DMIntegerField(DMFieldMixin, wtforms.fields.IntegerField):
    pass


class DMRadioField(DMSelectFieldMixin, DMFieldMixin, wtforms.fields.RadioField):
    widget = DMRadioInput()


class DMStringField(DMFieldMixin, wtforms.fields.StringField):
    widget = DMTextInput()


class DMStripWhitespaceStringField(DMFieldMixin, wtforms.fields.StringField):
    widget = DMTextInput()

    def __init__(self, label=None, **kwargs):
        kwargs['filters'] = tuple(chain(
            kwargs.get('filters', ()) or (),
            (
                strip_whitespace,
            ),
        ))
        super().__init__(label, **kwargs)


class DMEmailField(DMStripWhitespaceStringField):
    def __init__(self, label=None, **kwargs):
        kwargs["validators"] = tuple(chain(
            kwargs.pop("validators", ()) or (),
            (
                EmailValidator(),
                Length(max=511, message="Please enter an email address under 512 characters."),
            ),
        ))
        super().__init__(label, **kwargs)


class DMDateField(DMFieldMixin, wtforms.fields.Field):
    '''
    A date field(set) that uses a day, month and year field.

    The data is converted to a `datetime.date`. The year is
    required to be four digits.

    It behaves like a WTForms.FieldForm, but it can be used
    with validators like a normal WTForms.Field.

    >>> from wtforms import Form
    >>> from wtforms.validators import DataRequired
    >>> from werkzeug.datastructures import MultiDict
    >>> formdata = MultiDict({
    ...     'date-day': '31',
    ...     'date-month': '12',
    ...     'date-year': '1999'})
    >>> class DateForm(Form):
    ...     date = DateField(validators=[DataRequired()])
    >>> form = DateForm(formdata)
    >>> form.date.data
    datetime.date(1999, 12, 31)
    '''

    widget = DMDateInput()

    hint = "For example, 31 12 2020"

    # An internal class that defines the fields that make up the DateField.
    #
    # Inheriting from wtforms.FormField has limitations on using validators.
    #
    # Instead, the DateField is composed of a wtforms.FormField that is used
    # to turn the form data into integer values, and we then grab the data.
    #
    # The FormField instance is based on this class.
    class _DateForm(wtforms.Form):
        day = wtforms.fields.IntegerField("Day")
        month = wtforms.fields.IntegerField("Month")
        year = wtforms.fields.IntegerField("Year")

    def __init__(self, label=None, validators=None, hint=None, question_advice=None, separator='-', **kwargs):
        super().__init__(label=label, validators=validators, hint=hint, question_advice=question_advice, **kwargs)
        self.form_field = wtforms.fields.FormField(self._DateForm, separator=separator, **kwargs)

    def _value(self):
        '''
        Return the values that are used to display the form

        Overrides wtforms.Field._value().
        '''
        if self.raw_data:
            return self.raw_data[0]
        else:
            return {}

    @property
    def href(self):
        if self._href:
            return self._href

        # first form field field with an error,
        if self.form_field.errors:
            for subfield in self.form_field:
                if subfield.errors:
                    return "input-" + subfield.name

        # or just the first form field field
        return super().href + "-day"

    @property
    def day(self):
        return self.form_field.day

    @property
    def month(self):
        return self.form_field.month

    @property
    def year(self):
        return self.form_field.year

    def process(self, formdata, data=unset_value):
        '''
        Process incoming data.

        Overrides wtforms.Field.process().

        Filters, process_data and process_formdata are not supported.
        '''
        self.process_errors = []

        # use the FormField to process `formdata` and `data`
        self.form_field.process(formdata, data)

        # make a "fake" raw_data property from the FormField values
        # we need the raw_data property for various validators
        raw_data = {field.name: field.raw_data[0] for field in self.form_field
                    if field.raw_data}
        if not any(raw_data.values()):
            # if all fields were empty we want raw_data to be None-ish
            raw_data = {}

        # the WTForms.Field api expects .raw_data to be a list
        self.raw_data = [raw_data]

        try:
            self.data = datetime.date(**self.form_field.data)
        except (TypeError, ValueError):
            self.data = None
            self.process_errors.append(self.gettext('Not a valid date value'))

        # if the year does not have four digits call the data invalid
        if self.data:
            try:
                digits = len(self.form_field.year.raw_data[0])
            except IndexError:
                digits = 0

            if not digits == 4:
                self.data = None
                self.process_errors.append(self.gettext('Not a valid date value'))

    def post_validate(self, form, validation_stopped):
        # Consumers of a data field might want to highlight individual inputs
        # of the date input component, checking the values of {day, month,
        # year}.errors.  In the case where the validator chain hasn't added
        # errors to any of day month or year, we will add the errors to all the
        # fields so that all inputs get highlighted.
        if self.errors and not any((self.year.errors, self.month.errors, self.day.errors)):
            self.year.errors = self.errors
            self.month.errors = self.errors
            self.day.errors = self.errors
