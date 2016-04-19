from dmutils.filters import markdown_filter


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
