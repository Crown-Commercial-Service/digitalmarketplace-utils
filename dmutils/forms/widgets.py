from typing import Optional

from flask import current_app

__all__ = ["DMCheckboxInput", "DMDateInput", "DMRadioInput", "DMTextInput", "DMTextArea", "DMUnitInput"]


class DMJinjaWidgetBase:

    # we include common template arguments here to avoid repetition
    error = None
    name = None
    hint = None
    question = None
    question_advice = None
    value = None

    def __init__(self, hide_question=False, **kwargs):
        self.__template__ = None

        self.__context__ = {k: getattr(self, k) for k in dir(self) if not k.startswith("_")}
        self.__constructor_kwargs__ = kwargs

        self.__dict__.update(kwargs)

        if hide_question:
            del self.__context__["question"]

    def __call__(self, field, **kwargs):

        # get the template variables
        # precedence (decreasing order)
        # - kwargs to __call__
        # - kwargs to constructor
        # - field values
        # - widget defaults

        context = {}
        context.update(self.__context__)

        for attr in context:
            # we don't want the type from the field because
            # this is just the class name of the field
            if attr == "type":
                continue
            if hasattr(field, attr):
                context[attr] = getattr(field, attr)

        context.update(self.__constructor_kwargs__)
        context.update(kwargs)

        return self._render(context)

    def _render(self, *args, **kwargs):
        # cache the template
        # this cannot be done in __init__ as the flask app may not exist
        if not self.__template__:
            self.__template__ = current_app.jinja_env.get_template(self.__template_file__)

        return self.__template__.render(*args, **kwargs)


class DMSelectionButtonBase(DMJinjaWidgetBase):
    __template_file__ = "toolkit/forms/selection-buttons.html"

    type: Optional[str] = None
    inline = None
    options = None


class DMCheckboxInput(DMSelectionButtonBase):
    type = "checkbox"


class DMDateInput(DMJinjaWidgetBase):
    __template_file__ = "toolkit/forms/date.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        del self.__context__["value"]

    def __call__(self, field, **kwargs):
        return super().__call__(field, data=field.value, **kwargs)


class DMRadioInput(DMSelectionButtonBase):
    type = "radio"


class DMTextInput(DMJinjaWidgetBase):
    __template_file__ = "toolkit/forms/textbox.html"


class DMTextArea(DMTextInput):
    large = True

    def __init__(self, max_length_in_words=None, **kwargs):
        if max_length_in_words:
            self.max_length_in_words = max_length_in_words

        super().__init__(**kwargs)


class DMUnitInput(DMTextInput):
    unit = None
    unit_in_full = None
    unit_position = None
