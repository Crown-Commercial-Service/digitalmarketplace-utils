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
        self.hint = hint or getattr(self.__class__, 'hint', None)

        super().__init__(label=label, validators=validators, **kwargs)

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
