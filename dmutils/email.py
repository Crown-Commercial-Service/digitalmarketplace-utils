from flask import url_for, current_app, render_template
import mandrill
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime
from dmutils.formats import DATETIME_FORMAT


def send_email(
        user_id,
        email_address,
        email_body,
        api_key,
        subject,
        from_email,
        from_name):
    try:
        mandrill_client = mandrill.Mandrill(api_key)

        message = {'html': email_body,
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


def generate_token(data, secret_key, salt):
    ts = URLSafeTimedSerializer(secret_key)
    return ts.dumps(data, salt=salt)


def decode_token(token, secret_key, salt):
    ts = URLSafeTimedSerializer(secret_key)
    decoded, timestamp = ts.loads(
        token,
        salt=salt,
        max_age=86400,
        return_timestamp=True
    )
    return decoded, timestamp


def token_created_before_password_last_changed(token_timestamp, user):

        password_last_changed = datetime.strptime(
            user['users']['passwordChangedAt'], DATETIME_FORMAT)
        return token_timestamp < password_last_changed
