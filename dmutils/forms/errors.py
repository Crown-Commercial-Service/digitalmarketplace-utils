from collections import OrderedDict


def govuk_error(error):
    if error:
        text = error.get("message", error.get("question", ""))
        return {
            "text": text,
            "href": f"#input-{error['input_name']}",
            "errorMessage": {"text": text},
        }
    else:
        return {}


def govuk_errors(errors):
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
