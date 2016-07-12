from __future__ import unicode_literals
import re
from markdown import markdown
from flask import Markup


def markdown_filter(text, *args, **kwargs):
    return markdown(text, ['markdown.extensions.abbr'], *args, **kwargs)


def smartjoin(input):
    list_to_join = list(input)
    if len(list_to_join) > 1:
        return '{} and {}'.format(', '.join(list_to_join[:-1]), list_to_join[-1])
    elif len(list_to_join) == 1:
        return '{}'.format(list_to_join[0])
    else:
        return ''


def format_links(text, link_classes=("urlized-link",), plaintext_link_classes=("urlized-plaintext-link",)):
    """
        Replaces apparent urls in plaintext `text` with <a href="..."> elements, applying `link_classes` to the
        resulting elements.

        Apparent pseudo-urls (url-like substrings missing the scheme (beginning "www") are wrapped in a <span> element
        to which `plaintext_link_classes` are applied.

        `link_classes` and `plaintext_link_classes` are expected to be valid sensible html class names
    """
    url_match = re.compile(r"""(
                                (?:https?://|www\.)    # start with http:// or www.
                                (?:[^\s<>"'/?#]+)      # domain doesn't have these characters
                                (?:[^\s<>"']+)         # post-domain part of URL doesn't have these characters
                                [^\s<>,"'\.]           # no dot at end
                                )""", re.X)
    matched_urls = url_match.findall(text)
    if matched_urls:
        link = '<a href="{0}" class="{1}" rel="external">{0}</a>'
        plaintext_link = '<span class="{1}">{0}</span>'
        joined_link_classes = " ".join(link_classes)
        joined_plaintext_link_classes = " ".join(plaintext_link_classes)
        text_array = url_match.split(text)
        formatted_text_array = []
        for partial_text in text_array:
            if partial_text in matched_urls:
                if partial_text.startswith('www'):
                    url = plaintext_link.format(Markup.escape(partial_text), joined_plaintext_link_classes)
                else:
                    url = link.format(Markup.escape(partial_text), joined_link_classes)
                formatted_text_array.append(url)
            else:
                partial_text = Markup.escape(partial_text)
                formatted_text_array.append(partial_text)
        formatted_text = Markup(''.join(formatted_text_array))
        return formatted_text
    else:
        return text
