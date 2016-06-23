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


def format_links(text):
    url_match = re.compile(r"""(
                                (?:https?://|www\.)       # start with http:// or www.
                                (?:[^\s/?\.#<>"']+\.?)+   # first part of host name
                                \.                        # match dot in host name
                                (?:[^\s/?\.#<>"']+\.?)+   # match rest of domain
                                (?:/[^\s<>"']*)?          # rest of url
                                [^\s<>,"'\.]              # no dot at end
                                )""", re.X)
    matched_urls = url_match.findall(text)
    if matched_urls:
        link = '<a href="{0}" rel="external">{1}</a>'
        formatted_text = ""
        text_array = url_match.split(text)
        formatted_text_array = []
        for partial_text in text_array:
            if partial_text in matched_urls:
                url = "https://{}".format(partial_text) if partial_text.startswith('www') else partial_text
                url = link.format(Markup.escape(url), Markup.escape(partial_text))
                formatted_text_array.append(url)
            else:
                partial_text = Markup.escape(partial_text)
                formatted_text_array.append(partial_text)
        formatted_text = Markup(''.join(formatted_text_array))
        return formatted_text
    else:
        return text
