# -*- coding: utf-8 -*-
"""Tests for the Digital Marketplace MailChimp integration."""
import types

import mock
import pytest

from requests import RequestException
from requests.exceptions import HTTPError

from dmutils.email.dm_mailchimp import DMMailChimpClient


def test_create_campaign():
    dm_mailchimp_client = DMMailChimpClient('username', 'api key', 'logger')
    with mock.patch.object(dm_mailchimp_client._client.campaigns, 'create', autospec=True) as create:
        create.return_value = {"id": "100"}
        res = dm_mailchimp_client.create_campaign({"example": "data"})

        assert res == "100"
        create.assert_called_once_with({"example": "data"})


def test_log_error_message_if_error_creating_campaign():
    dm_mailchimp_client = DMMailChimpClient('username', 'api key', mock.MagicMock())
    with mock.patch.object(dm_mailchimp_client._client.campaigns, 'create', autospec=True) as create:
        create.side_effect = RequestException("error message")
        with mock.patch.object(dm_mailchimp_client.logger, 'error', autospec=True) as error:
            res = dm_mailchimp_client.create_campaign({"example": "data", 'settings': {'title': 'Foo'}})

            assert res is False
            error.assert_called_once_with(
                "Mailchimp failed to create campaign for 'campaign title'", extra={"error": "error message"}
            )


def test_set_campaign_content():
    dm_mailchimp_client = DMMailChimpClient('username', 'api key', 'logger')
    with mock.patch.object(dm_mailchimp_client._client.campaigns.content, 'update', autospec=True) as update:
        campaign_id = '1'
        html_content = {'html': '<p>One or two words</p>'}
        update.return_value = html_content
        res = dm_mailchimp_client.set_campaign_content(campaign_id, html_content)

        assert res == html_content
        dm_mailchimp_client._client.campaigns.content.update.assert_called_once_with(campaign_id, html_content)


@mock.patch("logging.Logger", autospec=True)
def test_log_error_message_if_error_setting_campaign_content(logger):
    dm_mailchimp_client = DMMailChimpClient('username', 'api key', logger)
    with mock.patch.object(dm_mailchimp_client._client.campaigns.content, 'update', autospec=True) as update:
        update.side_effect = RequestException("error message")

        res = dm_mailchimp_client.set_campaign_content('1', {"html": "some html"})

        assert res is False
        logger.error.assert_called_once_with(
            "Mailchimp failed to set content for campaign id '1'", extra={"error": "error message"}
        )


def test_send_campaign():
    campaign_id = "1"
    dm_mailchimp_client = DMMailChimpClient('username', 'api key', mock.MagicMock())
    with mock.patch.object(dm_mailchimp_client._client.campaigns.actions, 'send', autospec=True) as send:
        res = dm_mailchimp_client.send_campaign(campaign_id)

        assert res is True
        send.assert_called_once_with(campaign_id)


@mock.patch("logging.Logger", autospec=True)
def test_log_error_message_if_error_sending_campaign(logger):
    dm_mailchimp_client = DMMailChimpClient('username', 'api key', logger)
    with mock.patch.object(dm_mailchimp_client._client.campaigns.actions, 'send', autospec=True) as send:
        send.side_effect = RequestException("error sending")

        res = dm_mailchimp_client.send_campaign("1")

        assert res is False
        logger.error.assert_called_once_with(
            "Mailchimp failed to send campaign id '1'", extra={"error": "error sending"}
        )


@mock.patch("dmutils.email.dm_mailchimp.DMMailChimpClient.get_email_hash", return_value="foo")
def test_subscribe_new_email_to_list(get_email_hash):
    dm_mailchimp_client = DMMailChimpClient('username', 'api key', mock.MagicMock())
    with mock.patch.object(
            dm_mailchimp_client._client.lists.members, 'create_or_update', autospec=True) as create_or_update:

        create_or_update.return_value = {"response": "data"}
        res = dm_mailchimp_client.subscribe_new_email_to_list('list_id', 'example@example.com')

        assert res == {"response": "data"}
        create_or_update.assert_called_once_with(
            'list_id',
            "foo",
            {
                "email_address": "example@example.com",
                "status_if_new": "subscribed"
            }
        )


@mock.patch("logging.Logger", autospec=True)
@mock.patch("dmutils.email.dm_mailchimp.DMMailChimpClient.get_email_hash", return_value="foo")
def test_log_error_message_if_error_subscribing_email_to_list(get_email_hash, logger):
    dm_mailchimp_client = DMMailChimpClient('username', 'api key', logger)
    with mock.patch.object(
            dm_mailchimp_client._client.lists.members, 'create_or_update', autospec=True) as create_or_update:
        # The 400 response from MailChimp is actually falsey
        response = mock.MagicMock(__bool__=False)
        response.json.return_value = {"detail": "Unexpected error."}
        create_or_update.side_effect = RequestException("error sending", response=response)

        res = dm_mailchimp_client.subscribe_new_email_to_list('list_id', 'example@example.com')

        assert res is False
        logger.error.assert_called_once_with(
            "Mailchimp failed to add user (foo) to list (list_id)",
            extra={"error": "error sending"}
        )


@mock.patch("logging.Logger", autospec=True)
@mock.patch("dmutils.email.dm_mailchimp.DMMailChimpClient.get_email_hash", return_value="foo")
def test_returns_true_if_expected_error_subscribing_email_to_list(get_email_hash, logger):
    dm_mailchimp_client = DMMailChimpClient('username', 'api key', logger)
    with mock.patch.object(
            dm_mailchimp_client._client.lists.members, 'create_or_update', autospec=True) as create_or_update:
        response = mock.MagicMock(__bool__=False)
        response.json.return_value = {"detail": "foo looks fake or invalid, please enter a real email address."}
        create_or_update.side_effect = RequestException("error sending", response=response)

        res = dm_mailchimp_client.subscribe_new_email_to_list('list_id', 'example@example.com')

        assert res is True
        logger.error.assert_called_once_with(
            "Expected error: Mailchimp failed to add user (foo) to list (list_id). API error: The email address looks fake or invalid, please enter a real email address.",  # noqa
            extra={"error": "error sending"}
        )


def test_subscribe_new_emails_to_list():
    dm_mailchimp_client = DMMailChimpClient('username', 'api key', mock.MagicMock())
    with mock.patch.object(dm_mailchimp_client, 'subscribe_new_email_to_list', autospec=True):
        dm_mailchimp_client.subscribe_new_email_to_list.return_value = True
        res = dm_mailchimp_client.subscribe_new_emails_to_list('list_id', ['email1@example.com', 'email2@example.com'])
        calls = [mock.call('list_id', 'email1@example.com'), mock.call('list_id', 'email2@example.com')]

        assert res is True
        dm_mailchimp_client.subscribe_new_email_to_list.assert_has_calls(calls)


def test_subscribe_new_emails_to_list_tries_all_emails_returns_false_on_error():
    dm_mailchimp_client = DMMailChimpClient('username', 'api key', mock.MagicMock())
    with mock.patch.object(
            dm_mailchimp_client, 'subscribe_new_email_to_list', autospec=True) as subscribe_new_email_to_list:
        subscribe_new_email_to_list.side_effect = [False, True]
        res = dm_mailchimp_client.subscribe_new_emails_to_list('list_id', ['foo', 'email2@example.com'])
        calls = [mock.call('list_id', 'foo'), mock.call('list_id', 'email2@example.com')]

        assert res is False
        subscribe_new_email_to_list.assert_has_calls(calls)


def test_get_email_hash():
    assert DMMailChimpClient.get_email_hash("example@example.com") == '23463b99b62a72f26ed677cc556c44e8'


def test_get_email_hash_lowers():
    """Email must be lowercased before hashing as per api documentation."""
    DMMailChimpClient.get_email_hash("foo@EXAMPLE.com") == DMMailChimpClient.get_email_hash("foo@example.com")


def test_get_email_addresses_from_list_generates_emails():
    dm_mailchimp_client = DMMailChimpClient('username', 'api key', mock.MagicMock())
    with mock.patch.object(dm_mailchimp_client._client.lists.members, 'all', autospec=True) as all_members:

        all_members.side_effect = [
            {
                "members": [
                    {"email_address": "user1@example.com"},
                    {"email_address": "user2@example.com"},
                ]
            },
            {
                "members": []
            },
        ]

        res = dm_mailchimp_client.get_email_addresses_from_list('list_id')

        assert isinstance(res, types.GeneratorType)
        assert all_members.call_args_list == []

        assert list(res) == ["user1@example.com", "user2@example.com"]

        assert all_members.call_args_list == [
            mock.call('list_id', count=100, offset=0),
            mock.call('list_id', count=100, offset=100),
        ]


def test_default_timeout_retry_performs_no_retries():
    dm_mailchimp_client = DMMailChimpClient('username', 'api key', mock.MagicMock())
    with mock.patch.object(dm_mailchimp_client._client.lists.members, 'all', autospec=True) as all_members:
        all_members.side_effect = HTTPError(response=mock.Mock(status_code=504))
        with pytest.raises(HTTPError):
            list(dm_mailchimp_client.get_email_addresses_from_list('a_list_id'))
        assert all_members.call_args_list == [
            mock.call('a_list_id', count=100, offset=0),
        ]


def test_timeout_retry_performs_retries():
    dm_mailchimp_client = DMMailChimpClient('username', 'api key', mock.MagicMock(), retries=2)
    with mock.patch.object(dm_mailchimp_client._client.lists.members, 'all', autospec=True) as all_members:
        all_members.side_effect = HTTPError(response=mock.Mock(status_code=504))
        with pytest.raises(HTTPError):
            list(dm_mailchimp_client.get_email_addresses_from_list('a_list_id'))
        assert all_members.mock_calls == [
            mock.call('a_list_id', count=100, offset=0),
            mock.call('a_list_id', count=100, offset=0),
            mock.call('a_list_id', count=100, offset=0),
        ]


def test_success_does_not_perform_retry():
    dm_mailchimp_client = DMMailChimpClient('username', 'api key', mock.MagicMock(), retries=2)
    with mock.patch.object(dm_mailchimp_client._client.lists.members, 'all', autospec=True) as all_members:
        all_members.side_effect = [
            {
                "members": [
                    {"email_address": "user1@example.com"},
                    {"email_address": "user2@example.com"},
                ]
            },
            {
                "members": []
            },
        ]
        list(dm_mailchimp_client.get_email_addresses_from_list('a_list_id'))
        assert all_members.mock_calls == [
            mock.call('a_list_id', count=100, offset=0),
            mock.call('a_list_id', count=100, offset=100),
        ]


def test_offset_increments_until_no_members():
    dm_mailchimp_client = DMMailChimpClient('username', 'api key', mock.MagicMock())
    with mock.patch.object(dm_mailchimp_client._client.lists.members, 'all', autospec=True) as all_members:

        all_members.side_effect = [
            {"members": [{"email_address": "user1@example.com"}]},
            {"members": [{"email_address": "user2@example.com"}]},
            {"members": [{"email_address": "user3@example.com"}]},
            {"members": [{"email_address": "user4@example.com"}]},
            {"members": [{"email_address": "user5@example.com"}]},
            {"members": [{"email_address": "user6@example.com"}]},
            {"members": [{"email_address": "user7@example.com"}]},
            {"members": []},
        ]

        res = dm_mailchimp_client.get_email_addresses_from_list('a_list_id')

        assert list(res) == [
            "user1@example.com",
            "user2@example.com",
            "user3@example.com",
            "user4@example.com",
            "user5@example.com",
            "user6@example.com",
            "user7@example.com",
        ]

        assert all_members.call_args_list == [
            mock.call('a_list_id', count=100, offset=0),
            mock.call('a_list_id', count=100, offset=100),
            mock.call('a_list_id', count=100, offset=200),
            mock.call('a_list_id', count=100, offset=300),
            mock.call('a_list_id', count=100, offset=400),
            mock.call('a_list_id', count=100, offset=500),
            mock.call('a_list_id', count=100, offset=600),
            mock.call('a_list_id', count=100, offset=700),
        ]
