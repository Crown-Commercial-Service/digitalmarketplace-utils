from lxml import etree
import pytest

from dmutils.xmlutils import squashed_element_text, normalize_whitespace, squashed_normalized_text


_torture_xml = """
<one>
  <two language="pig-latin">
    Lorem  ipsum<three> dolor</three>,
    <four></four><five> </five>
  </two>
  sit &amp; 
\t  amet
</one>"""  # noqa


def test_squashed_element_text_torture():
    doc = etree.fromstring(_torture_xml)
    assert squashed_element_text(doc) == u"\n  \n    Lorem  ipsum dolor,\n     \n  \n  sit & \n\t  amet\n"
    elem_two = doc.xpath("//two")[0]
    assert squashed_element_text(elem_two) == u"\n    Lorem  ipsum dolor,\n     \n  "
    elem_three = doc.xpath("//three")[0]
    assert squashed_element_text(elem_three) == u" dolor"
    elem_four = doc.xpath("//four")[0]
    assert squashed_element_text(elem_four) == u""
    elem_five = doc.xpath("//five")[0]
    assert squashed_element_text(elem_five) == u" "


def test_squashed_normalized_text_torture():
    doc = etree.fromstring(_torture_xml)
    assert squashed_normalized_text(doc) == u"Lorem ipsum dolor, sit & amet"
    elem_two = doc.xpath("//two")[0]
    assert squashed_normalized_text(elem_two) == u"Lorem ipsum dolor,"
    elem_three = doc.xpath("//three")[0]
    assert squashed_normalized_text(elem_three) == u"dolor"
    elem_four = doc.xpath("//four")[0]
    assert squashed_normalized_text(elem_four) == u""
    elem_five = doc.xpath("//five")[0]
    assert squashed_normalized_text(elem_five) == u""
