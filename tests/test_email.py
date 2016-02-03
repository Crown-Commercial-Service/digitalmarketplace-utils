# -*- coding: utf-8 -*-
from freezegun import freeze_time
import pytest
import mock
import six

from datetime import datetime
from itsdangerous import BadTimeSignature
from mandrill import Error

from dmutils.config import init_app
from dmutils.email import (
    generate_token, decode_token, send_email, MandrillException, hash_email,
    token_created_before_password_last_changed,
    decode_invitation_token, decode_password_reset_token)
from dmutils.formats import DATETIME_FORMAT
from .test_user import user_json


@pytest.yield_fixture
def mandrill():
    with mock.patch('dmutils.email.Mandrill') as Mandrill:
        instance = Mandrill.return_value
        yield instance


@pytest.yield_fixture
def email_app(app):
    init_app(app)
    app.config['SHARED_EMAIL_KEY'] = "Key"
    app.config['INVITE_EMAIL_SALT'] = "Salt"
    app.config['SECRET_KEY'] = "Secret"
    app.config["RESET_PASSWORD_SALT"] = "PassSalt"
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
                'type': 'to'
            }],
            'important': False,
            'track_opens': False,
            'track_clicks': False,
            'auto_text': True,
            'tags': ['password-resets'],
            'headers': {'Reply-To': "from_email"},  # noqa
            'preserve_recipients': False,
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

        mandrill.messages.send.assert_called_once_with(message=expected_call, async=True)


def test_calls_send_email_to_multiple_addresses(email_app, mandrill):
    with email_app.app_context():

        mandrill.messages.send.return_value = [
            {'_id': '123', 'email': '123'}]

        send_email(
            ["email_address1", "email_address2"],
            "body",
            "api_key",
            "subject",
            "from_email",
            "from_name",
            ["password-resets"]

        )

        assert mandrill.messages.send.call_args[1]['message']['to'] == [
            {'email': "email_address1", 'type': 'to'},
            {'email': "email_address2", 'type': 'to'},
        ]

        assert mandrill.messages.send.call_args[1]['message']['recipient_metadata'] == [
            {'rcpt': "email_address1"},
            {'rcpt': "email_address2"},
        ]


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


def test_decode_password_reset_token_ok_for_good_token(email_app):
    user = user_json()
    user['users']['passwordChangedAt'] = "2016-01-01T12:00:00.30Z"
    data_api_client = mock.Mock()
    data_api_client.get_user.return_value = user
    with email_app.app_context():
        data = {'user': 'test@example.com'}
        token = generate_token(data, 'Secret', 'PassSalt')
        assert decode_password_reset_token(token, data_api_client) == data


def test_decode_password_reset_token_does_not_work_if_bad_token(email_app):
    user = user_json()
    user['users']['passwordChangedAt'] = "2016-01-01T12:00:00.30Z"
    data_api_client = mock.Mock()
    data_api_client.get_user.return_value = user
    data = {'user': 'test@example.com'}
    token = generate_token(data, 'Secret', 'PassSalt')[1:]

    with email_app.app_context():
        assert decode_password_reset_token(token, data_api_client) == {'error': 'token_invalid'}


def test_decode_password_reset_token_does_not_work_if_token_expired(email_app):
    user = user_json()
    user['users']['passwordChangedAt'] = "2016-01-01T12:00:00.30Z"
    data_api_client = mock.Mock()
    data_api_client.get_user.return_value = user
    with freeze_time('2015-01-02 03:04:05'):
        # Token was generated a year before current time
        data = {'user': 'test@example.com'}
        token = generate_token(data, 'Secret', 'PassSalt')

    with freeze_time('2016-01-02 03:04:05'):
        with email_app.app_context():
            assert decode_password_reset_token(token, data_api_client) == {'error': 'token_expired'}


def test_decode_password_reset_token_does_not_work_if_password_changed_later_than_token(email_app):
    user = user_json()
    user['users']['passwordChangedAt'] = "2016-01-01T13:00:00.30Z"
    data_api_client = mock.Mock()
    data_api_client.get_user.return_value = user

    with freeze_time('2016-01-01T12:00:00.30Z'):
        # Token was generated an hour earlier than password was changed
        data = {'user': 'test@example.com'}
        token = generate_token(data, 'Secret', 'PassSalt')

    with freeze_time('2016-01-01T14:00:00.30Z'):
        # Token is two hours old; password was changed an hour ago
        with email_app.app_context():
            assert decode_password_reset_token(token, data_api_client) == {'error': 'token_invalid'}


def test_decode_invitation_token_decodes_ok_for_buyer(email_app):
    with email_app.app_context():
        data = {'email_address': 'test-user@email.com'}
        token = generate_token(data, 'Key', 'Salt')
        assert decode_invitation_token(token, role='buyer') == data


def test_decode_invitation_token_decodes_ok_for_supplier(email_app):
    with email_app.app_context():
        data = {'email_address': 'test-user@email.com', 'supplier_id': 1234, 'supplier_name': 'A. Supplier'}
        token = generate_token(data, 'Key', 'Salt')
        assert decode_invitation_token(token, role='supplier') == data


def test_decode_invitation_token_does_not_work_if_there_are_missing_keys(email_app):
    with email_app.app_context():
        data = {'email_address': 'test-user@email.com', 'supplier_name': 'A. Supplier'}
        token = generate_token(data, email_app.config['SHARED_EMAIL_KEY'], email_app.config['INVITE_EMAIL_SALT'])

        assert decode_invitation_token(token, role='supplier') is None


def test_decode_invitation_token_does_not_work_if_bad_token(email_app):
    with email_app.app_context():
        data = {'email_address': 'test-user@email.com', 'supplier_name': 'A. Supplier'}
        token = generate_token(data, email_app.config['SHARED_EMAIL_KEY'], email_app.config['INVITE_EMAIL_SALT'])[1:]

        assert decode_invitation_token(token, role='supplier') is None


def test_decode_invitation_token_does_not_work_if_token_expired(email_app):
    with freeze_time('2015-01-02 03:04:05'):
        data = {'email_address': 'test-user@email.com', 'supplier_name': 'A. Supplier'}
        token = generate_token(data, email_app.config['SHARED_EMAIL_KEY'], email_app.config['INVITE_EMAIL_SALT'])
    with email_app.app_context():

        assert decode_invitation_token(token, role='supplier') is None


def test_token_created_before_password_last_changed():
    january_first = datetime.strptime("2016-01-01T12:00:00.30Z", DATETIME_FORMAT)
    january_second = datetime.strptime("2016-02-01T12:00:00.30Z", DATETIME_FORMAT)

    assert token_created_before_password_last_changed(january_first, january_second) is True
    assert token_created_before_password_last_changed(january_second, january_first) is False
