# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest

from flask import Markup
from unittest import mock

from dmutils.filters import (
    capitalize_first, format_links, nbsp, smartjoin, preserve_line_breaks, sub_country_codes
)


class TestSmartJoin:
    def test_smartjoin_for_more_than_one_item(self):
        list_to_join = ['one', 'two', 'three', 'four']
        filtered_string = 'one, two, three and four'
        assert smartjoin(list_to_join) == filtered_string

    def test_smartjoin_for_one_item(self):
        list_to_join = ['one']
        filtered_string = 'one'
        assert smartjoin(list_to_join) == filtered_string

    def test_smartjoin_for_empty_list(self):
        list_to_join = []
        filtered_string = ''
        assert smartjoin(list_to_join) == filtered_string


class TestFormatLinks:
    def test_format_link(self):
        link = 'http://www.example.com'
        formatted_link = '<a href="http://www.example.com" class="govuk-link" rel="external">http://www.example.com</a>' # noqa
        assert format_links(link) == formatted_link

    def test_format_link_without_protocol(self):
        link = 'www.example.com'
        formatted_link = 'www.example.com'
        assert format_links(link) == formatted_link

    def test_format_link_with_text(self):
        text = 'This is the Greek Γ Δ Ε Ζ Η Θ Ι Κ Λ link: http://www.exΔmple.com'
        formatted_text = 'This is the Greek Γ Δ Ε Ζ Η Θ Ι Κ Λ link: <a href="http://www.exΔmple.com" class="govuk-link" rel="external">http://www.exΔmple.com</a>'  # noqa
        assert format_links(text) == formatted_text

    def test_format_link_handles_markup_objects_with_protocol(self):
        text = Markup('<td class="summary-item-field">\n\n<span>Hurray - http://www.example.com is great</span></td>')
        formatted_text = Markup('<td class="summary-item-field">\n\n<span>Hurray - <a href="http://www.example.com" class="govuk-link" rel="external">http://www.example.com</a> is great</span></td>')  # noqa
        assert format_links(text) == formatted_text

    def test_format_link_handles_markup_objects_without_protocol(self):
        text = Markup('<td class="summary-item-field">\n\n<span>Hurray - www.example.com is great</span></td>')
        formatted_text = Markup('<td class="summary-item-field">\n\n<span>Hurray - www.example.com is great</span></td>')  # noqa
        assert format_links(text) == formatted_text

    def test_format_link_and_text_escapes_extra_html(self):
        text = 'This is the <strong>link</strong>: http://www.example.com'
        formatted_text = 'This is the &lt;strong&gt;link&lt;/strong&gt;: <a href="http://www.example.com" class="govuk-link" rel="external">http://www.example.com</a>'  # noqa
        assert format_links(text) == formatted_text

    def test_format_link_does_not_die_horribly(self):
        text = 'This is the URL that made a previous regex die horribly' \
               'https://something&lt;span&gt;what&lt;/span&gt;something.com'
        formatted_text = 'This is the URL that made a previous regex die horribly' \
                         '<a href="https://something&amp;lt;span&amp;gt;what&amp;lt;/span&amp;gt;something.com" ' \
                         'class="govuk-link" rel="external">' \
                         'https://something&amp;lt;span&amp;gt;what&amp;lt;/span'\
                         '&amp;gt;something.com</a>'
        assert format_links(text) == formatted_text

    def test_format_links_open_links_in_new_tab(self):
        link = 'http://www.example.com'
        link_new_tab = '<a href="http://www.example.com" class="govuk-link" rel="external noreferrer noopener" target="_blank">http://www.example.com</a>'  # noqa
        assert format_links(link, open_links_in_new_tab=True) == link_new_tab

    def test_multiple_urls(self):
        text = 'This is the first link http://www.example.com and this is the second http://secondexample.com.'  # noqa
        formatted_text = 'This is the first link <a href="http://www.example.com" class="govuk-link" '\
            'rel="external">http://www.example.com</a> and this is the second '\
            '<a href="http://secondexample.com" class="govuk-link" rel="external">' \
            'http://secondexample.com</a>.'
        assert format_links(text) == formatted_text

    def test_no_links_no_change(self):
        text = 'There are no Greek Γ Δ Ε Ζ Η Θ Ι Κ Λ links.'
        assert format_links(text) == text

    def test_handles_url_in_brackets(self):
        text = "(http://www.example.com)"
        formatted_text = '(<a href="http://www.example.com" class="govuk-link" '\
            'rel="external">http://www.example.com</a>)'
        assert format_links(text) == formatted_text

    def test_handles_url_in_angle_brackets(self):
        text = "<http://www.example.com>"
        formatted_text = '&lt;<a href="http://www.example.com" class="govuk-link" '\
            'rel="external">http://www.example.com</a>&gt;'
        assert format_links(text) == formatted_text


class TestNbsp:
    def test_nbsp(self):
        """Test that spaces are replaced with nbsp."""
        text = 'foo bar baz'
        expected = Markup('foo&nbsp;bar&nbsp;baz')
        result = nbsp(text)
        assert result == expected

    def test_nbsp_escapes(self):
        """Ensure the filter escapes HTML."""
        text = 'foo bar baz <script>'
        expected = Markup('foo&nbsp;bar&nbsp;baz&nbsp;&lt;script&gt;')
        result = nbsp(text)
        assert result == expected

    def test_nbsp_with_markup(self):
        """When markup passed in should still return markup."""
        text = Markup('foo bar baz <script>')
        expected = Markup('foo&nbsp;bar&nbsp;baz&nbsp;<script>')
        result = nbsp(text)
        assert result == expected


class TestCapitaliseFirst:
    def test_capitalise_first_for_strings(self):
        assert capitalize_first('lowercase') == 'Lowercase'
        assert capitalize_first('UPPERCASE') == 'UPPERCASE'
        assert capitalize_first('_lower') == '_lower'
        assert capitalize_first('cAMELcASE??') == 'CAMELcASE??'

    def test_capitalize_first_for_short_strings(self):
        assert capitalize_first('') == ''
        assert capitalize_first('a') == 'A'
        assert capitalize_first('B') == 'B'
        assert capitalize_first('+') == '+'

    def test_capitalize_first_for_non_strings(self):
        assert capitalize_first(5) == 5
        assert capitalize_first(None) is None
        assert capitalize_first(True) is True
        assert capitalize_first(False) is False
        assert capitalize_first(['list', 'of', 'strings']) == ['List', 'Of', 'Strings']
        assert capitalize_first([{'list': 'of'}, 'things']) == [{'list': 'of'}, 'Things']
        assert capitalize_first({'this': 'thing'}) == {'this': 'thing'}
        assert capitalize_first('https://www.example.com') == 'https://www.example.com'


class TestPreserveLineBreaks:
    @pytest.mark.parametrize("_autoescape", (False, True))
    def test_preserve_line_breaks(self, _autoescape):
        # We expect the same output regardless of the eval context `autoescape` value
        eval_ctx_mock = mock.Mock(autoescape=_autoescape)
        assert preserve_line_breaks(eval_ctx_mock, '\r\n') == '<br>'
        assert preserve_line_breaks(eval_ctx_mock, '\r\n\r\n') == '<br><br>'
        assert preserve_line_breaks(eval_ctx_mock, '\r\n \r\n \r\n') == '<br><br>'
        assert preserve_line_breaks(eval_ctx_mock, '\r\n\r\n\r\n\r\n\r\n\r\n') == '<br><br>'
        assert preserve_line_breaks(eval_ctx_mock, '') == ''
        assert preserve_line_breaks(eval_ctx_mock, '\r\n<h2>') == '<br>&lt;h2&gt;'
        assert preserve_line_breaks(eval_ctx_mock, '\n') == '\n'
        assert preserve_line_breaks(eval_ctx_mock, 'You’ll be eating 🍕') == 'You’ll be eating 🍕'
        assert preserve_line_breaks(eval_ctx_mock, '\r\n\r\n  \r\n\r\n  \t\v \r\n\r\n') == '<br><br>'


class TestSubCountryCodes:
    def test_sub_country_codes(self):
        assert sub_country_codes(None) is None
        assert sub_country_codes("") == ""
        assert sub_country_codes("This text contains no country codes") == "This text contains no country codes"
        assert sub_country_codes("country:GB") == "United Kingdom"
        assert sub_country_codes("The country:GB consists of four nations") == "The United Kingdom consists of four " \
                                                                               "nations"
        assert sub_country_codes("The UK consists of four nations") == "The UK consists of four nations"
        assert sub_country_codes("country:XY is not a valid country code") == "XY is not a valid country code"
        assert sub_country_codes("country:XY") == "XY"

        assert sub_country_codes(
            """
            There are three Latin American countries that straddle the equator:
            country:BR, country:EC, and country:CO.
            """
        ) == (
            """
            There are three Latin American countries that straddle the equator:
            Brazil, Ecuador, and Colombia.
            """
        )
