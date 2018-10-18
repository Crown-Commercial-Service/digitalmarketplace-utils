# -*- coding: utf-8 -*-
"""Tests for the Digital Marketplace MailChimp integration."""
import logging
import types
from json.decoder import JSONDecodeError

import mock
import pytest

from requests import RequestException
from requests.exceptions import HTTPError

from dmutils.email.dm_mailchimp import DMMailChimpClient
from helpers import assert_external_service_log_entry, PatchExternalServiceLogConditionMixin


# Mailchimp client checks the first part of the key against a regex: ^[0-9a-f]{32}$
DUMMY_MAILCHIMP_API_KEY = "1234567890abcdef1234567890abcdef-us5"


class TestMailchimp(PatchExternalServiceLogConditionMixin):
    def test_create_campaign(self):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, 'logger')
        with mock.patch.object(dm_mailchimp_client._client.campaigns, 'create', autospec=True) as create:
            create.return_value = {"id": "100"}

            with assert_external_service_log_entry():
                res = dm_mailchimp_client.create_campaign({"example": "data"})

            assert res == "100"
            create.assert_called_once_with({"example": "data"})

    def test_log_error_message_if_error_creating_campaign(self):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, mock.MagicMock())
        with mock.patch.object(dm_mailchimp_client._client.campaigns, 'create', autospec=True) as create:
            create.side_effect = RequestException("error message")
            with mock.patch.object(dm_mailchimp_client.logger, 'error', autospec=True) as error:
                with assert_external_service_log_entry(successful_call=False):
                    res = dm_mailchimp_client.create_campaign({"example": "data", 'settings': {'title': 'Foo'}})

                assert res is False
                error.assert_called_once_with(
                    "Mailchimp failed to create campaign for 'campaign title'", extra={"error": "error message"}
                )

    def test_set_campaign_content(self):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, 'logger')
        with mock.patch.object(dm_mailchimp_client._client.campaigns.content, 'update', autospec=True) as update:
            campaign_id = '1'
            html_content = {'html': '<p>One or two words</p>'}
            update.return_value = html_content
            with assert_external_service_log_entry():
                res = dm_mailchimp_client.set_campaign_content(campaign_id, html_content)

            assert res == html_content
            dm_mailchimp_client._client.campaigns.content.update.assert_called_once_with(campaign_id, html_content)

    def test_log_error_message_if_error_setting_campaign_content(self):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, logging.getLogger('mailchimp'))
        with mock.patch.object(dm_mailchimp_client._client.campaigns.content, 'update', autospec=True) as update:
            update.side_effect = RequestException("error message")

            with assert_external_service_log_entry(successful_call=False, extra_modules=['mailchimp']) as log_catcher:
                res = dm_mailchimp_client.set_campaign_content('1', {"html": "some html"})

            assert res is False

            assert log_catcher.records[1].msg == "Mailchimp failed to set content for campaign id '1'"
            assert log_catcher.records[1].error == "error message"

    def test_send_campaign(self):
        campaign_id = "1"
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, mock.MagicMock())
        with mock.patch.object(dm_mailchimp_client._client.campaigns.actions, 'send', autospec=True) as send:
            with assert_external_service_log_entry():
                res = dm_mailchimp_client.send_campaign(campaign_id)

            assert res is True
            send.assert_called_once_with(campaign_id)

    def test_log_error_message_if_error_sending_campaign(self):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, logging.getLogger('mailchimp'))
        with mock.patch.object(dm_mailchimp_client._client.campaigns.actions, 'send', autospec=True) as send:
            send.side_effect = RequestException("error sending")

            with assert_external_service_log_entry(successful_call=False, extra_modules=['mailchimp']) as log_catcher:
                res = dm_mailchimp_client.send_campaign("1")

            assert res is False

            assert log_catcher.records[1].msg == "Mailchimp failed to send campaign id '1'"
            assert log_catcher.records[1].levelname == 'ERROR'
            assert log_catcher.records[1].error == "error sending"

    @mock.patch("dmutils.email.dm_mailchimp.DMMailChimpClient.get_email_hash", return_value="foo")
    def test_subscribe_new_email_to_list(self, get_email_hash):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, mock.MagicMock())
        with mock.patch.object(
                dm_mailchimp_client._client.lists.members, 'create_or_update', autospec=True) as create_or_update:

            create_or_update.return_value = {"response": "data"}
            with assert_external_service_log_entry():
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

    @mock.patch("dmutils.email.dm_mailchimp.DMMailChimpClient.get_email_hash", return_value="foo")
    def test_log_error_message_if_error_subscribing_email_to_list(self, get_email_hash):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, logging.getLogger('mailchimp'))
        with mock.patch.object(
                dm_mailchimp_client._client.lists.members, 'create_or_update', autospec=True) as create_or_update:
            # The 400 response from MailChimp is actually falsey
            response = mock.MagicMock(__bool__=False)
            response.json.return_value = {"detail": "Unexpected error."}
            create_or_update.side_effect = RequestException("error sending", response=response)

            with assert_external_service_log_entry(successful_call=False, extra_modules=['mailchimp']) as log_catcher:
                res = dm_mailchimp_client.subscribe_new_email_to_list('list_id', 'example@example.com')

            assert res is False

            assert log_catcher.records[1].msg == "Mailchimp failed to add user (foo) to list (list_id)"
            assert log_catcher.records[1].error == "error sending"
            assert log_catcher.records[1].levelname == 'ERROR'

    @mock.patch("dmutils.email.dm_mailchimp.DMMailChimpClient.get_email_hash", return_value="foo")
    def test_returns_true_if_expected_invalid_email_error_subscribing_email_to_list(self, get_email_hash):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, logging.getLogger('mailchimp'))
        with mock.patch.object(
                dm_mailchimp_client._client.lists.members, 'create_or_update', autospec=True) as create_or_update:
            response = mock.MagicMock(__bool__=False)
            response.json.return_value = {"detail": "foo looks fake or invalid, please enter a real email address."}
            create_or_update.side_effect = RequestException("error sending", response=response)

            with assert_external_service_log_entry(successful_call=False, extra_modules=['mailchimp']) as log_catcher:
                res = dm_mailchimp_client.subscribe_new_email_to_list('list_id', 'example@example.com')

            assert res is True
            assert log_catcher.records[1].msg == (
                "Expected error: Mailchimp failed to add user (foo) to list (list_id). "
                "API error: The email address looks fake or invalid, please enter a real email address."
            )
            assert log_catcher.records[1].error == "error sending"
            assert log_catcher.records[1].levelname == 'ERROR'

    @mock.patch("dmutils.email.dm_mailchimp.DMMailChimpClient.get_email_hash", return_value="foo")
    def test_returns_true_if_expected_already_subscribed_email_error(self, get_email_hash):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, logging.getLogger('mailchimp'))

        with mock.patch.object(
            dm_mailchimp_client._client.lists.members, 'create_or_update', autospec=True
        ) as create_or_update:

            response = mock.MagicMock(__bool__=False)
            expected_error = "user@example.com is already a list member. Use PUT to insert or update list members."

            response.status_code = 400
            response.message = (
                "Bad Request for url: https://us5.api.mailchimp.com/3.0/lists/list_id/members/member_id"
            )
            response.json.return_value = {"detail": expected_error}
            create_or_update.side_effect = HTTPError("400 Client Error", response=response)

            with assert_external_service_log_entry(successful_call=False, extra_modules=['mailchimp']) as log_catcher:
                res = dm_mailchimp_client.subscribe_new_email_to_list('list_id', 'example@example.com')

            assert res is True
            assert log_catcher.records[1].msg == (
                "Expected error: Mailchimp failed to add user (foo) to list (list_id). "
                "API error: This email address is already subscribed."
            )
            assert log_catcher.records[1].error == "400 Client Error"
            assert log_catcher.records[1].levelname == 'WARNING'

    @mock.patch("dmutils.email.dm_mailchimp.DMMailChimpClient.get_email_hash", return_value="foo")
    def test_handles_responses_with_invalid_json(self, get_email_hash):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, logging.getLogger('mailchimp'))
        with mock.patch.object(
                dm_mailchimp_client._client.lists.members, 'create_or_update', autospec=True) as create_or_update:
            response = mock.Mock()
            response.json.side_effect = JSONDecodeError('msg', 'doc', 0)
            create_or_update.side_effect = RequestException("error sending", response=response)

            with assert_external_service_log_entry(successful_call=False, extra_modules=['mailchimp']) as log_catcher:
                res = dm_mailchimp_client.subscribe_new_email_to_list('list_id', 'example@example.com')

            assert res is False
            assert log_catcher.records[1].msg == 'Mailchimp failed to add user (foo) to list (list_id)'
            assert log_catcher.records[1].error == "error sending"
            assert log_catcher.records[1].levelname == 'ERROR'

    def test_subscribe_new_emails_to_list(self):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, mock.MagicMock())
        with mock.patch.object(dm_mailchimp_client, 'subscribe_new_email_to_list', autospec=True, return_value=True):

            with assert_external_service_log_entry(count=2):
                res = dm_mailchimp_client.subscribe_new_emails_to_list(
                    'list_id',
                    ['email1@example.com', 'email2@example.com']
                )

            assert res is True
            assert dm_mailchimp_client.subscribe_new_email_to_list.call_args_list == [
                mock.call('list_id', 'email1@example.com'), mock.call('list_id', 'email2@example.com')
            ]

    def test_subscribe_new_emails_to_list_tries_all_emails_returns_false_on_error(self):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, mock.MagicMock())
        with mock.patch.object(
                dm_mailchimp_client, 'subscribe_new_email_to_list', autospec=True) as subscribe_new_email_to_list:
            subscribe_new_email_to_list.side_effect = [False, True]

            with assert_external_service_log_entry(count=2):
                res = dm_mailchimp_client.subscribe_new_emails_to_list('list_id', ['foo', 'email2@example.com'])

            calls = [mock.call('list_id', 'foo'), mock.call('list_id', 'email2@example.com')]

            assert res is False
            subscribe_new_email_to_list.assert_has_calls(calls)

    def test_get_email_hash(self):
        assert DMMailChimpClient.get_email_hash("example@example.com") == '23463b99b62a72f26ed677cc556c44e8'

    def test_get_email_hash_lowers(self):
        """Email must be lowercased before hashing as per api documentation."""
        assert DMMailChimpClient.get_email_hash("foo@EXAMPLE.com") == \
            DMMailChimpClient.get_email_hash("foo@example.com")

    def test_get_email_addresses_from_list_generates_emails(self):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, logging.getLogger('mailchimp'))
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

            with assert_external_service_log_entry(extra_modules=['mailchimp'], count=2):
                assert list(res) == ["user1@example.com", "user2@example.com"]

            assert all_members.call_args_list == [
                mock.call('list_id', count=100, offset=0),
                mock.call('list_id', count=100, offset=100),
            ]

    def test_default_timeout_retry_performs_no_retries(self):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, logging.getLogger('mailchimp'))
        with mock.patch.object(dm_mailchimp_client._client.lists.members, 'all', autospec=True) as all_members:
            all_members.side_effect = HTTPError(response=mock.Mock(status_code=504))
            with pytest.raises(HTTPError):
                with assert_external_service_log_entry(successful_call=False, extra_modules=['mailchimp']):
                    list(dm_mailchimp_client.get_email_addresses_from_list('a_list_id'))
            assert all_members.call_args_list == [
                mock.call('a_list_id', count=100, offset=0),
            ]

    def test_timeout_retry_performs_retries(self):
        dm_mailchimp_client = DMMailChimpClient(
            'username', DUMMY_MAILCHIMP_API_KEY, logging.getLogger('mailchimp'), retries=2
        )
        with mock.patch.object(dm_mailchimp_client._client.lists.members, 'all', autospec=True) as all_members:
            all_members.side_effect = HTTPError(response=mock.Mock(status_code=504))
            with pytest.raises(HTTPError):
                with assert_external_service_log_entry(successful_call=False, extra_modules=['mailchimp'], count=3):
                    list(dm_mailchimp_client.get_email_addresses_from_list('a_list_id'))
            assert all_members.mock_calls == [
                mock.call('a_list_id', count=100, offset=0),
                mock.call('a_list_id', count=100, offset=0),
                mock.call('a_list_id', count=100, offset=0),
            ]

    def test_success_does_not_perform_retry(self):
        dm_mailchimp_client = DMMailChimpClient(
            'username', DUMMY_MAILCHIMP_API_KEY, logging.getLogger('mailchimp'), retries=2
        )
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
            with assert_external_service_log_entry(extra_modules=['mailchimp'], count=2):
                list(dm_mailchimp_client.get_email_addresses_from_list('a_list_id'))
            assert all_members.mock_calls == [
                mock.call('a_list_id', count=100, offset=0),
                mock.call('a_list_id', count=100, offset=100),
            ]

    def test_offset_increments_until_no_members(self):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, logging.getLogger('mailchimp'))
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

            with assert_external_service_log_entry(extra_modules=['mailchimp'], count=8):
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
