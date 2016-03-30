from dmutils.flask_init import pluralize
import pytest


@pytest.mark.parametrize("count,singular,plural,output", [
    (0, "person", "people", "people"),
    (1, "person", "people", "person"),
    (2, "person", "people", "people"),
])
def test_pluralize(count, singular, plural, output):
    assert pluralize(count, singular, plural) == output
