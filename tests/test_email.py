# -*- coding: utf-8 -*-
from dmutils.email import generate_token, decode_token, \
    send_email, MandrillException, hash_email
from itsdangerous import BadTimeSignature
import pytest
import mock
import six
from dmutils.config import init_app
from mandrill import Error


@pytest.yield_fixture
def mandrill():
    with mock.patch('dmutils.email.Mandrill') as Mandrill:
        instance = Mandrill.return_value
        yield instance


@pytest.yield_fixture
def email_app(app):
    init_app(app)
    yield app


def test_calls_send_email_with_correct_params(email_app, mandrill):
    with email_app.app_context():

        mandrill.messages.send.return_value = [
            {'_id': '123', 'email': '123'}]

        expected_call = {
            'html': "body",
            'subject': "subject",
            'from_email': "from_email",
            'from_name': "from_name",
            'to': [{
                'email': "email_address",
                'name': 'Recipient Name',
                'type': 'to'
            }],
            'important': False,
            'track_opens': None,
            'track_clicks': None,
            'auto_text': True,
            'tags': ['password-resets'],
            'headers': {'Reply-To': "from_email"},  # noqa
            'recipient_metadata': [{
                'rcpt': "email_address"
            }]
        }

        send_email(
            "email_address",
            "body",
            "api_key",
            "subject",
            "from_email",
            "from_name",
            ["password-resets"]

        )

        mandrill.messages.send.assert_called_once_with(
            message=expected_call,
            async=False,
            ip_pool='Main Pool'
        )


def test_should_throw_exception_if_mandrill_fails(email_app, mandrill):
    with email_app.app_context():

        mandrill.messages.send.side_effect = Error("this is an error")

        try:
            send_email(
                "email_address",
                "body",
                "api_key",
                "subject",
                "from_email",
                "from_name",
                ["password-resets"]

            )
        except MandrillException as e:
            assert str(e) == "this is an error"


def test_can_generate_token():
    token = generate_token({
        "key1": "value1",
        "key2": "value2"},
        secret_key="1234567890",
        salt="1234567890")

    token, timestamp = decode_token(token, "1234567890", "1234567890")
    assert {
        "key1": "value1",
        "key2": "value2"} == token
    assert timestamp


def test_cant_decode_token_with_wrong_salt():
    token = generate_token({
        "key1": "value1",
        "key2": "value2"},
        secret_key="1234567890",
        salt="1234567890")

    with pytest.raises(BadTimeSignature) as error:
        decode_token(token, "1234567890", "failed")
    assert "does not match" in str(error.value)


def test_cant_decode_token_with_wrong_key():
    token = generate_token({
        "key1": "value1",
        "key2": "value2"},
        secret_key="1234567890",
        salt="1234567890")

    with pytest.raises(BadTimeSignature) as error:
        decode_token(token, "failed", "1234567890")
    assert "does not match" in str(error.value)


def test_hash_email():
    tests = [
        (u'test@example.com', six.b('lz3-Rj7IV4X1-Vr1ujkG7tstkxwk5pgkqJ6mXbpOgTs=')),
        (u'☃@example.com', six.b('jGgXle8WEBTTIFhP25dF8Ck-FxQSCZ_N0iWYBWve4Ps=')),
    ]

    for test, expected in tests:
        assert hash_email(test) == expected
