
# allow importing from dmutils.forms.helpers for backwards compatibility
from .errors import get_errors_from_wtform  # noqa: F401

import typing


def remove_csrf_token(data):
    """Flask-WTF==0.14.2 now includes `csrf_token` in `form.data`, whereas previously wtforms explicitly didn't do
    this. When we pass form data straight through to the API, the API often carries out strict validation and doesn't
    like to see `csrf_token` in the input. So this helper will strip it out of a dict, if it's present.

    Example:
    >>> remove_csrf_token(form.data)
    """
    cleaned_data = {**data}

    if 'csrf_token' in data:
        del cleaned_data['csrf_token']

    return cleaned_data


def govuk_option(
    option: typing.Dict, data: typing.Optional[typing.Union[typing.List[str], str]] = None
) -> typing.Dict:
    """Converts one digitalmarketplace-frontend-toolkit style option (of the radio and checkboxes elements)
    into a format suitable for use with either digitalmarketplace-frontend-toolkit
    templates/macros or govuk-frontend macros.

    Example usage:

    # app.py

        @flask.route("/", methods=["GET", "POST"])
        def view():
            lot_question = {
            option["value"]: option
            for option in govuk_option(
                ContentQuestion(content_loader.get_question(framework_slug, 'services', 'lot')).get('options')
            )
        }
    """
    _data: typing.List[str]
    if data is None:
        _data = []
    elif isinstance(data, str):
        _data = [data]
    elif isinstance(data, list):
        _data = data
    else:
        raise TypeError("`data` must be a string or a list of strings")

    if option:
        # DMp does not require a value for an option, fallback to label if not present
        value = option.get("value", option["label"])
        item = {
            "value": value,
            "text": option['label'],
        }
        if value in _data:
            item["checked"] = True
        if "hint" in option:
            item.update({"hint": {"text": option["hint"]}})
        elif "description" in option:
            item.update({"hint": {"text": option["description"]}})
        return item
    else:
        return {}


def govuk_options(
    options: typing.List[typing.Dict], data: typing.Optional[typing.Union[typing.List[str], str]] = None
) -> typing.List[typing.Dict]:
    """Converts all digitalmarketplace-frontend-toolkit style options (of the radio and checkboxes elements)
    into a format suitable for use with either digitalmarketplace-frontend-toolkit
    templates/macros or govuk-frontend macros.

    Example usage:

    # app.py

    @direct_award_public.route('/<string:framework_family>/choose-lot', methods=("GET", "POST"))
    def choose_lot(framework_family):
        all_frameworks = data_api_client.find_frameworks().get('frameworks')
        framework = framework_helpers.get_latest_live_framework_or_404(all_frameworks, framework_family)

        content_loader.load_messages(framework['slug'], ['advice', 'descriptions'])
        gcloud_lot_messages = content_loader.get_message(framework['slug'], 'advice', 'lots')
        gcloud_lot_messages = {x['slug']: x for x in gcloud_lot_messages}

        lots = list()
        for lot in framework['lots']:
            lot_item = {
                "value": lot['slug'],
                "label": lot['name'],
                "description": gcloud_lot_messages[lot['slug']]['body'],
                "hint": gcloud_lot_messages[lot['slug']].get('advice'),
            }

            lots.append(lot_item)
        return render_template('choose-lot.html',
                            framework_family=framework_family,
                            title="Choose a category",
                            lots=govuk_options(lots))
    """
    return [govuk_option(option, data) for option in options]
