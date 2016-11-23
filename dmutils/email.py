import base64
import hashlib
import six

from flask import current_app, flash
from flask._compat import string_types

from datetime import datetime
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from mandrill import Mandrill, Error

from .formats import DATETIME_FORMAT

ONE_DAY_IN_SECONDS = 86400
SEVEN_DAYS_IN_SECONDS = 604800


class MandrillException(Exception):
    pass


def send_email(to_email_addresses, email_body, api_key, subject, from_email, from_name, tags, reply_to=None,
               metadata=None, logger=None):
    logger = logger or current_app.logger

    if isinstance(to_email_addresses, string_types):
        to_email_addresses = [to_email_addresses]

    try:
        mandrill_client = Mandrill(api_key)

        message = {
            'html': email_body,
            'subject': subject,
            'from_email': from_email,
            'from_name': from_name,
            'to': [{
                'email': email_address,
                'type': 'to'
            } for email_address in to_email_addresses],
            'important': False,
            'track_opens': False,
            'track_clicks': False,
            'auto_text': True,
            'tags': tags,
            'metadata': metadata,
            'headers': {'Reply-To': reply_to or from_email},
            'preserve_recipients': False,
            'recipient_metadata': [{
                'rcpt': email_address
            } for email_address in to_email_addresses]
        }

        result = mandrill_client.messages.send(message=message, async=True)
    except Error as e:
        # Mandrill errors are thrown as exceptions
        logger.error("Failed to send an email: {error}", extra={'error': e})
        raise MandrillException(e)

    logger.info("Sent {tags} response: id={id}, email={email_hash}",
                extra={'tags': tags, 'id': result[0]['_id'], 'email_hash': hash_email(result[0]['email'])})


def generate_token(data, secret_key, salt):
    ts = URLSafeTimedSerializer(secret_key)
    return ts.dumps(data, salt=salt)


def decode_token(token, secret_key, salt, max_age_in_seconds=86400):
    ts = URLSafeTimedSerializer(secret_key)
    decoded, timestamp = ts.loads(
        token,
        salt=salt,
        max_age=max_age_in_seconds,
        return_timestamp=True
    )
    return decoded, timestamp


def hash_email(email):
    m = hashlib.sha256()
    m.update(email.encode('utf-8'))

    return base64.urlsafe_b64encode(m.digest())


def decode_password_reset_token(token, data_api_client):
    try:
        decoded, timestamp = decode_token(
            token,
            current_app.config["SECRET_KEY"],
            current_app.config["RESET_PASSWORD_SALT"],
            ONE_DAY_IN_SECONDS
        )
    except SignatureExpired:
        current_app.logger.info("Password reset attempt with expired token.")
        return {'error': 'token_expired'}
    except BadSignature as e:
        current_app.logger.info("Error changing password: {error}", extra={'error': six.text_type(e)})
        return {'error': 'token_invalid'}

    user = data_api_client.get_user(decoded["user"])
    user_last_changed_password_at = datetime.strptime(
        user['users']['passwordChangedAt'],
        DATETIME_FORMAT
    )

    if token_created_before_password_last_changed(
            timestamp,
            user_last_changed_password_at
    ):
        current_app.logger.info("Error changing password: Token generated earlier than password was last changed.")
        return {'error': 'token_invalid'}

    return {
        'user': user['users']['id'],
        'email': user['users']['emailAddress']
    }


def decode_invitation_token(encoded_token, role):
    required_fields = ['email_address', 'supplier_id', 'supplier_name'] if role == 'supplier' else ['email_address']
    try:
        token, timestamp = decode_token(
            encoded_token,
            current_app.config['SHARED_EMAIL_KEY'],
            current_app.config['INVITE_EMAIL_SALT'],
            SEVEN_DAYS_IN_SECONDS
        )
        if all(field in token for field in required_fields):
            return token
        else:
            raise ValueError('Invitation token is missing required keys')
    except SignatureExpired as e:
        current_app.logger.info("Invitation attempt with expired token. error {error}",
                                extra={'error': six.text_type(e)})
        return None
    except BadSignature as e:
        current_app.logger.info("Invitation reset attempt with expired token. error {error}",
                                extra={'error': six.text_type(e)})
        return None
    except ValueError as e:
        current_app.logger.info("error {error}",
                                extra={'error': six.text_type(e)})
        return None


def token_created_before_password_last_changed(token_timestamp, user_timestamp):
    return token_timestamp < user_timestamp
