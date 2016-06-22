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
                                [^\s<>,"'\.]               # no dot at end
                                )""", re.X)
    matches = url_match.findall(text)
    if matches:
        link = '{0}<a href={1} rel="external">{2}</a>'
        formattedText = ""
        textArray = url_match.split(text)
        for text in textArray:
            if text in matches:
                url = "http://{}".format(text) if text.startswith('www') else text
                formattedText = link.format(formattedText, Markup.escape(url), Markup.escape(text))
            else:
                formattedText = '{}{}'.format(formattedText, Markup.escape(text))
        formattedText = Markup(formattedText)
        return formattedText
    else:
        return text
