# -*- coding: utf-8 -*-
"""Email helpers."""
import base64
import hashlib
import re


# List of characters that could be used to separate email addresses,
# in decreasing precedence order.
# Space (" ") should almost always be at the end of this list, otherwise
# it can cause weird issues when there are separators surrounded by space.
EMAIL_ADDRESS_SEPARATORS = [";", ",", "/", "&", " "]

# Largely copied from https://github.com/alphagov/notifications-utils/blob/\
#   67889886ec1476136d12e7f32787a7dbd0574cc2/notifications_utils/recipients.py
#
# regexes for use in validate_email_address.
# invalid local chars - whitespace, quotes and apostrophes, semicolons and colons, GBP sign
# Note: Normal apostrophe eg `Firstname-o'surname@domain.com` is allowed.
INVALID_LOCAL_CHARS = r"\s\",;:@£“”‘’"
email_regex = re.compile(r'^[^{}]+@([^.@][^@]+)$'.format(INVALID_LOCAL_CHARS))
hostname_part = re.compile(r'^(xn-|[a-z0-9]+)(-[a-z0-9]+)*$', re.IGNORECASE)
tld_part = re.compile(r'^([a-z]{2,63}|xn--([a-z0-9]+-)*[a-z0-9]+)$', re.IGNORECASE)


def hash_string(string):
    """Hash a given string."""
    m = hashlib.sha256(str(string).encode('utf-8'))
    return base64.urlsafe_b64encode(m.digest()).decode('utf-8')


def validate_email_address(email_address):
    """Return True if `email_address` is valid, otherwise returns False"""

    # Largely a straight copy from https://github.com/alphagov/notifications-utils/blob/\
    #   67889886ec1476136d12e7f32787a7dbd0574cc2/notifications_utils/recipients.py#L439 onwards so that we have
    # validity-parity with Notify and minimise nasty surprises once we attempt to send an email to this address via
    # Notify and only find out it won't be accepted once it's too late to give the user a sane validation message

    # almost exactly the same as by https://github.com/wtforms/wtforms/blob/master/wtforms/validators.py,
    # with minor tweaks for SES compatibility - to avoid complications we are a lot stricter with the local part
    # than neccessary - we don't allow any double quotes or semicolons to prevent SES Technical Failures
    email_address = (email_address or "").strip()
    match = re.match(email_regex, email_address)

    # not an email
    if not match:
        return False

    hostname = match.group(1)
    # don't allow consecutive periods in domain names
    if '..' in hostname:
        return False

    # idna = "Internationalized domain name" - this encode/decode cycle converts unicode into its accurate ascii
    # representation as the web uses. '例え.テスト'.encode('idna') == b'xn--r8jz45g.xn--zckzah'
    try:
        hostname = hostname.encode('idna').decode('ascii')
    except UnicodeError:
        return False

    parts = hostname.split('.')

    if len(hostname) > 253 or len(parts) < 2:
        return False

    for part in parts:
        if not part or len(part) > 63 or not hostname_part.match(part):
            return False

    # if the part after the last . is not a valid TLD then bail out
    if not tld_part.match(parts[-1]):
        return False

    return True


def get_email_addresses(string, separators=EMAIL_ADDRESS_SEPARATORS):
    """
    Returns a list of email addresses from a string.

    It does not validate the email addresses.

    @param separators   list of characters that could be
                        used to separate email addresses

    >>> from dmutils.email.helpers import get_email_addresses
    >>> get_email_addresses("bob@blob.com ")
    ['bob@blob.com']
    >>> get_email_addresses("bob@blob.com; bob.blob@job.com")
    ['bob@blob.com', 'bob.blob@job.com']
    >>> get_email_addresses("bob@blob.com /  bob.blob@job.com")
    ['bob@blob.com', 'bob.blob@job.com']
    >>> get_email_addresses("bob@invalid;bob.blob@job.com")
    ['bob@invalid', 'bob.blob@job.com']
    >>> get_email_addresses("bob@blob;bob.blob@job.com;bob@blob..invalid")
    ['bob@blob', 'bob.blob@job.com', 'bob@blob..invalid']
    >>> get_email_addresses("bob@blob & bob.blob@job.com")
    ['bob@blob', 'bob.blob@job.com']
    """

    addresses = [string]
    for sep in separators:
        if sep in string:
            addresses = string.split(sep)
            break  # earlier separators take precedence

    addresses = (s.strip() for s in addresses)
    addresses = [s for s in addresses if s]  # remove empty strings that can be left in by the algorithm

    return addresses
