from jinja2 import Markup, escape


def link_to(url, label='', **attrs):
    """Create a hyperlink with the given text pointing to the URL"""

    if url == '' or not isinstance(url, str):
        raise ValueError('link_to expects URL to be a non-empty string')

    if label == '' or label is None:
        label = url

    output = ['<a']
    output.append(f' href="{escape(url)}"')
    for key, value in attrs.items():
        if isinstance(value, str):
            output.append(' {}="{}"'.format(escape(key), escape(value)))
    output.append('>')
    output.append(escape(label))
    output.append('</a>')
    return Markup("".join(output))
