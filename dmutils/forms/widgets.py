
from flask import current_app

__all__ = ["DMCheckboxInput", "DMDateInput", "DMRadioInput", "DMTextInput", "DMUnitInput"]


class DMJinjaWidgetBase:

    template_args = []

    def __init__(self, hide_question=False):
        # we include common template arguments here to avoid repetition
        self.template_args = ["error", "name", "hint", "question", "value"] + self.template_args
        if hide_question:
            self.template_args.remove("question")

        self.template = None

    def __call__(self, field, **kwargs):
        # get the template variables from the field
        for attr in self.template_args:
            if hasattr(field, attr):
                kwargs.setdefault(attr, getattr(field, attr))

        # cache the template
        # this cannot be done in __init__ as the flask app may not exist
        if not self.template:
            self.template = current_app.jinja_env.get_template(self.template_file)

        html = self.template.render(**kwargs)
        return html


class DMSelectionButtonBase(DMJinjaWidgetBase):
    template_args = ["type", "inline", "options"]
    template_file = "toolkit/forms/selection-buttons.html"

    def __call__(self, field, **kwargs):
        kwargs["type"] = self.type
        return super().__call__(field, **kwargs)


class DMCheckboxInput(DMSelectionButtonBase):
    type = "checkbox"


class DMDateInput(DMJinjaWidgetBase):
    template_file = "toolkit/forms/date.html"

    def __init__(self):
        super().__init__()
        self.template_args.remove("value")

    def __call__(self, field, **kwargs):
        kwargs["data"] = field.value
        return super().__call__(field, **kwargs)


class DMRadioInput(DMSelectionButtonBase):
    type = "radio"


class DMTextInput(DMJinjaWidgetBase):
    template_file = "toolkit/forms/textbox.html"


class DMUnitInput(DMTextInput):
    template_args = ["unit_in_full", "unit", "unit_position"]
