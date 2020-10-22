import pytest

from dmutils.forms.helpers import govuk_options


@pytest.mark.parametrize("dm_options,expected_output", (
    ([], []),
    (
        [
            {
                "label": "text of the label",
            },
        ],
        [
            {
                "value": "text of the label",
                "text": "text of the label",
            },
        ],
    ),
    (
        [
            {
                "label": "text of the label",
                "value": "text of the value",
            },
        ],
        [
            {
                "value": "text of the value",
                "text": "text of the label",
            },
        ],
    ),
    (
        [
            {
                "label": "text of the label",
                "value": "text of the value",
                "description": "text of the description",
            },
        ],
        [
            {
                "value": "text of the value",
                "text": "text of the label",
                "hint": {"text": "text of the description"},
            },
        ],
    ),
    (
        [
            {
                "label": "text of the label",
                "value": "text of the value",
                "hint": "text of the hint",
            },
        ],
        [
            {
                "value": "text of the value",
                "text": "text of the label",
                "hint": {"text": "text of the hint"},
            },
        ],
    ),
))
def test_govuk_options(dm_options, expected_output):
    assert govuk_options(dm_options) == expected_output


def test_govuk_options_with_checked_item():
    options = [
        {"label": "Yes", "value": "yes"},
        {"label": "No", "value": "no"},
    ]

    data = "yes"

    items = govuk_options(options, data)

    assert items == [
        {"text": "Yes", "value": "yes", "checked": True},
        {"text": "No", "value": "no"},
    ]


def test_govuk_options_with_multiple_checked_items():
    options = [
        {"label": "A", "value": "a"},
        {"label": "B", "value": "b"},
        {"label": "C", "value": "c"},
    ]

    data = ["a", "c"]

    items = govuk_options(options, data)

    assert items == [
        {"text": "A", "value": "a", "checked": True},
        {"text": "B", "value": "b"},
        {"text": "C", "value": "c", "checked": True},
    ]


def test_govuk_options_with_invalid_data():
    options = [
        {"label": "a", "value": "a"},
        {"label": "b", "value": "b"},
        {"label": "c", "value": "c"},
    ]

    expected_options = [
        {"text": "a", "value": "a"},
        {"text": "b", "value": "b"},
        {"text": "c", "value": "c"},
    ]

    assert govuk_options(options, "yes") == expected_options
    assert govuk_options(options, "") == expected_options
    assert govuk_options(options, None) == expected_options
    assert govuk_options(options, []) == expected_options
    with pytest.raises(TypeError):
        govuk_options(options, {})
