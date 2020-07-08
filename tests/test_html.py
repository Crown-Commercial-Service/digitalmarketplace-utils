import pytest

from dmutils.html import link_to
import jinja2


class TestToLink:
    @pytest.mark.parametrize("label", (None, ''))
    def test_to_link_sets_url_as_label_if_label_is_empty(self, label):
        link = link_to('https://www.google.com', label)
        assert link == '<a href="https://www.google.com">https://www.google.com</a>'

    def test_to_link_wraps_label_with_a_tag(self):
        link = link_to('https://www.google.com', 'Label')
        assert link == '<a href="https://www.google.com">Label</a>'

    def test_to_link_raises_error_if_url_is_not_string(self):
        with pytest.raises(ValueError):
            link_to(False, 'label')

    def test_to_link_raises_error_if_url_is_empty(self):
        with pytest.raises(ValueError):
            link_to('', 'label')

    def test_to_link_adds_attributes(self):
        link = link_to('#', 'label', target='_blank')
        assert link == '<a href="#" target="_blank">label</a>'

    def test_to_link_ignores_non_text_attributes(self):
        link = link_to('#', 'label', target=2)
        assert link == '<a href="#">label</a>'

    @pytest.mark.parametrize('autoescape', (True, False))
    def test_to_link_returns_string_that_is_safe_for_jinja(self, autoescape):
        link = link_to('<script>bad thing</script>')
        env = jinja2.Environment(autoescape=autoescape)

        template = env.from_string("{{ html }}")

        expected = '<a href="&lt;script&gt;bad thing&lt;/script&gt;">&lt;script&gt;bad thing&lt;/script&gt;</a>'

        assert template.render(html=link) == expected
