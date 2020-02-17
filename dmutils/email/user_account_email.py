from warnings import warn

from flask import current_app, session, abort, url_for
from . import DMNotifyClient, generate_token, EmailError
from .helpers import hash_string


def send_user_account_email(role, email_address, template_name_or_id, extra_token_data={}, personalisation={}):
    notify_client = DMNotifyClient()

    token_data = {
        'role': role,
        'email_address': email_address
    }
    token_data.update(extra_token_data)

    token = generate_token(
        token_data,
        current_app.config['SHARED_EMAIL_KEY'],
        (
            current_app.config.get('INVITE_EMAIL_TOKEN_NS')
            or warn("INVITE_EMAIL_SALT has been renamed INVITE_EMAIL_TOKEN_NS", DeprecationWarning)
            or current_app.config['INVITE_EMAIL_SALT']
        ),
    )

    link_url = url_for('external.create_user', encoded_token=token, _external=True)

    personalisation_with_link = personalisation.copy()
    personalisation_with_link.update({'url': link_url})

    try:
        notify_client.send_email(
            email_address,
            template_name_or_id=template_name_or_id,
            personalisation=personalisation_with_link,
            reference='create-user-account-{}'.format(hash_string(email_address))
        )
        session['email_sent_to'] = email_address
    except EmailError:
        abort(503, response="Failed to send user creation email.")
