# -*- coding: utf-8 -*-
"""Tests for the Digital Marketplace Mandrill integration."""

import logging
import mock
import pytest
import json

from dmutils.config import init_app
from dmutils.email.dm_mandrill import DMMandrillClient
from dmutils.email.exceptions import EmailError
from helpers import assert_external_service_log_entry, PatchExternalServiceLogConditionMixin


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


@pytest.fixture
def client():
    return DMMandrillClient('api_key', logger=logging.getLogger("mandrill"))


def _get_json_decode_error():
    try:
        json.loads('')
    except json.JSONDecodeError as e:
        return e


class TestMandrill(PatchExternalServiceLogConditionMixin):
    def setup(self):
        super().setup()
        self.logger = logging.getLogger('mandrill')

    def test_calls_send_email_with_correct_params(self, email_app, mandrill, client):
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

            with assert_external_service_log_entry(extra_modules=['mandrill']):
                client.send_email(
                    'email_address',
                    'from_email',
                    'from_name',
                    'body',
                    'subject',
                    ['password-resets'],
                )

            mandrill.messages.send.assert_called_once_with(message=expected_call, async=True)

    def test_calls_send_email_to_multiple_addresses(self, email_app, mandrill, client):
        with email_app.app_context():

            mandrill.messages.send.return_value = [
                {'_id': '123', 'email': '123'}]

            with assert_external_service_log_entry(extra_modules=['mandrill']):
                client.send_email(
                    ['email_address1', 'email_address2'],
                    'from_email',
                    'from_name',
                    'body',
                    'subject',
                    ['password-resets'],
                )

            assert mandrill.messages.send.call_args[1]['message']['to'] == [
                {'email': 'email_address1', 'type': 'to'},
                {'email': 'email_address2', 'type': 'to'},
            ]

            assert mandrill.messages.send.call_args[1]['message']['recipient_metadata'] == [
                {'rcpt': 'email_address1'},
                {'rcpt': 'email_address2'},
            ]

    def test_calls_send_email_with_alternative_reply_to(self, email_app, mandrill, client):
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

            with assert_external_service_log_entry(extra_modules=['mandrill']):
                client.send_email(
                    'email_address',
                    'from_email',
                    'from_name',
                    'body',
                    'subject',
                    ['password-resets'],
                    reply_to='reply_address',
                )

            mandrill.messages.send.assert_called_once_with(message=expected_call, async=True)

    @pytest.mark.parametrize("exception", [
        Exception('this is an error'),  # all exceptions should be caught and turned into an EmailError
        _get_json_decode_error(),  # but we are particularly interested in knowing that JSON errors are handled
    ])
    def test_should_throw_exception_if_mandrill_fails(self, email_app, mandrill, client, exception):
        with email_app.app_context():
            mandrill.messages.send.side_effect = exception

            with pytest.raises(EmailError) as e:
                with assert_external_service_log_entry(successful_call=False, extra_modules=['mandrill']):
                    client.send_email(
                        'email_address',
                        'from_email',
                        'from_name',
                        'body',
                        'subject',
                        ['password-resets'],
                    )

            assert e.value.__context__ == exception

    def test_calls_get_sent_emails_with_correct_params(self, email_app, mandrill, client):
        with email_app.app_context():
            mandrill.messages.search.return_value = [
                {'_id': '123', 'email': '123'}
            ]

            client.get_sent_emails(['password-resets'], date_from='2018-02-10')

            assert mandrill.messages.search.call_args_list == [
                mock.call(date_from='2018-02-10', limit=1000, tags=['password-resets'])
            ]
