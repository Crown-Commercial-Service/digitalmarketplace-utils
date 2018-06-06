# -*- coding: utf-8 -*-
"""Digital Marketplace Notify integration."""
from flask import current_app
from notifications_python_client import NotificationsAPIClient
from notifications_python_client.errors import HTTPError

from dmutils.email.exceptions import EmailError
from dmutils.email.helpers import hash_string
from dmutils.timing import logged_duration_for_external_request as log_external_request


# These are listed here so that we have a central definition that can be imported and used by apps/scripts. These
# domains are *not* injected into all DMNotifyClients automatically.
DEFAULT_NOTIFY_REDIRECT_DOMAINS_TO_ADDRESS = {
    "example.com": "success@simulator.amazonses.com",
    "example.gov.uk": "success@simulator.amazonses.com",
    "user.marketplace.team": "success@simulator.amazonses.com",
}


class DMNotifyClient:
    """Digital Marketplace wrapper around the Notify python client."""

    _client_class = NotificationsAPIClient
    _sent_references_cache = None

    def __init__(
            self,
            govuk_notify_api_key,
            govuk_notify_base_url='https://api.notifications.service.gov.uk',
            logger=None,
            redirect_domains_to_address=None,
    ):
        """
            :param govuk_notify_api_key:
            :param govuk_notify_base_url:
            :param logger: logger to log progress to, taken from current_app if Falsey
            :param redirect_domains_to_address: dictionary mapping email domain to redirected email address - emails
                sent to a email with a domain in this mapping will instead be sent to the corresponding value set here.
                if `redirect_domains_to_address` is `None` will fall back to looking for a
                `DM_NOTIFY_REDIRECT_DOMAINS_TO_ADDRESS` setting in the current flask app's config (if available).
        """
        self.logger = logger or current_app.logger
        self.client = self._client_class(govuk_notify_api_key, govuk_notify_base_url)
        self._redirect_domains_to_address = (
            current_app.config.get("DM_NOTIFY_REDIRECT_DOMAINS_TO_ADDRESS")
            if current_app and redirect_domains_to_address is None else
            redirect_domains_to_address
        )

    def get_all_notifications(self, **kwargs):
        """Wrapper for notifications_python_client.notifications.NotificationsAPIClient::get_all_notifications"""
        with log_external_request(service='Notify'):
            return self.client.get_all_notifications(**kwargs)['notifications']

    def get_delivered_notifications(self, **kwargs):
        """Wrapper for notifications_python_client.notifications.NotificationsAPIClient::get_all_notifications"""
        return self.get_all_notifications(status='delivered', **kwargs)

    def get_delivered_references(self, invalidate_cache=False):
        """Get the references of all notifications that have already been delivered."""
        if invalidate_cache:
            self._sent_references_cache = None
        if self._sent_references_cache is None:
            self._sent_references_cache = set(i['reference'] for i in self.get_delivered_notifications())
        return self._sent_references_cache

    def _update_cache(self, reference):
        """If the cache has been instantiated then cache the new reference."""
        if self._sent_references_cache is not None:
            self._sent_references_cache.update([reference])

    def has_been_sent(self, reference):
        """Checks for a matching reference in our list of delivered references."""
        return reference in self.get_delivered_references()

    @staticmethod
    def get_reference(email_address, template_id, personalisation=None):
        """
        Method to return the standard reference given the variables the email is sent with.

        :param email_address: Emails recipient
        :param template_id: Emails template ID on Notify
        :param personalisation: Template parameters
        :return: Hashed string 'reference' to be passed to client.send_email_notification or self.send_email
        """
        personalisation_string = u','.join(
            list(map(lambda x: u'{}'.format(x), personalisation.values()))
        ) if personalisation else u''
        details_string = u'|'.join([email_address, template_id, personalisation_string])
        return hash_string(details_string)

    @staticmethod
    def get_error_message(email_address, error):
        """Format a logical error message from the error response."""
        messages = []
        message_prefix = u'Error sending message to {email_address}: '.format(email_address=email_address)
        message_string = u'{status_code} {error}: {message}'

        for message in error.message:
            format_kwargs = {
                'status_code': error.status_code,
                'error': message['error'],
                'message': message['message'],
            }
            messages.append(message_string.format(**format_kwargs))
        return message_prefix + u', '.join(messages)

    def send_email(self, email_address, template_id, personalisation=None, allow_resend=True, reference=None):
        """
        Method to send an email using the Notify api.

        :param email_address: String email address for recipient
        :param template_id: Template accessible on the Notify account whose  api_key you instantiated the class with
        :param personalisation: The template variables, dict
        :param allow_resend: if False instantiate the delivered reference cache and ensure we are not sending duplicates
        :return: response from the api. For more information see https://github.com/alphagov/notifications-python-client
        """
        reference = reference or self.get_reference(email_address, template_id, personalisation)
        if not allow_resend and self.has_been_sent(reference):
            self.logger.info(
                "Email {reference} (template {template_id}) has already been sent to {email_address} through Notify",
                extra=dict(
                    email_address=hash_string(email_address),
                    template_id=template_id,
                    reference=reference,
                ),
            )
            return

        # NOTE how the potential replacement of the email address happens *after* the has_been_sent check and
        # reference generation
        final_email_address = (
            self._redirect_domains_to_address
            and self._redirect_domains_to_address.get(
                # splitting at rightmost @ should reliably give us the domain
                email_address.rsplit("@", 1)[-1].lower()
            )
        ) or email_address

        try:
            with log_external_request(service='Notify'):
                response = self.client.send_email_notification(
                    final_email_address,
                    template_id,
                    personalisation=personalisation,
                    reference=reference,
                )

        except HTTPError as e:
            self.logger.error(self.get_error_message(hash_string(email_address), e))
            raise EmailError(str(e))

        self._update_cache(reference)

        return response
