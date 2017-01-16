# -*- coding: utf-8 -*-
"""Email helpers."""
import base64
import hashlib


def hash_string(string):
    """Hash a given string."""
    m = hashlib.sha256(string.encode('utf-8'))
    return base64.urlsafe_b64encode(m.digest())
