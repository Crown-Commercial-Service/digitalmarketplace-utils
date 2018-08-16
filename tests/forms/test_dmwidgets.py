
import mock
import pytest

import dmutils.forms.widgets


def get_render_context(widget):
    call = widget._render.call_args
    return dict(*call[0], **call[1])


def monkeypatch_render(cls):
    def factory(*args, **kwargs):
        instance = cls(*args, **kwargs)
        instance._render = mock.Mock()
        return instance
    return factory


@pytest.fixture(params=dmutils.forms.widgets.__all__)
def widget_class(request):
    return monkeypatch_render(getattr(dmutils.forms.widgets, request.param))


@pytest.fixture
def widget(widget_class):
    return widget_class()


@pytest.fixture
def field():
    return mock.Mock()


def test_calling_widget_calls_template_render(widget, field):
    widget(field)
    assert widget._render.called


def test_template_context_is_populated_from_field(widget, field):
    widget(field)
    for k in widget.__context__:
        if widget.__context__[k] is not None:
            continue
        assert k in dir(field)
        assert k in get_render_context(widget)


def test_template_context_includes_hint(widget, field):
    field.hint = "Hint text."
    widget(field)
    assert get_render_context(widget)["hint"] == "Hint text."


def test_arguments_can_be_added_to_template_context_from_widget_constructor(widget_class, field):
    widget = widget_class(foo="bar")
    widget(field)
    assert get_render_context(widget)["foo"] == "bar"


class TestDMDateInput:
    @pytest.fixture()
    def widget_class(self):
        return monkeypatch_render(dmutils.forms.widgets.DMDateInput)

    def test_dm_date_input_does_not_send_value_to_template(self, widget, field):
        widget(field)
        assert "value" not in get_render_context(widget)

    def test_sends_render_argument_data_which_is_equal_to_field_value(self, widget, field):
        widget(field)
        assert get_render_context(widget)["data"] == field.value


class TestDMSelectionButtons:
    @pytest.fixture(params=["DMCheckboxInput", "DMRadioInput"])
    def widget_class(self, request):
        return monkeypatch_render(getattr(dmutils.forms.widgets, request.param))

    def test_dm_selection_buttons_send_type_to_render(self, widget, field):
        widget(field)
        assert "type" in get_render_context(widget)
