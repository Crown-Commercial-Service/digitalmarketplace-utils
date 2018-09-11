import mock
import pytest
from flask import session, current_app

from dmutils.config import init_app
from dmutils.email import send_user_account_email, EmailError
from dmutils.external import external as external_blueprint


@pytest.yield_fixture
def email_app(app):
    init_app(app)
    app.register_blueprint(external_blueprint)
    app.config['SHARED_EMAIL_KEY'] = 'shared_email_key'
    app.config['INVITE_EMAIL_SALT'] = 'invite_email_salt'
    app.config['SECRET_KEY'] = 'secet_key'
    app.config['DM_NOTIFY_API_KEY'] = 'dm_notify_api_key'
    app.config['NOTIFY_TEMPLATES'] = {'create_user_account': 'this-would-be-the-id-of-the-template'}
    yield app


class TestSendUserAccountEmail:

    def setup(self):
        self.generate_token_patch = mock.patch("dmutils.email.user_account_email.generate_token", autospec=True)
        self.notify_client_patch = mock.patch("dmutils.email.user_account_email.DMNotifyClient", autospec=True)

        self.generate_token = self.generate_token_patch.start()
        self.notify_client = self.notify_client_patch.start().return_value

    def teardown(self):
        self.notify_client_patch.stop()
        self.generate_token_patch.stop()

    def test_correctly_calls_notify_client_for_buyer(
        self, email_app
    ):
        with email_app.test_request_context():
            self.generate_token.return_value = 'mocked-token'

            send_user_account_email(
                'buyer',
                'test@example.gov.uk',
                current_app.config['NOTIFY_TEMPLATES']['create_user_account']
            )

            self.notify_client.send_email.assert_called_once_with(
                'test@example.gov.uk',
                template_name_or_id='this-would-be-the-id-of-the-template',
                personalisation={
                    'url': 'http://localhost/user/create/mocked-token'
                },
                reference='create-user-account-KmmJkEa5sLyv7vuxG3xja3S3fnnM6Rgq5EZY0S_kCjE='
            )
            assert session['email_sent_to'] == 'test@example.gov.uk'

    def test_correctly_calls_notify_client_for_supplier(
        self, email_app
    ):
        with email_app.test_request_context():
            self.generate_token.return_value = 'mocked-token'

            send_user_account_email(
                'supplier',
                'test@example.gov.uk',
                current_app.config['NOTIFY_TEMPLATES']['create_user_account'],
                extra_token_data={
                    'supplier_id': 12345,
                    'supplier_name': 'Digital Marketplace'
                },
                personalisation={
                    'user': 'Digital Marketplace Team',
                    'supplier': 'Digital Marketplace'
                }
            )

            self.notify_client.send_email.assert_called_once_with(
                'test@example.gov.uk',
                template_name_or_id=current_app.config['NOTIFY_TEMPLATES']['create_user_account'],
                personalisation={
                    'url': 'http://localhost/user/create/mocked-token',
                    'user': 'Digital Marketplace Team',
                    'supplier': 'Digital Marketplace'
                },
                reference='create-user-account-KmmJkEa5sLyv7vuxG3xja3S3fnnM6Rgq5EZY0S_kCjE='
            )
            assert session['email_sent_to'] == 'test@example.gov.uk'

    @mock.patch('dmutils.email.user_account_email.abort')
    def test_abort_with_503_if_send_email_fails_with_EmailError(self, abort, email_app):
        with email_app.test_request_context():
            self.notify_client.send_email.side_effect = EmailError('OMG!')

            send_user_account_email(
                'buyer',
                'test@example.gov.uk',
                current_app.config['NOTIFY_TEMPLATES']['create_user_account']
            )

            abort.assert_called_once_with(503, response="Failed to send user creation email.")
