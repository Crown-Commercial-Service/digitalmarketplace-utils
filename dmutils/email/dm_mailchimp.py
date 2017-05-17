# -*- coding: utf-8 -*-
"""Digital Marketplace MailChimp integration."""

from mailchimp3 import MailChimp
from requests.exceptions import RequestException
from hashlib import md5
import six


class DMMailChimpClient(object):

    def __init__(
        self,
        mailchimp_username,
        mailchimp_api_key,
        logger
    ):
        self.client = MailChimp(mailchimp_username, mailchimp_api_key)
        self.logger = logger

    @staticmethod
    def get_email_hash(email_address):
        """md5 hashing of lower cased emails has been chosen by mailchimp to identify email addresses"""
        formatted_email_address = six.text_type(email_address.lower()).encode('utf-8')
        return md5(formatted_email_address).hexdigest()

    def create_campaign(self, campaign_data):
        try:
            campaign = self.client.campaigns.create(campaign_data)
            return campaign['id']
        except RequestException as e:
            self.logger.error(
                "Mailchimp failed to create campaign for '{0}'".format(
                    campaign_data.get("settings").get("title")
                ),
                extra={"error": str(e)}
            )
        return False

    def set_campaign_content(self, campaign_id, content_data):
        try:
            return self.client.campaigns.content.update(campaign_id, content_data)
        except RequestException as e:
            self.logger.error(
                "Mailchimp failed to set content for campaign id '{0}'".format(campaign_id),
                extra={"error": str(e)}
            )
        return False

    def send_campaign(self, campaign_id):
        try:
            self.client.campaigns.actions.send(campaign_id)
            return True
        except RequestException as e:
            self.logger.error(
                "Mailchimp failed to send campaign id '{0}'".format(campaign_id),
                extra={"error": str(e)}
            )
        return False

    def subscribe_new_email_to_list(self, list_id, email_address):
        """ Will subscribe email address to list if they do not already exist in that list else do nothing"""
        hashed_email = self.get_email_hash(email_address)
        try:
            return self.client.lists.members.create_or_update(
                list_id,
                hashed_email,
                {
                    "email_address": email_address,
                    "status_if_new": "subscribed"
                }
            )
        except RequestException as e:
            # As defined in mailchimp API documentation, this particular error message may arise if a user has requested
            # mailchimp to never add them to mailchimp lists. In this case, we resort to allowing a failed API call (but
            # log) as a user of this method would unlikely be able to do anything as we have no control over this
            # behaviour.
            if "looks fake or invalid, please enter a real email address." in e.response.json()["detail"]:
                self.logger.error(
                    "Expected error: Mailchimp failed to add user ({}) to list ({}). API error: The email address looks fake or invalid, please enter a real email address.".format(  # noqa
                        hashed_email,
                        list_id
                    ),
                    extra={"error": str(e)}
                )
                return True
            self.logger.error(
                "Mailchimp failed to add user ({}) to list ({})".format(
                    hashed_email,
                    list_id
                ),
                extra={"error": str(e)}
            )
            return False

    def subscribe_new_emails_to_list(self, list_id, email_addresses):
        success = True
        for email_address in email_addresses:
            if not self.subscribe_new_email_to_list(list_id, email_address):
                success = False
        return success

    def get_email_addresses_from_list(self, list_id):
        member_data = self.client.lists.members.all(list_id, get_all=True)
        return [member["email_address"] for member in member_data["members"]]
