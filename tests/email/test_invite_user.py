import mock
import pytest
from flask import session

from dmutils.config import init_app
from dmutils.email import InviteUser, EmailError
from dmutils.email.tokens import decode_invitation_token


@pytest.yield_fixture
def email_app(app):
    init_app(app)
    app.config['SHARED_EMAIL_KEY'] = 'shared_email_key'
    app.config['INVITE_EMAIL_SALT'] = 'invite_email_salt'
    app.config['SECRET_KEY'] = 'secet_key'
    app.config['DM_NOTIFY_API_KEY'] = 'dm_notify_api_key'
    app.config['NOTIFY_TEMPLATES'] = {'create_user_account': 'this-would-be-the-id-of-the-template'}
    yield app


class TestInviteUser():

    def test_InviteUser_object_creates_token_on_instantiation(self, email_app):
        with email_app.app_context():
            token_data = {
                'role': 'buyer',
                'email_address': 'test@example.gov.uk'
            }

            invite_user = InviteUser(token_data)

            assert decode_invitation_token(invite_user.token) == {
                'role': 'buyer',
                'email_address': 'test@example.gov.uk'
            }

    @mock.patch('dmutils.email.invite_user.DMNotifyClient')
    def test_send_invite_email_correctly_calls_notify_client(self, DMNotifyClient, email_app):
        with email_app.test_request_context():
            notify_client_mock = mock.Mock()
            DMNotifyClient.return_value = notify_client_mock

            token_data = {
                'role': 'buyer',
                'email_address': 'test@example.gov.uk'
            }

            invite_user = InviteUser(token_data)
            invite_user.send_invite_email('http://link.to./create-user')

            notify_client_mock.send_email.assert_called_once_with(
                'test@example.gov.uk',
                template_id='this-would-be-the-id-of-the-template',
                personalisation={
                    'url': 'http://link.to./create-user'
                },
                reference='create-user-account-KmmJkEa5sLyv7vuxG3xja3S3fnnM6Rgq5EZY0S_kCjE='
            )
            assert session['email_sent_to'] == 'test@example.gov.uk'

    @mock.patch('dmutils.email.invite_user.current_app')
    @mock.patch('dmutils.email.invite_user.abort')
    @mock.patch('dmutils.email.invite_user.DMNotifyClient')
    def test_abort_with_503_if_send_email_fails_with_EmailError(self, DMNotifyClient, abort, current_app, email_app):
        with email_app.test_request_context():
            notify_client_mock = mock.Mock()
            notify_client_mock.send_email.side_effect = EmailError('OMG!')
            DMNotifyClient.return_value = notify_client_mock

            token_data = {
                'role': 'buyer',
                'email_address': 'test@example.gov.uk'
            }

            invite_user = InviteUser(token_data)
            invite_user.send_invite_email('http://link.to./create-user')

            current_app.logger.error.assert_called_once_with(
                "{code}: Create user email for email_hash {email_hash} failed to send. Error: {error}",
                extra={
                    'error': 'OMG!',
                    'email_hash': 'KmmJkEa5sLyv7vuxG3xja3S3fnnM6Rgq5EZY0S_kCjE=',
                    'code': 'buyercreate.fail'
                }
            )
            abort.assert_called_once_with(503, response="Failed to send user creation email.")
