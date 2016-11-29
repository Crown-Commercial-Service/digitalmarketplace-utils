# -*- coding: utf-8 -*-
from freezegun import freeze_time
import pytest
import mock
import base64

from datetime import datetime
from mandrill import Error
from cryptography import fernet

from itsdangerous import URLSafeTimedSerializer
from dmutils.config import init_app
from dmutils.email import (
    generate_token,
    decode_token,
    encrypt_data,
    send_email,
    MandrillException,
    hash_string,
    token_created_before_password_last_changed,
    decode_invitation_token,
    decode_password_reset_token,
    _parse_fernet_timestamp
)
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


@pytest.fixture
def data_api_client():
    user = user_json()
    user['users']['passwordChangedAt'] = "2016-01-01T12:00:00.30Z"
    data_api_client = mock.Mock()
    data_api_client.get_user.return_value = user
    return data_api_client


@pytest.fixture
def password_reset_token():
    return {'user': 123, 'email': 'test@example.com'}


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
            'metadata': None,
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


def test_calls_send_email_with_alternative_reply_to(email_app, mandrill):
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
            'metadata': None,
            'headers': {'Reply-To': "reply_address"},
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
            ["password-resets"],
            reply_to="reply_address"
        )

        mandrill.messages.send.assert_called_once_with(message=expected_call, async=True)


def test_should_throw_exception_if_mandrill_fails(email_app, mandrill):
    with email_app.app_context():

        mandrill.messages.send.side_effect = Error("this is an error")

        with pytest.raises(MandrillException) as e:
            send_email(
                "email_address",
                "body",
                "api_key",
                "subject",
                "from_email",
                "from_name",
                ["password-resets"]

            )
        assert str(e.value) == "this is an error"


def signed_token():
    ts = URLSafeTimedSerializer("1234567890")
    return ts.dumps({"key1": "value1", "key2": "value2"}, salt="0987654321")


def encrypted_token():
    return encrypt_data({"key1": "value1", "key2": "value2"}, secret_key="1234567890", namespace="0987654321")


@pytest.mark.parametrize('token', [signed_token, encrypted_token], ids=lambda x: x.__name__)
def test_can_generate_and_decode_token(token):
    with freeze_time('2016-01-01T12:00:00Z'):
        token, timestamp = decode_token(token(), "1234567890", "0987654321")
    assert token == {"key1": "value1", "key2": "value2"}
    assert timestamp == datetime(2016, 1, 1, 12, 0, 0)


def test_cant_decode_token_with_wrong_salt():
    token = generate_token({
        "key1": "value1",
        "key2": "value2"},
        secret_key="1234567890",
        namespace="1234567890")

    with pytest.raises(fernet.InvalidToken):
        decode_token(token, "1234567890", "failed")


def test_cant_decode_token_with_wrong_key():
    token = generate_token({
        "key1": "value1",
        "key2": "value2"},
        secret_key="1234567890",
        namespace="1234567890")

    with pytest.raises(fernet.InvalidToken):
        decode_token(token, "failed", "1234567890")


@pytest.mark.parametrize('test, expected', [
    (u'test@example.com', b'lz3-Rj7IV4X1-Vr1ujkG7tstkxwk5pgkqJ6mXbpOgTs='),
    (u'☃@example.com', b'jGgXle8WEBTTIFhP25dF8Ck-FxQSCZ_N0iWYBWve4Ps='),
])
def test_hash_string(test, expected):
    assert hash_string(test) == expected


def test_generate_token_does_not_contain_plaintext_email(email_app, data_api_client, password_reset_token):
    with email_app.app_context(), freeze_time('2016-01-01T12:00:00.30Z'):
        token = generate_token(password_reset_token, 'Secret', 'PassSalt')

    # a fernet string always starts with the version, which should be 128
    assert token[:4] == 'gAAA'

    token = token.encode('utf-8')

    # Personally identifiable information should not be readable without secret key
    assert b'test@example.com' not in base64.urlsafe_b64decode(token)

    # a fernet string contains the timestamp at which it was encrypted
    assert _parse_fernet_timestamp(token) == datetime(2016, 1, 1, 12)


def test_decrypt_token_ok_for_known_good_token():
    # encrypted on 2016-01-01T12:00:00.30Z with secret 'Secret' and namespace 'PassSalt'
    token = 'gAAAAABWhmpA1ecLpuzdKiIcJ_drdA1Vf4ip07TH3UqZ_fA-pD9yYlGMqSTi-Mpbd58Z-wlZfa5sXGE6FVHPilTpsZWEiMDRLdCBlccvBPbY9IOO5F3uabjkrk87mrlPxaSbMAza5Nku'  # noqa

    with freeze_time('2016-01-01T12:00:00.30Z'):
        data = decode_token(token, 'Secret', 'PassSalt')

    assert data == ({'email': 'test@example.com', 'user': 123}, datetime(2016, 1, 1, 12, 0, 0))


def test_decode_password_reset_token_ok_for_good_token(email_app, data_api_client, password_reset_token):
    with email_app.app_context():
        token = generate_token(password_reset_token, 'Secret', 'PassSalt')
        assert decode_password_reset_token(token, data_api_client) == password_reset_token
    data_api_client.get_user.assert_called_once_with(123)


def test_decode_password_reset_token_does_not_work_if_bad_token(email_app, data_api_client, password_reset_token):
    token = generate_token(password_reset_token, 'Secret', 'PassSalt')[1:]

    with email_app.app_context():
        assert decode_password_reset_token(token, data_api_client) == {'error': 'token_invalid'}


def test_decode_password_reset_token_does_not_work_if_token_expired(email_app, data_api_client, password_reset_token):
    with freeze_time('2015-01-02 03:04:05'):
        # Token was generated a year before current time
        token = generate_token(password_reset_token, 'Secret', 'PassSalt')

    with freeze_time('2016-01-02 03:04:05'):
        with email_app.app_context():
            assert decode_password_reset_token(token, data_api_client) == {'error': 'token_invalid'}


def test_decode_password_reset_token_does_not_work_if_password_changed_later_than_token(
    email_app, data_api_client, password_reset_token
):
    with freeze_time('2016-01-01T11:00:00.30Z'):
        # Token was generated an hour earlier than password was changed
        token = generate_token(password_reset_token, 'Secret', 'PassSalt')

    with freeze_time('2016-01-01T13:00:00.30Z'):
        # Token is two hours old; password was changed an hour ago
        with email_app.app_context():
            assert decode_password_reset_token(token, data_api_client) == {'error': 'token_invalid'}


def test_decode_invitation_token_decodes_ok(email_app):
    with email_app.app_context():
        # works with arbitrary fields
        data = {'email_address': 'test-user@email.com', 'supplier_id': 1234, 'foo': 'bar'}
        token = generate_token(data, 'Key', 'Salt')
        assert decode_invitation_token(token) == data


def test_decode_invitation_token_does_not_work_if_bad_token(email_app):
    with email_app.app_context():
        data = {'email_address': 'test-user@email.com', 'supplier_name': 'A. Supplier'}
        token = generate_token(data, email_app.config['SHARED_EMAIL_KEY'], email_app.config['INVITE_EMAIL_SALT'])[1:]

        assert decode_invitation_token(token) is None


def test_decode_invitation_token_does_not_work_if_token_expired(email_app):
    with freeze_time('2015-01-02 03:04:05'):
        data = {'email_address': 'test-user@email.com', 'supplier_name': 'A. Supplier'}
        token = generate_token(data, email_app.config['SHARED_EMAIL_KEY'], email_app.config['INVITE_EMAIL_SALT'])
    with email_app.app_context():

        assert decode_invitation_token(token) is None


def test_token_created_before_password_last_changed():
    january_first = datetime.strptime("2016-01-01T12:00:00.30Z", DATETIME_FORMAT)
    january_second = datetime.strptime("2016-02-01T12:00:00.30Z", DATETIME_FORMAT)

    assert token_created_before_password_last_changed(january_first, january_second) is True
    assert token_created_before_password_last_changed(january_second, january_first) is False
