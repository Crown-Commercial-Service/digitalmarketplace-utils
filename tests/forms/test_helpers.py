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
))
def test_govuk_options(dm_options, expected_output):
    assert govuk_options(dm_options) == expected_output
