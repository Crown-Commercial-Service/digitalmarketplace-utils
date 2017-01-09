# -*- coding: utf-8 -*-
"""Digital Marketplace Mandrill integration."""
import base64
import json
import struct
from datetime import datetime

import itsdangerous
import six
from cryptography import fernet
from flask import current_app
from flask._compat import string_types

from mandrill import Mandrill, Error
from dmutils.email.exceptions import EmailError
from dmutils.email.helpers import hash_string
from dmutils.formats import DATETIME_FORMAT

ONE_DAY_IN_SECONDS = 86400
SEVEN_DAYS_IN_SECONDS = 604800


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
        raise EmailError(e)

    logger.info("Sent {tags} response: id={id}, email={email_hash}",
                extra={'tags': tags, 'id': result[0]['_id'], 'email_hash': hash_string(result[0]['email'])})


def generate_token(data, secret_key, namespace):
    return encrypt_data(data, secret_key, namespace)


def decode_token(token, secret_key, namespace, max_age_in_seconds=86400):
    """
    Decode a token given a secret_key and namespace.

    The token may have been created by a previous version of dmutils, which only supported signed unencrypted tokens.
    To maintain backwards compatibility during rollouts, we try and decode using the old format, and if that fails
    assume it is is a new encrypted token.

    This functionality can be removed once all rollouts have completed and the longest time-to-live of the old signed
    tokens has expired (seven days for an invite email).
    """
    try:
        return decode_signed_token(token, secret_key, namespace, max_age_in_seconds)
    except itsdangerous.BadData:
        return decrypt_data(token, secret_key, namespace, max_age_in_seconds)


def decode_signed_token(token, secret_key, namespace, max_age_in_seconds=86400):
    ts = itsdangerous.URLSafeTimedSerializer(secret_key)
    decoded, timestamp = ts.loads(
        token,
        salt=namespace,
        max_age=max_age_in_seconds,
        return_timestamp=True
    )
    return decoded, timestamp


def encrypt_data(json_data, secret_key, namespace):
    """
    Encrypt data using a provided secret_key and namespace.

    The process is as follows:
    * The secret_key is combined with the namespace and hashed using sha256. The namespace ensures that a token for
      `invite-user` cannot be re-used by an attacker on the `reset-password` endpoint. Hashing is used to ensure the
      key conforms to the 32 byte length requirement for Fernet.
    * The combined secret key is used to initialise the Fernet encryption algorithm. Fernet is a wrapper around AES
      that provides HMAC, TTL (time to live), and some quality of life features (url-safe base64 encoding)
      The fernet spec can be viewed here: https://github.com/fernet/spec/blob/master/Spec.md
    * The data is dumped from json and encrypted.
    * The output data is returned as a urlsafe_base64 (https://tools.ietf.org/html/rfc4648#section-5) unicode string.

    Fernet acepts and returns bytes, so call `.encode` before and `.decode` after to convert to strings, to ensure we
    use regular python strings for as much of the code flow as possible

    :param json_data: data to encrypt. Must be json-like blob that `json.dumps` will accept
    :param secret_key: The secret key to encrypt with. No length/content restrictions. Must be a string type.
    :param namespace: The namespace to encrypt with. No length/content restrictions. Must be a string type.
    :return: returns a urlsale_base64 encoded encrypted unicode string.
    :rtype: `unicode`
    """
    secret_key = hash_string(secret_key + namespace)
    data = json.dumps(json_data).encode('utf-8')
    f = fernet.Fernet(secret_key)
    return f.encrypt(data).decode('utf-8')


def decrypt_data(encrypted_data, secret_key, namespace, max_age_in_seconds):
    """
    Decrypt data using a provided secret_key, namespace, and TTL (max_age_in_seconds).

    The process is as follows:
    * secret key and fernet are initialised as in `encrypt_data`
    * the data is decrypted and json_dumped
    * the timestamp is pulled out and compared to the max_age_in_seconds to ensure that the token has not expired
    * the original json-able blob is returned, along with the timestamp that it was encrypted at. This timestamp can
      then be used for verifying the authenticity of the request, for example, comparing a password reset token
      against the last time the password was reset to ensure it is not used twice.

    Fernet acepts and returns bytes, so call `.encode` before and `.decode` after to convert to strings, to ensure we
    use regular python strings for as much of the code flow as possible

    :param encrypted_data: data to decrypt. Must be a string type.
    :param secret_key: The secret key you encrypted the data with. Must be a string type.
    :param namespace: The namespace you encrypted the data with. Must be a string type.
    :param max_age_in_seconds: The maximum age of the encrypted data.
    :return: the original encrypted data and the datetime it was encrypted at.
    :rtype: `tuple(json-able, datetime)`
    :raises fernet.InvalidToken: If the secret key and namespace are not able to decrypt the message,
        or max_age_in_seconds has been exceeded.
    """
    encrypted_bytes = encrypted_data.encode('utf-8')
    secret_key = hash_string(secret_key + namespace)
    f = fernet.Fernet(secret_key)

    # this raises fernet.InvalidToken if the key does not match or if TTL is exceeded
    data = f.decrypt(encrypted_bytes, ttl=max_age_in_seconds)

    timestamp = _parse_fernet_timestamp(encrypted_bytes)
    return json.loads(data.decode('utf-8')), timestamp


def _parse_fernet_timestamp(ciphertext):
    """
    Returns utc timestamp embedded in Fernet-encrypted ciphertext, converted to Python datetime object.

    Decryption should be attempted before using this function, as that does cryptographically strong tests on the
    validity of the ciphertext.
    """
    decoded = base64.urlsafe_b64decode(ciphertext)

    try:
        epoch_timestamp = struct.unpack('>Q', decoded[1:9])[0]
    except struct.error as e:
        raise fernet.InvalidToken(e.message)

    return datetime.utcfromtimestamp(epoch_timestamp)


def decode_password_reset_token(token, data_api_client):
    try:
        decoded, token_timestamp = decode_token(
            token,
            current_app.config["SECRET_KEY"],
            current_app.config["RESET_PASSWORD_SALT"],
            ONE_DAY_IN_SECONDS,
        )
    except fernet.InvalidToken as e:
        current_app.logger.info("Error changing password: {error}", extra={'error': six.text_type(e)})
        return {'error': 'token_invalid'}

    user = data_api_client.get_user(decoded["user"])
    user_last_changed_password_at = datetime.strptime(
        user['users']['passwordChangedAt'],
        DATETIME_FORMAT
    )

    # If the token was created before the last password change
    if token_timestamp < user_last_changed_password_at:
        current_app.logger.info("Error changing password: Token generated earlier than password was last changed.")
        return {'error': 'token_invalid'}

    return {
        'user': user['users']['id'],
        'email': user['users']['emailAddress']
    }


def decode_invitation_token(encoded_token):
    try:
        token, _ = decode_token(
            encoded_token,
            current_app.config['SHARED_EMAIL_KEY'],
            current_app.config['INVITE_EMAIL_SALT'],
            SEVEN_DAYS_IN_SECONDS
        )
        return token
    except fernet.InvalidToken as e:
        current_app.logger.info("Invitation reset attempt with expired token. error {error}",
                                extra={'error': six.text_type(e)})
        return None
