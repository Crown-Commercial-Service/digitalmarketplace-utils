# -*- coding: utf-8 -*-
"""Digital Marketplace MailChimp integration."""

from mailchimp3 import MailChimp
from requests.exceptions import RequestException
from hashlib import md5


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
        return md5(email_address).hexdigest()

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

    def subscribe_email_to_list(self, list_id, email_address):
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
            self.logger.error(
                "Mailchimp failed to send campaign id '{0}'".format(campaign_id),
                extra={"error": str(e)}
            )
        return False
