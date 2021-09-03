# -*- coding: utf-8 -*-
"""Digital Marketplace MailChimp integration."""

from json.decoder import JSONDecodeError
from hashlib import md5
from logging import Logger
from typing import Callable, Iterator, Mapping, Sequence, Union, cast

from requests.exceptions import RequestException, HTTPError

from mailchimp3 import MailChimp
from mailchimp3.mailchimpclient import MailChimpError

from dmutils.timing import logged_duration_for_external_request as log_external_request

PAGINATION_SIZE = 1000


def get_response_from_exception(exc):
    if isinstance(exc, RequestException):
        try:
            return exc.response.json()
        except (AttributeError, ValueError, JSONDecodeError):
            pass
    if isinstance(exc, MailChimpError):
        return exc.args[0]
    return {}


class DMMailChimpClient(object):

    def __init__(
        self,
        mailchimp_username: str,
        mailchimp_api_key: str,
        logger: Logger,
        retries: int = 0,
    ):
        self._client = MailChimp(mc_user=mailchimp_username, mc_api=mailchimp_api_key, timeout=25)
        self.logger = logger
        self.retries = retries

    @staticmethod
    def get_email_hash(email_address: Union[str, bytes]) -> str:
        """md5 hashing of lower cased emails has been chosen by mailchimp to identify email addresses"""
        formatted_email_address = str(email_address.lower()).encode('utf-8')
        return md5(formatted_email_address).hexdigest()

    def timeout_retry(self, method: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            for i in range(1 + self.retries):
                try:
                    with log_external_request(service='Mailchimp'):
                        return method(*args, **kwargs)
                except HTTPError as e:
                    exception = e
                    if exception.response.status_code == 504:
                        continue
                    raise exception
            raise exception

        return wrapper

    def create_campaign(self, campaign_data: Mapping) -> Union[str, bool]:
        try:
            with log_external_request(service='Mailchimp'):
                campaign = self._client.campaigns.create(campaign_data)
            return cast(str, campaign['id'])
        except (RequestException, MailChimpError) as e:
            self.logger.error(
                "Mailchimp failed to create campaign for '{campaign_title}'".format(
                    campaign_title=campaign_data.get("settings", {}).get("title")
                ),
                extra={
                    "error": str(e),
                    "mailchimp_response": get_response_from_exception(e),
                },
            )
        return False

    def set_campaign_content(self, campaign_id: str, content_data: Mapping):
        try:
            with log_external_request(service='Mailchimp'):
                return self._client.campaigns.content.update(campaign_id, content_data)
        except (RequestException, MailChimpError) as e:
            self.logger.error(
                "Mailchimp failed to set content for campaign id '{0}'".format(campaign_id),
                extra={
                    "error": str(e),
                    "mailchimp_response": get_response_from_exception(e),
                },
            )
        return False

    def send_campaign(self, campaign_id: str):
        try:
            with log_external_request(service='Mailchimp'):
                self._client.campaigns.actions.send(campaign_id)
            return True
        except (RequestException, MailChimpError) as e:
            self.logger.error(
                "Mailchimp failed to send campaign id '{0}'".format(campaign_id),
                extra={
                    "error": str(e),
                    "mailchimp_response": get_response_from_exception(e),
                }
            )
        return False

    def subscribe_new_email_to_list(self, list_id: str, email_address: str):
        """
        Will subscribe email address to list if they do not already exist in that list else do nothing.
        Possible return values:
        True:          User error, e.g. already on list, fake/invalid email (status 4xx)
        False:         Unexpected error, e.g. cannot connect to Mailchimp (status 5xx)
        deleted_user:  Mailchimp can't subscribe a deleted user (status 400)
        anything else: User successfully subscribed (status 200)
        """
        hashed_email = self.get_email_hash(email_address)
        try:
            with log_external_request(service='Mailchimp'):
                resp = self._client.lists.members.create_or_update(
                    list_id,
                    hashed_email,
                    {
                        "email_address": email_address,
                        "status_if_new": "subscribed"
                    }
                )
                resp.update({"status": "success", "error_type": None, "status_code": 200})
                return resp
        except (RequestException, MailChimpError) as e:
            # Some errors we don't care about but do want to log. Find and log them here.
            response = get_response_from_exception(e)
            if "looks fake or invalid, please enter a real email address." in response.get("detail", ""):
                # As defined in mailchimp API documentation, this particular error message may arise if a user has
                # requested mailchimp to never add them to mailchimp lists. In this case, we resort to allowing a
                # failed API call (but log) as a user of this method would unlikely be able to do anything as we have
                # no control over this behaviour.
                self.logger.warning(
                    f"Expected error: Mailchimp failed to add user ({hashed_email}) to list ({list_id}). "
                    "API error: The email address looks fake or invalid, please enter a real email address.",
                    extra={"error": str(e), "mailchimp_response": response}
                )
                return {"status": "error", "error_type": "invalid_email", "status_code": 400}
            elif 'is already a list member.' in response.get("detail", ""):
                # If a user is already a list member we receive a 400 error as documented in the tests for this error
                self.logger.warning(
                    f"Expected error: Mailchimp failed to add user ({hashed_email}) to list ({list_id}). "
                    "API error: This email address is already subscribed.",
                    extra={"error": str(e), "mailchimp_response": response}
                )
                return {"status": "error", "error_type": "already_subscribed", "status_code": 400}
            elif 'The contact must re-subscribe to get back on the list.' in response.get('detail', ''):
                # User has been deleted and cannot be programmatically resubscribed
                self.logger.warning(
                    f"Expected error: Mailchimp cannot automatically subscribe user ({hashed_email}) to list "
                    f"({list_id}) as the user has been permanently deleted.",
                    extra={"error": str(e), "mailchimp_response": response}
                )
                return {"status": "error", "error_type": "deleted_user", "status_code": 400}
            elif response.get('status') == 400:
                # Some other validation error
                self.logger.warning(
                    f"Expected error: Mailchimp failed to add user ({hashed_email}) to list ({list_id}). "
                    "API error: The email address was invalid.",
                    extra={"error": str(e), "mailchimp_response": response}
                )
                return {"status": "error", "error_type": "invalid_email", "status_code": 400}

            # Otherwise this was an unexpected error and should be logged as such
            self.logger.error(
                f"Mailchimp failed to add user ({hashed_email}) to list ({list_id})",
                extra={"error": str(e), "mailchimp_response": response}
            )
            return {"status": "error", "error_type": "unexpected_error", "status_code": 500}

    def subscribe_new_emails_to_list(self, list_id: str, email_addresses: str) -> bool:
        success = True
        for email_address in email_addresses:
            with log_external_request(service='Mailchimp'):
                if not self.subscribe_new_email_to_list(list_id, email_address):
                    success = False
        return success

    def get_email_addresses_from_list(
            self,
            list_id: str,
            pagination_size: int = 100,
            **query_parameters,
    ) -> Iterator[str]:
        """
        See https://mailchimp.com/developer/marketing/api/list-members/list-members-info/ for possible query parameters.
        """
        offset = 0
        while True:
            member_data = self.timeout_retry(
                self._client.lists.members.all
            )(list_id, count=pagination_size, offset=offset, **query_parameters)
            if not member_data.get("members", None):
                break
            offset += pagination_size

            yield from [member['email_address'] for member in member_data['members']]

    def get_lists_for_email(self, email_address: str) -> Sequence[Mapping]:
        """
            Returns a sequence of all lists the email_address has an association with (note: even if that association is
            "unsubscribed" or "cleaned").
        """
        with log_external_request(service='Mailchimp'):
            return tuple(
                {
                    "list_id": mailing_list["id"],
                    "name": mailing_list["name"],
                } for mailing_list in self._client.lists.all(get_all=True, email=email_address)["lists"]
            )

    def permanently_remove_email_from_list(self, email_address: str, list_id: str) -> bool:
        """
            Permanently (very permanently) erases all trace of an email address from a given list
        """
        hashed_email = self.get_email_hash(email_address)
        try:
            with log_external_request(service='Mailchimp'):
                self._client.lists.members.delete_permanent(
                    list_id=list_id,
                    subscriber_hash=hashed_email,
                )
            return True
        except (RequestException, MailChimpError) as e:
            self.logger.error(
                f"Mailchimp failed to permanently remove user ({hashed_email}) from list ({list_id})",
                extra={"error": str(e), "mailchimp_response": get_response_from_exception(e)},
            )
        return False
