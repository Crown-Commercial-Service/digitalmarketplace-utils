# -*- coding: utf-8 -*-
"""Digital Marketplace Mandrill integration."""
from flask import current_app
from flask._compat import string_types

from mandrill import Mandrill
from dmutils.email.exceptions import EmailError
from dmutils.email.helpers import hash_string
from dmutils.timing import logged_duration_for_external_request as log_external_request


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

        with log_external_request(service='Mandrill', logger=logger):
            result = mandrill_client.messages.send(message=message, async=True)

    except Exception as e:
        # Anything that Mandrill throws will be rethrown in a manner consistent with out other email backends.
        # Note that this isn't just `mandrill.Error` exceptions, because the mandrill client also sometimes throws
        # things like JSONDecodeError (sad face).
        logger.error("Failed to send an email: {error}", extra={'error': e})
        raise EmailError(e)

    logger.info("Sent {tags} response: id={id}, email={email_hash}",
                extra={'tags': tags, 'id': result[0]['_id'], 'email_hash': hash_string(result[0]['email'])})


def get_sent_emails(mandrill_api_key, tags, date_from=None):
    mandrill_client = Mandrill(mandrill_api_key)

    return mandrill_client.messages.search(tags=tags, date_from=date_from, limit=1000)
