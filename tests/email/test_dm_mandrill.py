# -*- coding: utf-8 -*-
"""Tests for the Digital Marketplace Mandrill integration."""

import mock
import pytest

from dmutils.config import init_app
from dmutils.email.dm_mandrill import send_email
from dmutils.email.exceptions import EmailError


@pytest.yield_fixture
def mandrill():
    with mock.patch('dmutils.email.dm_mandrill.Mandrill') as Mandrill:
        instance = Mandrill.return_value
        yield instance


@pytest.yield_fixture
def email_app(app):
    init_app(app)
    app.config['SHARED_EMAIL_KEY'] = 'Key'
    app.config['INVITE_EMAIL_SALT'] = 'Salt'
    app.config['SECRET_KEY'] = 'Secret'
    app.config['RESET_PASSWORD_SALT'] = 'PassSalt'
    yield app


def test_calls_send_email_with_correct_params(email_app, mandrill):
    with email_app.app_context():
        mandrill.messages.send.return_value = [
            {'_id': '123', 'email': '123'}
        ]

        expected_call = {
            'html': 'body',
            'subject': 'subject',
            'from_email': 'from_email',
            'from_name': 'from_name',
            'to': [{
                'email': 'email_address',
                'type': 'to'
            }],
            'important': False,
            'track_opens': False,
            'track_clicks': False,
            'auto_text': True,
            'tags': ['password-resets'],
            'headers': {'Reply-To': 'from_email'},  # noqa
            'metadata': None,
            'preserve_recipients': False,
            'recipient_metadata': [{
                'rcpt': 'email_address'
            }]
        }

        send_email(
            'email_address',
            'body',
            'api_key',
            'subject',
            'from_email',
            'from_name',
            ['password-resets']
        )

        mandrill.messages.send.assert_called_once_with(message=expected_call, async=True)


def test_calls_send_email_to_multiple_addresses(email_app, mandrill):
    with email_app.app_context():

        mandrill.messages.send.return_value = [
            {'_id': '123', 'email': '123'}]

        send_email(
            ['email_address1', 'email_address2'],
            'body',
            'api_key',
            'subject',
            'from_email',
            'from_name',
            ['password-resets']

        )

        assert mandrill.messages.send.call_args[1]['message']['to'] == [
            {'email': 'email_address1', 'type': 'to'},
            {'email': 'email_address2', 'type': 'to'},
        ]

        assert mandrill.messages.send.call_args[1]['message']['recipient_metadata'] == [
            {'rcpt': 'email_address1'},
            {'rcpt': 'email_address2'},
        ]


def test_calls_send_email_with_alternative_reply_to(email_app, mandrill):
    with email_app.app_context():
        mandrill.messages.send.return_value = [
            {'_id': '123', 'email': '123'}]

        expected_call = {
            'html': 'body',
            'subject': 'subject',
            'from_email': 'from_email',
            'from_name': 'from_name',
            'to': [{
                'email': 'email_address',
                'type': 'to'
            }],
            'important': False,
            'track_opens': False,
            'track_clicks': False,
            'auto_text': True,
            'tags': ['password-resets'],
            'metadata': None,
            'headers': {'Reply-To': 'reply_address'},
            'preserve_recipients': False,
            'recipient_metadata': [{
                'rcpt': 'email_address'
            }]
        }

        send_email(
            'email_address',
            'body',
            'api_key',
            'subject',
            'from_email',
            'from_name',
            ['password-resets'],
            reply_to='reply_address'
        )

        mandrill.messages.send.assert_called_once_with(message=expected_call, async=True)


def test_should_throw_exception_if_mandrill_fails(email_app, mandrill):
    with email_app.app_context():
        something_bad = Exception('this is an error')
        mandrill.messages.send.side_effect = something_bad

        with pytest.raises(EmailError) as e:
            send_email(
                'email_address',
                'body',
                'api_key',
                'subject',
                'from_email',
                'from_name',
                ['password-resets']

            )
        assert str(e.value) == 'this is an error'
        assert e.value.__context__ == something_bad
