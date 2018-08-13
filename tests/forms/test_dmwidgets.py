
import mock
import pytest

import dmutils.forms.widgets as dm_widgets


@pytest.fixture(params=dm_widgets.__all__)
def widget_class(request):
    return getattr(dm_widgets, request.param)


@pytest.fixture
def widget(widget_class):
    widget = widget_class()
    widget.template = mock.Mock()
    return widget


@pytest.fixture
def field():
    return mock.Mock()


def test_calling_widget_calls_template_render(widget, field):
    widget(field)
    assert widget.template.render.called


def test_template_render_args_are_populated_from_field(widget, field):
    widget(field)
    for k in widget.template_args:
        assert k in dir(field)
        assert k in widget.template.render.call_args[1]
