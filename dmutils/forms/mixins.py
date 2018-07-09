'''
This module includes mixins that are designed to make it easier to use WTForms
with the Digital Marketplace frontend toolkit.

For example:

    >>> from wtforms import Form, StringField
    >>>
    >>> # include the mixin in a new class
    >>> class DMStringField(DMFieldMixin, StringField):
    ...     pass
    >>>
    >>> # create a form with our new field class
    >>> class TextForm(Form):
    ...     text = DMStringField('Text field', hint='Type text here.')
    >>>
    >>> form = TextForm()
    >>>
    >>> # our new field has all the benefits of DMFieldMixin
    >>> form.text.name
    'text'
    >>> form.text.question
    'Text field'
    >>> form.text.hint
    'Type text here.'

For more examples of these mixins in action, see `dmutils/forms/dm_fields.py`.

For more about mixins in general, see this `online article`_,
or the very excellent `Python Cookbook`_ by David Beazley.

.. _online article:
    https://zonca.github.io/2013/04/simple-mixin-usage-in-python.html
.. _Python Cookbook:
    http://dabeaz.com/cookbook.html
'''

from copy import copy

from wtforms.compat import text_type
from wtforms.fields import SelectField


class DMFieldMixin:
    '''
    A mixin designed to make it easier to use WTForms
    with the frontend toolkit. The idea is that the
    properties mirror the definitions that the toolkit
    template macros expect.

    It adds the following features:
        - a `hint` property that can be set in the initialiser
        - a `question` property that contains the label text
        - a `value` property for the data that is displayed
        - an `error` property for the field validation error

    Derived classes which include this mixin should have a
    subclass of `wtforms.Field` in their base classes.
    '''
    def __init__(self, label=None, validators=None, hint=None, **kwargs):
        super().__init__(label=label, validators=validators, **kwargs)
        self.hint = hint or getattr(self.__class__, 'hint', None)
        self.type = getattr(self.__class__, 'type', self.type)

    @property
    def question(self):
        return self.label.text

    @property
    def value(self):
        return self._value()

    @property
    def error(self):
        try:
            return self.errors[0]
        except IndexError:
            return None


class DMSelectFieldMixin(SelectField):
    '''
    A Digital Marketplace wrapper for selection fields.

    The `options` argument for the constructor should be a dictionary with
    `value`, label`, and `description` keys.

    The `options` attribute is the choices in a format suitable for the
    frontend toolkit.
    '''
    def __init__(self, label=None, validators=None, coerce=text_type, options=None, **kwargs):
        super().__init__(label, validators, coerce, **kwargs)
        self.options = copy(options)

    @property
    def choices(self):
        return [(option['value'], option['label']) for option in self.options] if self.options else []

    @choices.setter
    def choices(self, value):
        if value is None:
            self.options = None
        else:
            for value, label in value:
                self.options.append(
                    {
                        'label': label,
                        'value': value,
                    }
                )
