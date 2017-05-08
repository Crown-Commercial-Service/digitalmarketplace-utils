# -*- coding: utf-8 -*-
"""Tests for the Digital Marketplace MailChimp integration."""
import mock

from dmutils.email.dm_mailchimp import DMMailChimpClient
from requests import RequestException


def test_create_campaign():
    dm_mailchimp_client = DMMailChimpClient('username', 'api key', 'logger')
    with mock.patch.object(dm_mailchimp_client.client.campaigns, 'create', autospec=True) as create:
        create.return_value = {"id": "100"}
        res = dm_mailchimp_client.create_campaign({"example": "data"})

        assert res == "100"
        create.assert_called_once_with({"example": "data"})


def test_log_error_message_if_error_creating_campaign():
    dm_mailchimp_client = DMMailChimpClient('username', 'api key', mock.MagicMock())
    with mock.patch.object(dm_mailchimp_client.client.campaigns, 'create', autospec=True) as create:
        create.side_effect = RequestException("error message")
        with mock.patch.object(dm_mailchimp_client.logger, 'error', autospec=True) as error:
            res = dm_mailchimp_client.create_campaign({"example": "data", 'settings': {'title': 'Foo'}})

            assert res is False
            error.assert_called_once_with(
                "Mailchimp failed to create campaign for 'campaign title'", extra={"error": "error message"}
            )


def test_set_campaign_content():
    dm_mailchimp_client = DMMailChimpClient('username', 'api key', 'logger')
    with mock.patch.object(dm_mailchimp_client.client.campaigns.content, 'update', autospec=True) as update:
        campaign_id = '1'
        html_content = {'html': '<p>One or two words</p>'}
        update.return_value = html_content
        res = dm_mailchimp_client.set_campaign_content(campaign_id, html_content)

        assert res == html_content
        dm_mailchimp_client.client.campaigns.content.update.assert_called_once_with(campaign_id, html_content)


def test_log_error_message_if_error_setting_campaign_content():
    dm_mailchimp_client = DMMailChimpClient('username', 'api key', mock.MagicMock())
    with mock.patch.object(dm_mailchimp_client.client.campaigns.content, 'update', autospec=True) as update:
        update.side_effect = RequestException("error message")

        with mock.patch.object(dm_mailchimp_client.logger, 'error', autospec=True) as error:
            res = dm_mailchimp_client.set_campaign_content('1', {"html": "some html"})

            assert res is False
            error.assert_called_once_with(
                "Mailchimp failed to set content for campaign id '1'", extra={"error": "error message"}
            )


def test_send_campaign():
    campaign_id = "1"
    dm_mailchimp_client = DMMailChimpClient('username', 'api key', mock.MagicMock())
    with mock.patch.object(dm_mailchimp_client.client.campaigns.actions, 'send', autospec=True) as send:
        res = dm_mailchimp_client.send_campaign(campaign_id)

        assert res is True
        send.assert_called_once_with(campaign_id)


def test_log_error_message_if_error_sending_campaign():
    dm_mailchimp_client = DMMailChimpClient('username', 'api key', mock.MagicMock())
    with mock.patch.object(dm_mailchimp_client.client.campaigns.actions, 'send',  autospec=True) as send:
        send.side_effect = RequestException("error sending")
        with mock.patch.object(dm_mailchimp_client.logger, 'error', autospec=True) as error:
            res = dm_mailchimp_client.send_campaign("1")

            assert res is False
            error.assert_called_once_with(
                "Mailchimp failed to send campaign id '1'", extra={"error": "error sending"}
            )
