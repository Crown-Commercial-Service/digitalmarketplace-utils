from markdown import markdown


def markdown_filter(text, *args, **kwargs):
    return markdown(text, *args, **kwargs)
