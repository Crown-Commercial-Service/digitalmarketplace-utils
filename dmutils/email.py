from flask import url_for, current_app, render_template
import mandrill
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime
from dmutils.formats import DATETIME_FORMAT


def send_password_email(
        user_id,
        email_address,
        locked,
        api_key,
        subject,
        from_email,
        from_name,
        secret_key,
        salt):
    try:
        mandrill_client = mandrill.Mandrill(api_key)
        url = generate_reset_url(user_id, email_address, secret_key, salt)
        body = render_template("emails/reset_password_email.html",
                               url=url, locked=locked)
        message = {'html': body,
                   'subject': subject,
                   'from_email': from_email,
                   'from_name': from_name,
                   'to': [{'email': email_address,
                           'name': 'Recipient Name',
                           'type': 'to'}],
                   'important': False,
                   'track_opens': None,
                   'track_clicks': None,
                   'auto_text': True,
                   'tags': ['password-resets'],
                   'headers': {'Reply-To': from_email},  # noqa
                   'recipient_metadata': [
                       {'rcpt': email_address,
                        'values': {'user_id': user_id}}]
        }
        result = mandrill_client.messages.send(message=message, async=False,
                                               ip_pool='Main Pool')
    except mandrill.Error as e:
        # Mandrill errors are thrown as exceptions
        current_app.logger.error("A mandrill error occurred: %s", e)
        return
    current_app.logger.info("Sent password email: %s", result)


def generate_reset_url(user_id, email_address, secret_key, salt):
    ts = URLSafeTimedSerializer(secret_key)
    token = ts.dumps(
        {
            "user": user_id,
            "email": email_address
        },
        salt=salt)
    url = url_for('main.reset_password', token=token, _external=True)
    current_app.logger.debug("Generated reset URL: %s", url)
    return url


def decode_email(token, key, salt):
    ts = URLSafeTimedSerializer(key)
    decoded = ts.loads(token,
                       salt=salt,
                       max_age=86400, return_timestamp=True)
    return decoded


def token_created_before_password_last_changed(token_timestamp, user):

        password_last_changed = datetime.strptime(
            user['users']['passwordChangedAt'], DATETIME_FORMAT)
        return token_timestamp < password_last_changed
