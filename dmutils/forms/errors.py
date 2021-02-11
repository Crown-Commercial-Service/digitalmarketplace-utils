from collections import OrderedDict
import typing


# TODO use TypedDict once we're on python 3.8 to allow us to be more specific about this mapping's contents
ErrorMapping = typing.Mapping[str, typing.Any]


def govuk_error(error: ErrorMapping) -> ErrorMapping:
    if error:
        text = error.get("message", error.get("question", ""))
        return {
            "text": text,
            "href": error.get("href") or f"#input-{error['input_name']}",
            "errorMessage": {"text": text},
        }
    else:
        return {}


# TODO: use typing.OrderedDict once we're on Python 3.7
def govuk_errors(errors: typing.Mapping[str, ErrorMapping]) -> typing.Mapping[str, ErrorMapping]:
    """Converts digitalmarketplace-frontend-toolkit style errors into a format
    suitable for use with either digitalmarketplace-frontend-toolkit
    templates/macros or govuk-frontend macros.

    Returns a dictionary with the following keys, supporting three types of
    error display:

    1) digitalmarketplace-frontend-toolkit template toolkit/forms/validation.html:
      `input_name`, `question`, `message`

    2) govuk-frontend macro govukErrorSummary:
      `text`, `href`

    3) govuk-frontend errorMessage:
      `errorMessage`

    This allows us to treat errors from both content-loader forms and wtforms
    the same way inside templates,
    and provides backwards-compatible support for the migration to using
    govuk-frontend components.

    Example usage:

        # app.py

        @flask.route("/", methods=["GET", "POST"])
        def view():
            section = content_loader.get_section()
            try:
                data_api_client.update_something()
            except HTTPError as e:
                errors = govuk_errors(
                    section.get_error_messages(e.message)
                )

            return render(
                "template.html",
                question=section,
                errors=errors,
            )

        # template.html  (govuk-frontend)
        {{ govukErrorSummary({
            "errorList": errors.values()
        }) }}

        {{ govukTextInput({
            "errorMessage": errors.input.errorMessage,
        }) }}

        # template.html (DM frontend toolkit uses 'errors' by default)
        {% include 'toolkit/forms/validation.html' %}

        {{ forms[question.type](question, service_data, errors) }}

    :param errors: A digitalmarketplace-frontend-toolkit error dictionary
    :return: A dict with error information in a form suitable for
             Digital Marketplace templates
    """
    return OrderedDict(
        (key, {**error, **govuk_error(error)}) for key, error in errors.items()
    )


def get_errors_from_wtform(form):
    """Converts Flask-WTForm errors into formats suitable for use in Digital Marketplace templates.

    Returns a dictionary with the following keys, supporting three types of error display:

    1) digitalmarketplace-frontend-toolkit template toolkit/forms/validation.html:
      `input_name`, `question`, `message`

    2) govuk-frontend macro govukErrorSummary:
      `text`, `href`

    3) govuk-frontend errorMessage:
      `errorMessage`

    This allows us to treat errors from both content-loader forms and wtforms the same way inside templates,
    and provides backwards-compatible support for the migration to using govuk-frontend components.

    The `href` for the govuk-frontend error summary is derived from the `id` of the form field; if you need to
    override the `href` for some reason you can do this by passing the correct `id` to the field constructor.

    Example usage:

        # app.py
        class Form(FlaskForm):
            input = DMTextInput()

        @flask.route("/")
        def view():
            form = Form()
            errors = get_errors_from_wtform(form)
            return render(
                "template.html",
                errors=errors,
            )

        # template.html  (govuk-frontend)
        {{ govukErrorSummary({
            "errorList": errors.values()
        }) }}

        {{ govukTextInput({
            "errorMessage": errors.input.errorMessage,
        }) }}

        # template.html (DM frontend toolkit uses 'errors' by default)
        {% include 'toolkit/forms/validation.html' %}

    :param form: A Flask-WTForm
    :return: A dict with error information in a form suitable for Digital Marketplace templates
    """
    return OrderedDict(
        # TODO: remove legacy code (items for frontend toolkit validation banners)
        (
            key,
            {
                # parameters for digitalmarketplace-frontend-toolkit template toolkit/forms/validation.html
                "input_name": key, "question": form[key].label.text, "message": form[key].errors[0],

                # parameters for govuk-frontend macro govukErrorSummary
                "text": form[key].errors[0], "href": f"#{getattr(form[key], 'href', form[key].id)}",

                # parameters for govuk-frontend errorMessage parameter
                "errorMessage": (
                    {"text": form[key].errors[0]}
                    if form[key].errors[0]
                    else {}
                )
            }
        )
        for key in
        form.errors.keys()
    )
