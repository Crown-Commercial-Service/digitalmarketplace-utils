# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from dmutils.filters import markdown_filter, smartjoin, format_links


def test_markdown_filter_produces_markup():

    markdown_string = """## H2 title

- List item 1
- List item 2

Paragraph
**Bold**
*Emphasis*

HTML is an abbreviation.

*[HTML]: Hyper Text Markup Language
"""

    html_string = """<h2>H2 title</h2>
<ul>
<li>List item 1</li>
<li>List item 2</li>
</ul>
<p>Paragraph
<strong>Bold</strong>
<em>Emphasis</em></p>
<p><abbr title="Hyper Text Markup Language">HTML</abbr> is an abbreviation.</p>"""

    assert markdown_filter(markdown_string) == html_string


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
    formatted_link = '<a href="http://www.example.com" rel="external">http://www.example.com</a>'
    assert format_links(link) == formatted_link


def test_format_link_with_implied_protocol():
    link = 'www.example.com'
    formatted_link = '<a href="https://www.example.com" rel="external">www.example.com</a>'
    assert format_links(link) == formatted_link


def test_format_link_with_text():
    text = 'This is the Greek Γ Δ Ε Ζ Η Θ Ι Κ Λ link: http://www.exΔmple.com'
    formatted_text = 'This is the Greek Γ Δ Ε Ζ Η Θ Ι Κ Λ link: <a href="http://www.exΔmple.com" rel="external">http://www.exΔmple.com</a>'  # noqa
    assert format_links(text) == formatted_text


def test_format_link_and_text_escapes_extra_html():
    text = 'This is the <strong>link</strong>: http://www.example.com'
    formatted_text = 'This is the &lt;strong&gt;link&lt;/strong&gt;: <a href="http://www.example.com" rel="external">http://www.example.com</a>'  # noqa
    assert format_links(text) == formatted_text


def test_multiple_urls():
    text = 'This is the first link http://www.example.com and this is the second http://secondexample.com.'  # noqa
    formatted_text = 'This is the first link <a href="http://www.example.com" '\
        'rel="external">http://www.example.com</a> and this is the second '\
        '<a href="http://secondexample.com" rel="external">http://secondexample.com</a>.'
    assert format_links(text) == formatted_text


def test_no_links_no_change():
    text = 'There are no Greek Γ Δ Ε Ζ Η Θ Ι Κ Λ links.'
    assert format_links(text) == text
