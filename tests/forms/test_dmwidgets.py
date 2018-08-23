
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


def test_template_context_includes_question_advice(widget, field):
    field.question_advice = "Advice text."
    widget(field)
    assert get_render_context(widget)["question_advice"] == "Advice text."


def test_arguments_can_be_added_to_template_context_from_widget_constructor(widget_class, field):
    widget = widget_class(foo="bar")
    widget(field)
    assert get_render_context(widget)["foo"] == "bar"


class TestDMTextArea:
    @pytest.fixture()
    def widget_class(self):
        return monkeypatch_render(dmutils.forms.widgets.DMTextArea)

    def test_dm_text_area_sends_large_is_true_to_template(self, widget, field):
        widget(field)
        assert get_render_context(widget)["large"] is True

    @pytest.mark.parametrize("max_length_in_words", (1, 45, 100))
    def test_dm_text_area_can_send_max_length_in_words_to_template(self, widget_class, max_length_in_words, field):
        widget = widget_class()
        widget(field)
        assert "max_length_in_words" not in get_render_context(widget)

        widget = widget_class(max_length_in_words=max_length_in_words)
        widget(field)
        assert get_render_context(widget)["max_length_in_words"] == max_length_in_words

    def test_dm_text_area_max_words_template_constant_is_instance_variable(self, widget_class):
        widget1 = widget_class(max_length_in_words=mock.sentinel.max_length1)
        widget2 = widget_class(max_length_in_words=mock.sentinel.max_length2)

        widget1(mock.Mock())
        widget2(mock.Mock())

        assert (
            get_render_context(widget1)["max_length_in_words"]
            !=
            get_render_context(widget2)["max_length_in_words"]
        )


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
