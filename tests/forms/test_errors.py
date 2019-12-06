from collections import OrderedDict

import pytest

from dmutils.forms.errors import govuk_errors


@pytest.mark.parametrize("dm_errors,expected_output", (
    ({}, OrderedDict()),
    (
        OrderedDict((
            ("haddock", {
                "input_name": "haddock",
                "question": "What was that, Joe?",
                "message": "Too numerous to be enumerated",
            },),
            ("pollock", {},),
            ("flounder", {
                "input_name": "flounder",
                "question": "Anything strange or wonderful, Joe?",
                "roach": "halibut",
            },),
        )),
        OrderedDict((
            ("haddock", {
                "input_name": "haddock",
                "question": "What was that, Joe?",
                "message": "Too numerous to be enumerated",
                "text": "Too numerous to be enumerated",
                "href": "#input-haddock",
                "errorMessage": {"text": "Too numerous to be enumerated"},
            },),
            ("pollock", {},),
            ("flounder", {
                "input_name": "flounder",
                "question": "Anything strange or wonderful, Joe?",
                "roach": "halibut",
                "text": "Anything strange or wonderful, Joe?",
                "href": "#input-flounder",
                "errorMessage": {"text": "Anything strange or wonderful, Joe?"},
            },),
        )),
    ),
))
def test_govuk_errors(dm_errors, expected_output):
    assert govuk_errors(dm_errors) == expected_output
