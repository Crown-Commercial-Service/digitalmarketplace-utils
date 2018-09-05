
import pytest

from dmutils.email.helpers import get_email_addresses


@pytest.mark.parametrize(
    ("multiple_email_addresses", "expected"), (
        ("grace.hopper@example.com",
            ["grace.hopper@example.com"]),
        ("sally_ride@space.example ",
            ["sally_ride@space.example"]),
        ("bob@blob.example / bob.blob@job.example",
            ["bob@blob.example", "bob.blob@job.example"]),
        ("annie.jump.cannon@example.email; mary.brück@email.example",
            ["annie.jump.cannon@example.email", "mary.brück@email.example"]),
        ("margrete.bose@physics.example,noether1882@erlangen.example,jocelyn.bell-burnell@lgm-1.example",
            ["margrete.bose@physics.example", "noether1882@erlangen.example", "jocelyn.bell-burnell@lgm-1.example"]),
        ("foobar / barfoo",
            ["foobar", "barfoo"]),
        ("bob@blob",
            ["bob@blob"]),
        ("bob@blob.com;bob.blob@job..com",
            ["bob@blob.com", "bob.blob@job..com"]),
        ("Please send emails to bob@blob.com",
            ["Please send emails to bob@blob.com"]),
    )
)
def test_get_email_addresses_returns_list_of_valid_email_addresses(multiple_email_addresses, expected):
    assert get_email_addresses(multiple_email_addresses) == expected
