from dmutils.email import generate_token, decode_token
from itsdangerous import BadTimeSignature
import pytest


def test_can_generate_token():
    token = generate_token({
        "key1": "value1",
        "key2": "value2"},
        secret_key="1234567890",
        salt="1234567890")

    token, timestamp = decode_token(token, "1234567890", "1234567890")
    assert {
        "key1": "value1",
        "key2": "value2"} == token
    assert timestamp


def test_cant_decode_token_with_wrong_salt():
    token = generate_token({
        "key1": "value1",
        "key2": "value2"},
        secret_key="1234567890",
        salt="1234567890")

    with pytest.raises(BadTimeSignature) as error:
        decode_token(token, "1234567890", "failed")
    assert "does not match" in str(error.value)


def test_cant_decode_token_with_wrong_key():
    token = generate_token({
        "key1": "value1",
        "key2": "value2"},
        secret_key="1234567890",
        salt="1234567890")

    with pytest.raises(BadTimeSignature) as error:
        decode_token(token, "failed", "1234567890")
    assert "does not match" in str(error.value)
