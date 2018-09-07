# -*- coding: utf-8 -*-
"""Tests for the Digital Marketplace Notify client."""
import json

import mock
import os
from collections import OrderedDict
from itertools import product

import pytest

from dmutils.email.dm_notify import DMNotifyClient
from helpers import PatchExternalServiceLogConditionMixin, assert_external_service_log_entry


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


_test_api_key = '1111111111' * 8


@pytest.fixture
def dm_notify_client(app):
    """Supply initialized client."""
    with app.app_context():
        return DMNotifyClient(_test_api_key)


@pytest.fixture
def notify_example_http_error():
    """Return a mock object with attributes of Notify `HTTPError`."""
    e = mock.Mock
    e.status_code = 400
    e.message = [
        {u'message': u'email_address Not a valid email address', u'error': u'ValidationError'},
        {u'message': u'template_id is not a valid UUID', u'error': u'ValidationError'},
        # notify do actually use non-ascii characters in their error messages
        {u'message': u'Won\u2019t send unless you give us \u00a3\u00a3\u00a3', u'error': u'ValidationError'},
    ]
    return e


@pytest.fixture
def notify_get_all_notifications():
    """Return a dummy `notifications_python_client.NotificationsAPIClient.get_all_notifications` response."""
    pth = os.path.join(FIXTURES_DIR, 'notifications__get_all_notifications__response.json')
    with open(pth) as get_all_notifications_response:
        return json.loads(get_all_notifications_response.read())


@pytest.fixture
def notify_send_email():
    """Lifted directly from the https://github.com/alphagov/notifications-python-client README.md

    Success response for `notifications_python_client.NotificationsAPIClient.send_email_notification`
    """
    example_response = {
        'id': 'bfb50d92-100d-4b8b-b559-14fa3b091cda',
        'reference': None,
        'content': {
            'subject': 'Licence renewal',
            'body': 'Dear Bill, your licence is due for renewal on 3 January 2016.',
            'from_email': 'the_service@gov.uk'
        },
        'uri': 'https://api.notifications.service.gov.uk/v2/notifications/ceb50d92-100d-4b8b-b559-14fa3b091cd',
        'template': {
            'id': 'ceb50d92-100d-4b8b-b559-14fa3b091cda',
            'version': 1,
            'uri': 'https://api.notifications.service.gov.uk/service/'
            'your_service_id/templates/bfb50d92-100d-4b8b-b559-14fa3b091cda'
        }
    }
    return example_response


class TestDMNotifyClient(PatchExternalServiceLogConditionMixin):
    """Tests for the Digital Marketplace Notify API Client."""

    client_class_str = 'notifications_python_client.NotificationsAPIClient'

    def setup(self):
        """Set up some standard attributes for tests."""
        super().setup()

        self.email_address = 'example@example.com'
        self.template_id = 'my-cool-example-template'
        self.personalisation = OrderedDict([
            (u'foo\u00a3', u'foo_p13n'),
            (u'bar', u'bar_p13n\u00a3'),
            (u'\u00a3baz', u'\u00a3baz_p13n'),
        ])
        self.standard_args = {
            'to_email_address': self.email_address,
            'template_id': self.template_id,
            'personalisation': self.personalisation
        }

    def test_get_reference(self, dm_notify_client):
        """Test the staticmethod that creates the reference field to be sent with the request."""
        ref = dm_notify_client.get_reference(**self.standard_args)
        expected = (
            'jnQ0zrayV0IgiUDcXld9AVU9gM9wUn5ZyAgt2gGjeX8='
        )

        assert ref == expected

    def test_send_email_creates_reference(self, dm_notify_client, notify_send_email):
        """Test the `send_email` function with data that should pass and run without exception."""
        with mock.patch(self.client_class_str + '.' + 'send_email_notification') as email_mock:
            email_mock.return_value = notify_send_email

            dm_notify_client.send_email(self.email_address, self.template_id)

            email_mock.assert_called_with(
                self.email_address,
                self.template_id,
                personalisation=None,
                reference='niC4qhMflcnl8MkY82N7Gqze2ZA7ed1pSBTGnxeDPj0='
            )

    @pytest.mark.parametrize("redirect_app_config,redirect_constructor,expected_redirected_address", tuple(
        (a, b, c) for (a, b), c in zip(
            product(
                (
                    {  # 0
                        "example.com": "bollope@do.om",
                        "s.to.om": "ble@ph.en",
                    },
                    {  # 1
                        "s.to.om": "ble@ph.en",
                    },
                    # 2
                    None,
                ),
                (
                    {  # 0
                        "example.com": "moll@dopel.oob",
                        "ble.ph.en": "s@to.om",
                    },
                    {  # 1
                        "ble.ph.en": "s@to.om",
                    },
                    # 2
                    None,
                ),
            ),
            (
                # None -> "no redirect" - should be same as self.email_address
                "moll@dopel.oob",  # (0, 0,)
                None,              # (0, 1,)
                "bollope@do.om",   # (0, 2,)
                "moll@dopel.oob",  # (1, 0,)
                None,              # (1, 1,)
                None,              # (1, 2,)
                "moll@dopel.oob",  # (2, 0,)
                None,              # (2, 1,)
                None,              # (2, 2,)
            )
        )
    ))
    def test_send_email_replace_address_constructor(
        self,
        app,
        notify_send_email,
        redirect_app_config,
        redirect_constructor,
        expected_redirected_address,
    ):
        with app.app_context():
            app.config["DM_NOTIFY_REDIRECT_DOMAINS_TO_ADDRESS"] = redirect_app_config
            dm_notify_client = DMNotifyClient(_test_api_key, redirect_domains_to_address=redirect_constructor)

            with mock.patch(self.client_class_str + '.' + 'send_email_notification') as email_mock:
                email_mock.return_value = notify_send_email

                dm_notify_client.send_email(self.email_address, self.template_id)

                email_mock.assert_called_with(
                    expected_redirected_address if expected_redirected_address is not None else self.email_address,
                    self.template_id,
                    personalisation=None,
                    # NOTE how reference is unaffected by any of this
                    reference='niC4qhMflcnl8MkY82N7Gqze2ZA7ed1pSBTGnxeDPj0=',
                )

    def test_send_email_with_external_reference(self, dm_notify_client, notify_send_email):
        with mock.patch(self.client_class_str + '.' + 'send_email_notification') as email_mock:
            email_mock.return_value = notify_send_email

            dm_notify_client.send_email(self.email_address, self.template_id, reference='abc')

            email_mock.assert_called_with(
                self.email_address,
                self.template_id,
                personalisation=None,
                reference='abc'
            )

    def test_personalisation_passed(self, dm_notify_client, notify_send_email):
        """Assert the expected existence of personalisation."""
        personalisation = {u'f\u00a3oo': u'bar\u00a3'}
        with mock.patch(self.client_class_str + '.' + 'send_email_notification') as email_mock:
            notify_send_email.update(personalisation=personalisation)

            dm_notify_client.send_email(
                self.email_address,
                self.template_id,
                personalisation=personalisation
            )

            email_mock.assert_called_with(
                self.email_address,
                self.template_id,
                personalisation=personalisation,
                reference='CLkthp1ZgyeBSMCgQj-zf18netwEf3J9aJxLcm-FZ4s='
            )

    def test_personalisation_appears_in_reference(self, dm_notify_client, notify_send_email):
        """Assert personalisation is added to the auto generated reference."""
        personalisation = {u'f\u00a3oo': u'bar\u00a3'}
        with mock.patch(self.client_class_str + '.' + 'send_email_notification') as email_mock:
            notify_send_email.update(personalisation=personalisation)

            dm_notify_client.send_email(
                self.email_address,
                self.template_id,
                personalisation=personalisation
            )

            email_mock.assert_called_with(
                self.email_address,
                self.template_id,
                personalisation=personalisation,
                reference='CLkthp1ZgyeBSMCgQj-zf18netwEf3J9aJxLcm-FZ4s='
            )

    def test_cache_not_instantiated_with_allow_resend(self, dm_notify_client):
        """The cache shouldn't be touched until we pass `allow_resend=False` to `send_email`."""
        with mock.patch(self.client_class_str + '.' + 'send_email_notification'):
            assert dm_notify_client._sent_references_cache is None

            dm_notify_client.send_email(self.email_address, self.template_id)

            assert dm_notify_client._sent_references_cache is None

    def test_cache_instantiated_without_allow_resend(
            self,
            dm_notify_client,
            notify_send_email,
            notify_get_all_notifications
    ):
        """Setting `allow_resend=False` on `send_email` should cause the cache to be populated."""
        with mock.patch(self.client_class_str + '.' + 'send_email_notification') as send_email_notification_mock:
            with mock.patch(self.client_class_str + '.' + 'get_all_notifications') as get_all_notifications_mock:
                send_email_notification_mock.return_value = notify_send_email
                get_all_notifications_mock.return_value = notify_get_all_notifications

                assert dm_notify_client._sent_references_cache is None

                dm_notify_client.send_email(self.email_address, self.template_id, allow_resend=False)

                get_all_notifications_mock.assert_called_once_with(status='delivered')

                # Dummy data from notify_get_all_notifications + the one we just sent = 9
                assert len(dm_notify_client._sent_references_cache) == 9
                assert dm_notify_client.has_been_sent(
                    dm_notify_client.get_reference(self.email_address, self.template_id, None)
                )

    def test_cache_always_populated_after_first_send_without_allow_resend(self, dm_notify_client, notify_send_email):
        """Until `allow_resend` is set to False for the first time the cache shouldn't be populated, after, it should.

        After the first instance of `allow_resend=False` every reference should be added to the cache.
        This is to stop us having to query the api on every email send with `allow_resend=False`.
        """
        with mock.patch(self.client_class_str + '.' + 'send_email_notification') as send_email_notification_mock:
            with mock.patch(self.client_class_str + '.' + 'get_all_notifications') as get_all_notifications_mock:
                send_email_notification_mock.return_value = notify_send_email
                get_all_notifications_mock.return_value = {
                    "links": {
                        "current": "https://api.notifications.service.gov.uk/v2/foo",
                        "next": "https://api.notifications.service.gov.uk/v2/bar",
                    },
                    "notifications": []
                }

                assert dm_notify_client._sent_references_cache is None, "Cache should be None on instantiation"

                dm_notify_client.send_email(self.email_address, self.template_id)
                assert dm_notify_client._sent_references_cache is None, "Cache should be None with allow_resend=True"

                dm_notify_client.send_email(self.email_address, self.template_id, allow_resend=False)
                assert dm_notify_client._sent_references_cache == {
                    dm_notify_client.get_reference(self.email_address, self.template_id)
                }, "Cache should now start populating"

                dm_notify_client.send_email(self.email_address + 'foo', self.template_id + 'bar', allow_resend=False)
                assert dm_notify_client._sent_references_cache == {
                    dm_notify_client.get_reference(self.email_address, self.template_id),
                    dm_notify_client.get_reference(self.email_address + 'foo', self.template_id + 'bar')
                }, "Cache should now start populating regardless of allow_resend flag"

    def test_not_allow_resend(self, dm_notify_client):
        """Trigger identical emails and make sure only one is sent!"""
        with mock.patch(self.client_class_str + '.' + 'send_email_notification') as send_email_notification_mock:
            with mock.patch(self.client_class_str + '.' + 'get_all_notifications') as get_all_notifications_mock:
                send_email_notification_mock.return_value = {'id': 'example-id'}
                get_all_notifications_mock.return_value = {"notifications": []}

                dm_notify_client.send_email(self.email_address, self.template_id, allow_resend=False)
                dm_notify_client.send_email(self.email_address, self.template_id, allow_resend=False)

                send_email_notification_mock.assert_called_once_with(
                    self.email_address,
                    self.template_id,
                    personalisation=None,
                    reference='niC4qhMflcnl8MkY82N7Gqze2ZA7ed1pSBTGnxeDPj0='
                )

    def test_behaviour_outside_flask_app_context(self):
        """If logger is supplied then app context is not required"""
        dm_notify_client = DMNotifyClient(
            _test_api_key,
            logger=mock.Mock(),
        )

        with mock.patch(self.client_class_str + '.' + 'send_email_notification') as send_email_notification_mock:
            dm_notify_client.send_email("email@example.com", "template_id")

            assert send_email_notification_mock.call_args \
                == mock.call(
                    "email@example.com",
                    "template_id",
                    personalisation=None,
                    reference=mock.ANY,
                )

    def test_replacement_address_allows_resend(self, app):
        """
            Test the replacement_email_address mechanism doesn't make calls to different addresses look like resends.
        """
        with app.app_context():
            dm_notify_client = DMNotifyClient(
                _test_api_key,
                redirect_domains_to_address={"example.gov.uk": "ellpod@bomo.ol"},
            )

        with mock.patch(self.client_class_str + '.' + 'send_email_notification') as send_email_notification_mock:
            with mock.patch(self.client_class_str + '.' + 'get_all_notifications') as get_all_notifications_mock:
                send_email_notification_mock.return_value = {'id': 'example-id'}
                get_all_notifications_mock.return_value = {"notifications": []}

                # First call to send_email instantiates the cache with calls to `get_all_notifications`
                # and `get_delivered_notifications`, hence 2 extra log entries.
                dm_notify_client.send_email("fatchuck@example.gov.uk", self.template_id, allow_resend=False)
                dm_notify_client.send_email("cheek.chops@example.gov.uk", self.template_id, allow_resend=False)

                assert send_email_notification_mock.call_args_list == [
                    mock.call(
                        "ellpod@bomo.ol",
                        self.template_id,
                        personalisation=None,
                        reference="oq2Xi6D6ymviEtVK8Gr9I0675Q8KcjfAz3IO9sfX8a0="
                    ),
                    mock.call(
                        "ellpod@bomo.ol",
                        self.template_id,
                        personalisation=None,
                        reference='Q_0wRa57Pj4BEIWGop9gOLoxhkCsVMsE2UOZeOnZyas='
                    ),
                ]

    def test_get_all_notifications_logs_for_external_service_calls(self, dm_notify_client):
        with mock.patch(self.client_class_str + '.' + 'get_all_notifications') as get_all_notifications_mock:
            get_all_notifications_mock.return_value = {"notifications": []}

            with assert_external_service_log_entry(service='Notify', description='get_all_notifications'):
                dm_notify_client.get_all_notifications()

    def test_send_email_writes_logs_for_external_service_calls(self, dm_notify_client):
        with mock.patch(self.client_class_str + '.' + 'send_email_notification') as send_email_notification_mock:
            with mock.patch(self.client_class_str + '.' + 'get_all_notifications') as get_all_notifications_mock:
                send_email_notification_mock.return_value = {'id': 'example-id'}
                get_all_notifications_mock.return_value = {"notifications": []}

                with assert_external_service_log_entry(service='Notify', description='send_email'):
                    dm_notify_client.send_email(self.email_address, self.template_id, allow_resend=True)

                with assert_external_service_log_entry(service='Notify', description='send_email', count=2):
                    dm_notify_client.send_email(self.email_address, self.template_id, allow_resend=True)
                    dm_notify_client.send_email(self.email_address, self.template_id, allow_resend=True)

                with assert_external_service_log_entry(service='Notify', description='send_email', count=1):
                    dm_notify_client.send_email(self.email_address + 'foo', self.template_id, allow_resend=False)
                    dm_notify_client.send_email(self.email_address + 'foo', self.template_id, allow_resend=False)

    def test_constructor_can_retrieve_api_key_from_app_config(self, app):
        api_key = "notify-api-key-" + _test_api_key
        app.config["DM_NOTIFY_API_KEY"] = api_key

        with mock.patch("dmutils.email.dm_notify.DMNotifyClient._client_class") as notify_client_mock:
            with app.app_context():
                DMNotifyClient()

            assert notify_client_mock.call_args \
                == mock.call(
                    api_key,
                    mock.ANY,
                )

    def test_can_use_templates_from_app_config(self, app):
        app.config["NOTIFY_TEMPLATES"] = {"template_name": "template-id"}

        with app.app_context():
            dm_notify_client = DMNotifyClient(_test_api_key)

        with mock.patch(self.client_class_str + '.' + 'send_email_notification') as send_email_notification_mock:
            dm_notify_client.send_email("email@example.com", "template_name")
            assert send_email_notification_mock.call_args \
                == mock.call(
                    "email@example.com",
                    "template-id",
                    personalisation=None,
                    reference=mock.ANY,
                )
