import pytest

import wtforms

from dmutils.forms.fields import DMBooleanField


class BooleanForm(wtforms.Form):
    field = DMBooleanField()


@pytest.fixture
def form():
    return BooleanForm()
