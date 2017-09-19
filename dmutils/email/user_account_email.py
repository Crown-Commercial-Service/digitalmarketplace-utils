from flask import current_app, session, abort
from . import DMNotifyClient, generate_token, EmailError
from .helpers import hash_string


class UserAccountEmail():

    def __init__(self, token_data, template_id):
        self.role = token_data['role']
        self.email_address = token_data['email_address']
        self.token = self._generate_create_token(token_data)
        self.template_id = template_id

    def send_email(self, personalisation):
        notify_client = DMNotifyClient(current_app.config['DM_NOTIFY_API_KEY'])

        try:
            notify_client.send_email(
                self.email_address,
                template_id=self.template_id,
                personalisation=personalisation,
                reference='create-user-account-{}'.format(hash_string(self.email_address))
            )
            session['email_sent_to'] = self.email_address
        except EmailError as e:
            current_app.logger.error(
                "{code}: Create user email for email_hash {email_hash} failed to send. Error: {error}",
                extra={
                    'error': str(e),
                    'email_hash': hash_string(self.email_address),
                    'code': '{}create.fail'.format(self.role)
                })
            abort(503, response="Failed to send user creation email.")

    def _generate_create_token(self, token_data):
        return generate_token(
            token_data,
            current_app.config['SHARED_EMAIL_KEY'],
            current_app.config['INVITE_EMAIL_SALT']
        )
