# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mock
import pytest

from flask import Markup

from dmutils.filters import capitalize_first, format_links, nbsp, smartjoin, preserve_line_breaks


def test_smartjoin_for_more_than_one_item():
    list_to_join = ['one', 'two', 'three', 'four']
    filtered_string = 'one, two, three and four'
    assert smartjoin(list_to_join) == filtered_string


def test_smartjoin_for_one_item():
    list_to_join = ['one']
    filtered_string = 'one'
    assert smartjoin(list_to_join) == filtered_string


def test_smartjoin_for_empty_list():
    list_to_join = []
    filtered_string = ''
    assert smartjoin(list_to_join) == filtered_string


def test_format_link():
    link = 'http://www.example.com'
    formatted_link = '<a href="http://www.example.com" class="break-link" rel="external">http://www.example.com</a>'
    assert format_links(link) == formatted_link


def test_format_link_without_protocol():
    link = 'www.example.com'
    formatted_link = '<span class="break-link">www.example.com</span>'
    assert format_links(link) == formatted_link


def test_format_link_with_text():
    text = 'This is the Greek Γ Δ Ε Ζ Η Θ Ι Κ Λ link: http://www.exΔmple.com'
    formatted_text = 'This is the Greek Γ Δ Ε Ζ Η Θ Ι Κ Λ link: <a href="http://www.exΔmple.com" class="break-link" rel="external">http://www.exΔmple.com</a>'  # noqa
    assert format_links(text) == formatted_text


def test_format_link_and_text_escapes_extra_html():
    text = 'This is the <strong>link</strong>: http://www.example.com'
    formatted_text = 'This is the &lt;strong&gt;link&lt;/strong&gt;: <a href="http://www.example.com" class="break-link" rel="external">http://www.example.com</a>'  # noqa
    assert format_links(text) == formatted_text


def test_format_link_does_not_die_horribly():
    text = 'This is the URL that made a previous regex die horribly' \
           'https://something&lt;span&gt;what&lt;/span&gt;something.com'
    formatted_text = 'This is the URL that made a previous regex die horribly' \
                     '<a href="https://something&amp;lt;span&amp;gt;what&amp;lt;/span&amp;gt;something.com" ' \
                     'class="break-link" rel="external">https://something&amp;lt;span&amp;gt;what&amp;lt;/span'\
                     '&amp;gt;something.com</a>'
    assert format_links(text) == formatted_text


def test_multiple_urls():
    text = 'This is the first link http://www.example.com and this is the second http://secondexample.com.'  # noqa
    formatted_text = 'This is the first link <a href="http://www.example.com" class="break-link" '\
        'rel="external">http://www.example.com</a> and this is the second '\
        '<a href="http://secondexample.com" class="break-link" rel="external">http://secondexample.com</a>.'
    assert format_links(text) == formatted_text


def test_no_links_no_change():
    text = 'There are no Greek Γ Δ Ε Ζ Η Θ Ι Κ Λ links.'
    assert format_links(text) == text


def test_nbsp():
    """Test that spaces are replaced with nbsp."""
    text = 'foo bar baz'
    expected = Markup('foo&nbsp;bar&nbsp;baz')
    result = nbsp(text)
    assert result == expected


def test_nbsp_escapes():
    """Ensure the filter escapes HTML."""
    text = 'foo bar baz <script>'
    expected = Markup('foo&nbsp;bar&nbsp;baz&nbsp;&lt;script&gt;')
    result = nbsp(text)
    assert result == expected


def test_nbsp_with_markup():
    """When markup passed in should still return markup."""
    text = Markup('foo bar baz <script>')
    expected = Markup('foo&nbsp;bar&nbsp;baz&nbsp;<script>')
    result = nbsp(text)
    assert result == expected


def test_capitalise_first_for_strings():
    assert capitalize_first('lowercase') == 'Lowercase'
    assert capitalize_first('UPPERCASE') == 'UPPERCASE'
    assert capitalize_first('_lower') == '_lower'
    assert capitalize_first('cAMELcASE??') == 'CAMELcASE??'


def test_capitalize_first_for_short_strings():
    assert capitalize_first('') == ''
    assert capitalize_first('a') == 'A'
    assert capitalize_first('B') == 'B'
    assert capitalize_first('+') == '+'


def test_capitalize_first_for_non_strings():
    assert capitalize_first(5) == 5
    assert capitalize_first(None) is None
    assert capitalize_first(True) is True
    assert capitalize_first(False) is False
    assert capitalize_first(['list', 'of', 'strings']) == ['List', 'Of', 'Strings']
    assert capitalize_first([{'list': 'of'}, 'things']) == [{'list': 'of'}, 'Things']
    assert capitalize_first({'this': 'thing'}) == {'this': 'thing'}
    assert capitalize_first('https://www.example.com') == 'https://www.example.com'


@pytest.mark.parametrize("bool", (False, True,))  # Shouldn't matter
def test_preserve_line_breaks(bool):
    assert preserve_line_breaks(mock.Mock(autoescape=bool), '\r\n', 'textbox_large') == '<br>'
    assert preserve_line_breaks(mock.Mock(autoescape=bool), '\r\n\r\n', 'textbox_large') == '<br><br>'
    assert preserve_line_breaks(mock.Mock(autoescape=bool), '\r\n \r\n \r\n', 'textbox_large') == '<br><br>'
    assert preserve_line_breaks(mock.Mock(autoescape=bool), '\r\n\r\n\r\n\r\n\r\n\r\n', 'textbox_large') == '<br><br>'
    assert preserve_line_breaks(mock.Mock(autoescape=bool), '', 'textbox_large') == ''
    assert preserve_line_breaks(mock.Mock(autoescape=bool), '\r\n<h2>', 'textbox_large') == '<br>&lt;h2&gt;'
    assert preserve_line_breaks(mock.Mock(autoescape=bool), 'You’ll be working', 'textbox_large') == 'You’ll be working'
    assert preserve_line_breaks(mock.Mock(autoescape=bool), '\n', 'textbox_large') == '\n'
    assert preserve_line_breaks(mock.Mock(autoescape=bool), '\r\n', 'not_textbox_large') == '\r\n'
    assert preserve_line_breaks(mock.Mock(autoescape=bool),
                                '\r\n\r\n  \r\n\r\n  \r\n\r\n', 'textbox_large') == '<br><br>'
