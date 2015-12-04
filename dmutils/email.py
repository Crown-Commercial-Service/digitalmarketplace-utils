import hashlib
import base64

from flask import current_app
from flask._compat import string_types
from mandrill import Mandrill, Error
from itsdangerous import URLSafeTimedSerializer


class MandrillException(Exception):
    pass


def send_email(to_email_addresses, email_body, api_key, subject, from_email, from_name, tags):
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
            'headers': {'Reply-To': from_email},
            'preserve_recipients': False,
            'recipient_metadata': [{
                'rcpt': email_address
            } for email_address in to_email_addresses]
        }

        result = mandrill_client.messages.send(message=message)
    except Error as e:
        # Mandrill errors are thrown as exceptions
        current_app.logger.error("A mandrill error occurred: {error}",
                                 extra={'error': e})
        raise MandrillException(e)

    current_app.logger.info("Sent {tags} response: id={id}, email={email_hash}",
                            extra={'tags': tags,
                                   'id': result[0]['_id'],
                                   'email_hash': hash_email(result[0]['email'])})


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
