from __future__ import unicode_literals
import re
from flask import Markup, escape
from six import string_types


def smartjoin(input):
    list_to_join = list(input)
    if len(list_to_join) > 1:
        return '{} and {}'.format(', '.join(list_to_join[:-1]), list_to_join[-1])
    elif len(list_to_join) == 1:
        return '{}'.format(list_to_join[0])
    else:
        return ''


def format_links(text):
    url_match = re.compile(r"""(
                                (?:https?://|www\.)    # start with http:// or www.
                                (?:[^\s<>"'/?#]+)      # domain doesn't have these characters
                                (?:[^\s<>"']+)         # post-domain part of URL doesn't have these characters
                                [^\s<>,"'\.]           # no dot at end
                                )""", re.X)
    matched_urls = url_match.findall(text)
    if matched_urls:
        link = '<a href="{0}" class="break-link" rel="external">{0}</a>'
        plaintext_link = '<span class="break-link">{0}</span>'
        text_array = url_match.split(text)
        formatted_text_array = []
        for partial_text in text_array:
            if partial_text in matched_urls:
                if partial_text.startswith('www'):
                    url = plaintext_link.format(Markup.escape(partial_text))
                else:
                    url = link.format(Markup.escape(partial_text))
                formatted_text_array.append(url)
            else:
                partial_text = Markup.escape(partial_text)
                formatted_text_array.append(partial_text)
        formatted_text = Markup(''.join(formatted_text_array))
        return formatted_text
    else:
        return text


def nbsp(text):
    """Replace spaces with nbsp.

    If you want to use html with this filter you need to pass it in as marksafe
    ie.
    {{ "some text and <html>"|marksafe|nbsp }}"""
    text = escape(text)
    return text.replace(' ', Markup('&nbsp;'))


def capitalize_first(maybe_text):
    """If it's a string capitalise the first character

    :param maybe_text: Could be anything
    :return: If maybe_text is a string it will be returned with an initial capital letter, otherwise unchanged
    """
    return maybe_text[0].capitalize() + maybe_text[1:] \
        if maybe_text and isinstance(maybe_text, string_types) \
        else maybe_text
