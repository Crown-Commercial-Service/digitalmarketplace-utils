# -*- coding: utf-8 -*-
"""Digital Marketplace Mandrill integration."""
from flask import current_app
from flask._compat import string_types

from mandrill import Mandrill
from dmutils.email.exceptions import EmailError
from dmutils.timing import logged_duration_for_external_request as log_external_request


class DMMandrillClient:
    def __init__(self, api_key=None, *, logger=None):
        if api_key is None:
            api_key = current_app.config["DM_MANDRILL_API_KEY"]

        self.logger = logger or current_app.logger
        self.client = Mandrill(api_key)

    def get_sent_emails(self, tags, date_from=None):
        return self.client.messages.search(tags=tags, date_from=date_from, limit=1000)

    def send_email(
        self,
        to_email_addresses,
        from_email_address,
        from_name,
        email_body,
        subject,
        tags,
        reply_to=None,
        metadata=None,
    ):
        if isinstance(to_email_addresses, string_types):
            to_email_addresses = [to_email_addresses]

        try:
            message = {
                'html': email_body,
                'subject': subject,
                'from_email': from_email_address,
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
                'headers': {'Reply-To': reply_to or from_email_address},
                'preserve_recipients': False,
                'recipient_metadata': [{
                    'rcpt': email_address
                } for email_address in to_email_addresses]
            }

            with log_external_request(service='Mandrill', logger=self.logger):
                result = self.client.messages.send(message=message, async=True)

        except Exception as e:
            # Anything that Mandrill throws will be rethrown in a manner consistent with out other email backends.
            # Note that this isn't just `mandrill.Error` exceptions, because the mandrill client also sometimes throws
            # things like JSONDecodeError (sad face).
            self.logger.error(
                "Error sending email: {error}",
                extra={
                    "client": self.client.__class__,
                    "error": e,
                    "tags": tags,
                },
            )
            raise EmailError(e)

        return result
