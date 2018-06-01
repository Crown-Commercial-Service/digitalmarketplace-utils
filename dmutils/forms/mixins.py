

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

    It needs to be used with `wtforms.Field`.

    Usage:
    >>> from wtforms import Form, StringField
    >>> class DMStringField(DMFieldMixin, StringField):
    ...     pass
    >>> class TextForm(Form):
    ...     text = DMStringField('Text field', hint='Type text here.')
    >>> form = TextForm()
    >>> form.text.name
    'text'
    >>> form.text.question
    'Text field'
    >>> form.text.hint
    'Type text here.'
    '''
    def __init__(self, label=None, validators=None, hint=None, **kwargs):
        self.hint = hint

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
