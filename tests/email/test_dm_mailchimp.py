# -*- coding: utf-8 -*-
"""Tests for the Digital Marketplace MailChimp integration."""
import logging
import mock
import pytest
import types

from json.decoder import JSONDecodeError
from requests import RequestException
from requests.exceptions import HTTPError, ConnectTimeout

from dmutils.email.dm_mailchimp import DMMailChimpClient, get_response_from_exception
from mailchimp3.mailchimpclient import MailChimpError

from helpers import assert_external_service_log_entry, PatchExternalServiceLogConditionMixin


# Mailchimp client checks the first part of the key against a regex: ^[0-9a-f]{32}$
DUMMY_MAILCHIMP_API_KEY = "1234567890abcdef1234567890abcdef-us5"


class TestGetResponseFromException:

    def test_request_exception(self):
        exception = RequestException('error message')
        with mock.patch.object(exception, 'response', autospec=True) as response:
            response.json.return_value = {'detail': 'error'}
            result = get_response_from_exception(exception)

            assert exception.response.json.called
            assert result == {'detail': 'error'}

    @pytest.mark.parametrize('error', (AttributeError(), ValueError(), JSONDecodeError('message', '', 0)))
    def test_exception_on_json_decode(self, error):
        exception = RequestException('error message')
        with mock.patch.object(exception, 'response', autospec=True) as response:
            response.json.side_effect = error
            result = get_response_from_exception(exception)

            assert exception.response.json.called
            assert result == {}

    def test_mail_chimp_error(self):
        exception = MailChimpError({'detail': 'error'})

        assert get_response_from_exception(exception) == {'detail': 'error'}

    def test_unrelated_exception(self):
        exception = IndexError('error message')

        assert get_response_from_exception(exception) == {}


class TestMailchimp(PatchExternalServiceLogConditionMixin):
    def test_create_campaign(self):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, 'logger')
        with mock.patch.object(dm_mailchimp_client._client.campaigns, 'create', autospec=True) as create:
            create.return_value = {"id": "100"}

            with assert_external_service_log_entry():
                res = dm_mailchimp_client.create_campaign({"example": "data"})

            assert res == "100"
            create.assert_called_once_with({"example": "data"})

    @pytest.mark.parametrize(
        ('exception', 'expected_error'),
        [
            (RequestException("error message"), {"error": "error message"}),
            (MailChimpError({"request": "failed", "status": 500}), {'error': '{"request": "failed", "status": 500}'})
        ]
    )
    def test_log_error_message_if_error_creating_campaign(self, exception, expected_error):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, mock.MagicMock())
        with mock.patch.object(dm_mailchimp_client._client.campaigns, 'create', autospec=True) as create:
            create.side_effect = exception
            with mock.patch.object(dm_mailchimp_client.logger, 'error', autospec=True) as error:
                with assert_external_service_log_entry(successful_call=False):
                    res = dm_mailchimp_client.create_campaign({"example": "data", 'settings': {'title': 'Foo'}})

                assert res is False
                error.assert_called_once_with(
                    "Mailchimp failed to create campaign for 'campaign title'", extra=expected_error
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

    @pytest.mark.parametrize(
        ('exception', 'expected_error'),
        [
            (RequestException("error message"), "error message"),
            (MailChimpError({'request': 'failed', 'status': 500}), "{'request': 'failed', 'status': 500}")
        ]
    )
    def test_log_error_message_if_error_setting_campaign_content(self, exception, expected_error):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, logging.getLogger('mailchimp'))
        with mock.patch.object(dm_mailchimp_client._client.campaigns.content, 'update', autospec=True) as update:
            update.side_effect = exception

            with assert_external_service_log_entry(successful_call=False, extra_modules=['mailchimp']) as log_catcher:
                res = dm_mailchimp_client.set_campaign_content('1', {"html": "some html"})

            assert res is False

            assert log_catcher.records[1].msg == "Mailchimp failed to set content for campaign id '1'"
            assert log_catcher.records[1].error == expected_error

    def test_send_campaign(self):
        campaign_id = "1"
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, mock.MagicMock())
        with mock.patch.object(dm_mailchimp_client._client.campaigns.actions, 'send', autospec=True) as send:
            with assert_external_service_log_entry():
                res = dm_mailchimp_client.send_campaign(campaign_id)

            assert res is True
            send.assert_called_once_with(campaign_id)

    @pytest.mark.parametrize(
        ('exception', 'expected_error'),
        [
            (RequestException("error sending"), "error sending"),
            (MailChimpError({'request': 'failed', 'status': 500}), "{'request': 'failed', 'status': 500}")
        ]
    )
    def test_log_error_message_if_error_sending_campaign(self, exception, expected_error):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, logging.getLogger('mailchimp'))
        with mock.patch.object(dm_mailchimp_client._client.campaigns.actions, 'send', autospec=True) as send:
            send.side_effect = exception

            with assert_external_service_log_entry(successful_call=False, extra_modules=['mailchimp']) as log_catcher:
                res = dm_mailchimp_client.send_campaign("1")

            assert res is False

            assert log_catcher.records[1].msg == "Mailchimp failed to send campaign id '1'"
            assert log_catcher.records[1].levelname == 'ERROR'
            assert log_catcher.records[1].error == expected_error

    @mock.patch("dmutils.email.dm_mailchimp.DMMailChimpClient.get_email_hash", return_value="foo")
    def test_subscribe_new_email_to_list(self, get_email_hash):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, mock.MagicMock())
        with mock.patch.object(
                dm_mailchimp_client._client.lists.members, 'create_or_update', autospec=True) as create_or_update:

            create_or_update.return_value = {"response": "data"}
            with assert_external_service_log_entry():
                res = dm_mailchimp_client.subscribe_new_email_to_list('list_id', 'example@example.com')

            assert res == {"status": "success", 'error_type': None, 'status_code': 200, "response": "data"}
            create_or_update.assert_called_once_with(
                'list_id',
                "foo",
                {
                    "email_address": "example@example.com",
                    "status_if_new": "subscribed"
                }
            )

    @mock.patch("dmutils.email.dm_mailchimp.DMMailChimpClient.get_email_hash", return_value="foo")
    def test_log_request_exception_error_message_if_error_subscribing_email_to_list(self, get_email_hash):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, logging.getLogger('mailchimp'))
        with mock.patch.object(
                dm_mailchimp_client._client.lists.members, 'create_or_update', autospec=True) as create_or_update:
            # The 400 response from MailChimp is actually falsey
            response = mock.MagicMock(__bool__=False)
            response.json.return_value = {"detail": "Unexpected error."}
            create_or_update.side_effect = RequestException("error sending", response=response)

            with assert_external_service_log_entry(successful_call=False, extra_modules=['mailchimp']) as log_catcher:
                res = dm_mailchimp_client.subscribe_new_email_to_list('list_id', 'example@example.com')

            assert res == {"status": "error", "error_type": "unexpected_error", "status_code": 500}

            assert log_catcher.records[1].msg == "Mailchimp failed to add user (foo) to list (list_id)"
            assert log_catcher.records[1].error == "error sending"
            assert log_catcher.records[1].levelname == 'ERROR'

    @mock.patch("dmutils.email.dm_mailchimp.DMMailChimpClient.get_email_hash", return_value="foo")
    def test_log_mailchimp_error_unexpected_error_payload_if_error_subscribing_email_to_list(self, get_email_hash):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, logging.getLogger('mailchimp'))
        with mock.patch.object(
                dm_mailchimp_client._client.lists.members, 'create_or_update', autospec=True) as create_or_update:
            create_or_update.side_effect = MailChimpError({'request': 'failed', 'status': 500})

            with assert_external_service_log_entry(successful_call=False, extra_modules=['mailchimp']) as log_catcher:
                res = dm_mailchimp_client.subscribe_new_email_to_list('list_id', 'example@example.com')

            assert res == {"status": "error", "error_type": "unexpected_error", "status_code": 500}

            assert log_catcher.records[1].msg == "Mailchimp failed to add user (foo) to list (list_id)"
            assert log_catcher.records[1].error == "{'request': 'failed', 'status': 500}"
            assert log_catcher.records[1].levelname == 'ERROR'

    @mock.patch("dmutils.email.dm_mailchimp.DMMailChimpClient.get_email_hash", return_value="foo")
    def test_create_or_update_returns_error_payload_for_expected_request_exception(self, get_email_hash):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, logging.getLogger('mailchimp'))
        with mock.patch.object(
                dm_mailchimp_client._client.lists.members, 'create_or_update', autospec=True) as create_or_update:
            response = mock.MagicMock(__bool__=False)
            response.json.return_value = {"detail": "foo looks fake or invalid, please enter a real email address."}
            create_or_update.side_effect = RequestException("error sending", response=response)

            with assert_external_service_log_entry(successful_call=False, extra_modules=['mailchimp']) as log_catcher:
                res = dm_mailchimp_client.subscribe_new_email_to_list('list_id', 'example@example.com')

            assert res == {"status": "error", "error_type": "invalid_email", "status_code": 400}
            assert log_catcher.records[1].msg == (
                "Expected error: Mailchimp failed to add user (foo) to list (list_id). "
                "API error: The email address looks fake or invalid, please enter a real email address."
            )
            assert log_catcher.records[1].error == "error sending"
            assert log_catcher.records[1].levelname == 'ERROR'

    @mock.patch("dmutils.email.dm_mailchimp.DMMailChimpClient.get_email_hash", return_value="foo")
    def test_create_or_update_returns_error_payload_for_expected_mailchimp_error(self, get_email_hash):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, logging.getLogger('mailchimp'))
        with mock.patch.object(
                dm_mailchimp_client._client.lists.members, 'create_or_update', autospec=True) as create_or_update:
            create_or_update.side_effect = MailChimpError(
                {
                    "detail": "foo looks fake or invalid, please enter a real email address.",
                    'request': 'failed',
                    'status': 500
                }
            )

            with assert_external_service_log_entry(successful_call=False, extra_modules=['mailchimp']) as log_catcher:
                res = dm_mailchimp_client.subscribe_new_email_to_list('list_id', 'example@example.com')

            assert res == {"status": "error", "error_type": "invalid_email", "status_code": 400}
            assert log_catcher.records[1].msg == (
                "Expected error: Mailchimp failed to add user (foo) to list (list_id). "
                "API error: The email address looks fake or invalid, please enter a real email address."
            )
            assert log_catcher.records[1].error == (
                "{'detail': 'foo looks fake or invalid, please enter a real email address.', "
                "'request': 'failed', 'status': 500}"
            )
            assert log_catcher.records[1].levelname == 'ERROR'

    @mock.patch("dmutils.email.dm_mailchimp.DMMailChimpClient.get_email_hash", return_value="foo")
    def test_returns_error_payload_if_expected_already_subscribed_email_error(self, get_email_hash):
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

            assert res == {"status": "error", "error_type": "already_subscribed", "status_code": 400}
            assert log_catcher.records[1].msg == (
                "Expected error: Mailchimp failed to add user (foo) to list (list_id). "
                "API error: This email address is already subscribed."
            )
            assert log_catcher.records[1].error == "400 Client Error"
            assert log_catcher.records[1].levelname == 'WARNING'

    @mock.patch("dmutils.email.dm_mailchimp.DMMailChimpClient.get_email_hash", return_value="foo")
    def test_returns_error_payload_if_user_previously_unsubscribed_error(self, get_email_hash):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, logging.getLogger('mailchimp'))

        with mock.patch.object(
            dm_mailchimp_client._client.lists.members, 'create_or_update', autospec=True
        ) as create_or_update:

            response = mock.MagicMock(__bool__=False)
            expected_error = "user@example.com was permanently deleted and cannot be re-imported. " \
                             "The contact must re-subscribe to get back on the list."

            response.status_code = 400
            response.message = (
                "Bad Request for url: https://us5.api.mailchimp.com/3.0/lists/list_id/members/member_id"
            )
            response.json.return_value = {"detail": expected_error}
            create_or_update.side_effect = HTTPError("400 Client Error", response=response)

            with assert_external_service_log_entry(successful_call=False, extra_modules=['mailchimp']) as log_catcher:
                res = dm_mailchimp_client.subscribe_new_email_to_list('list_id', 'example@example.com')

            assert res == {"status": "error", "error_type": "deleted_user", "status_code": 400}
            assert log_catcher.records[1].msg == (
                "Expected error: Mailchimp cannot automatically subscribe user (foo) to list (list_id) as the user "
                "has been permanently deleted."
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

            assert res == {'error_type': 'unexpected_error', 'status': 'error', 'status_code': 500}
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

    @mock.patch('dmutils.email.dm_mailchimp.MailChimp', autospec=True)
    def test_timeout_default_is_passed_to_client(self, mailchimp_client):
        DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, logging.getLogger('mailchimp'))
        args, kwargs = mailchimp_client.call_args

        assert kwargs['timeout'] == 25

    def test_timeout_exception_is_not_propagated_for_create_or_update(self):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, logging.getLogger('mailchimp'))
        with mock.patch.object(
                dm_mailchimp_client._client.lists.members, 'create_or_update', autospec=True) as create_or_update:
            create_or_update.side_effect = ConnectTimeout()

            assert dm_mailchimp_client.subscribe_new_email_to_list('a_list_id', 'example@example.com') == \
                {"status": "error", "error_type": "unexpected_error", "status_code": 500}
            assert create_or_update.called is True

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

    def test_get_lists_for_email(self):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, logging.getLogger('mailchimp'))
        with mock.patch.object(dm_mailchimp_client._client.lists, 'all', autospec=True) as all_lists:
            all_lists.return_value = {
                "lists": [
                    {"id": "gadz00ks", "name": "Pistachios", "irrelevant": "custard"},
                    {"id": "1886", "name": "Square the circle", "meaningless": 3.1415},
                ],
                "pigeon": "pasty",
            }

            with assert_external_service_log_entry(extra_modules=['mailchimp'], count=1):
                result = dm_mailchimp_client.get_lists_for_email("trousers.potato@purse.net")

            assert tuple(result) == (
                {"list_id": "gadz00ks", "name": "Pistachios"},
                {"list_id": "1886", "name": "Square the circle"},
            )

            assert all_lists.call_args_list == [
                mock.call(get_all=True, email="trousers.potato@purse.net"),
            ]

    def test_permanently_remove_email_from_list_success(self):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, logging.getLogger('mailchimp'))
        with mock.patch.object(
            dm_mailchimp_client._client.lists.members,
            'delete_permanent',
            autospec=True,
        ) as del_perm:
            del_perm.return_value = {"don't rely": "on me"}

            with assert_external_service_log_entry(extra_modules=['mailchimp'], count=1):
                result = dm_mailchimp_client.permanently_remove_email_from_list(
                    "trousers.potato@purse.net",
                    "modern_society",
                )

            assert result is True

            assert del_perm.call_args_list == [
                mock.call(
                    list_id="modern_society",
                    subscriber_hash="ee5ae5f54bdf3394d48ea4e79e6d0e39",
                ),
            ]

    @pytest.mark.parametrize("exception", (RequestException("No thoroughfare"), MailChimpError({"status": 500})))
    def test_permanently_remove_email_from_list_failure(self, exception):
        dm_mailchimp_client = DMMailChimpClient('username', DUMMY_MAILCHIMP_API_KEY, logging.getLogger('mailchimp'))
        with mock.patch.object(
            dm_mailchimp_client._client.lists.members,
            'delete_permanent',
            autospec=True,
        ) as del_perm:
            del_perm.side_effect = exception

            with assert_external_service_log_entry(successful_call=False, extra_modules=['mailchimp'], count=1):
                result = dm_mailchimp_client.permanently_remove_email_from_list(
                    "Trousers.Potato@purse.net",
                    "p_kellys_budget",
                )

            assert result is False

            assert del_perm.call_args_list == [
                mock.call(
                    list_id="p_kellys_budget",
                    subscriber_hash="ee5ae5f54bdf3394d48ea4e79e6d0e39",
                ),
            ]
