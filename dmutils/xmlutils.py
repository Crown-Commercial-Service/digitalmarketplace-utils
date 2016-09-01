import re


def squashed_element_text(element):
    """
        returns a concatenation of text contents of `element` and all its children
    """
    return (element.text or u"") + u"".join(
        squashed_element_text(child_element)+(child_element.tail or u"") for child_element in element
    )


_whitespace_re = re.compile(r"\s+", flags=re.UNICODE)


def normalize_whitespace(whitespace_in_this):
    """
        returns string with whitespace normalized (to single spaces, stripped at ends)

        Note proper xml-standard way of doing this is a little more complex afaik
    """
    return _whitespace_re.sub(" ", whitespace_in_this).strip()


def squashed_normalized_text(element):
    """
        A shortcut for `normalize_whitespace`-wrapped `squashed_element_text`
    """
    return normalize_whitespace(squashed_element_text(element))
