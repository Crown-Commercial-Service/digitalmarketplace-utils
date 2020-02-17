import base64
import json
import struct
from warnings import warn


from datetime import datetime, timedelta

from cryptography import fernet
from flask import current_app

from dmutils.formats import DATETIME_FORMAT
from dmutils.email.helpers import hash_string

ONE_DAY_IN_SECONDS = 86400
SEVEN_DAYS_IN_SECONDS = 604800


def generate_token(json_data, secret_key, namespace):
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
    f = fernet.Fernet(secret_key.encode('utf-8'))
    return f.encrypt(data).decode('utf-8')


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


def decode_token(encrypted_data, secret_key, namespace, max_age_in_seconds=ONE_DAY_IN_SECONDS):
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
    f = fernet.Fernet(secret_key.encode('utf-8'))

    # this raises fernet.InvalidToken if the key does not match or if TTL is exceeded
    data = f.decrypt(encrypted_bytes, ttl=max_age_in_seconds)

    timestamp = _parse_fernet_timestamp(encrypted_bytes)
    return json.loads(data.decode('utf-8')), timestamp


def decode_password_reset_token(token, data_api_client):
    try:
        decoded, token_timestamp = decode_token(
            token,
            current_app.config["SHARED_EMAIL_KEY"],
            (
                current_app.config.get('RESET_PASSWORD_TOKEN_NS')
                or warn("RESET_PASSWORD_SALT has been renamed RESET_PASSWORD_TOKEN_NS", DeprecationWarning)
                or current_app.config['RESET_PASSWORD_SALT']
            ),
            ONE_DAY_IN_SECONDS,
        )
    except fernet.InvalidToken as e:
        current_app.logger.info("Error changing password: {error}", extra={'error': str(e)})
        return {'error': 'token_invalid'}

    user = data_api_client.get_user(decoded["user"])
    user_last_changed_password_at = datetime.strptime(
        user['users']['passwordChangedAt'],
        DATETIME_FORMAT
    )

    if not user["users"]["active"]:
        current_app.logger.info("Error changing password: target user is not active.")
        return {'error': 'user_inactive'}

    # Check if the token was created before the last password change
    # (allow 1 second leeway for reset tokens generated for the 'Your password was changed' email link)
    if token_timestamp + timedelta(seconds=1) < user_last_changed_password_at:
        current_app.logger.info("Error changing password: Token generated earlier than password was last changed.")
        return {'error': 'token_invalid'}

    if token_timestamp > datetime.utcnow():
        current_app.logger.info("Error changing password: cannot use token generated in the future.")
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
            (
                current_app.config.get('INVITE_EMAIL_TOKEN_NS')
                or warn("INVITE_EMAIL_SALT has been renamed INVITE_EMAIL_TOKEN_NS", DeprecationWarning)
                or current_app.config['INVITE_EMAIL_SALT']
            ),
            SEVEN_DAYS_IN_SECONDS,
        )
        return token

    except fernet.InvalidToken as error:
        try:
            token, _ = decode_token(
                encoded_token,
                current_app.config['SHARED_EMAIL_KEY'],
                (
                    current_app.config.get('INVITE_EMAIL_TOKEN_NS')
                    or warn("INVITE_EMAIL_SALT has been renamed INVITE_EMAIL_TOKEN_NS", DeprecationWarning)
                    or current_app.config['INVITE_EMAIL_SALT']
                ),
                None,
            )

            current_app.logger.info("Invitation reset attempt with expired token. error {error}",
                                    extra={'error': str(error)})

            return {
                'error': 'token_expired',
                'role': token.get('role') or ('supplier' if token.get('supplier_id') else 'buyer')
            }

        except fernet.InvalidToken as invalid_token_error:
            current_app.logger.info("Invitation reset attempt with invalid token. error {error}",
                                    extra={'error': str(invalid_token_error)})

            return {'error': 'token_invalid'}
