import os
import json

import requests_mock
import requests
import pytest
import mock

from dmutils.apiclient import SearchAPIClient


@pytest.yield_fixture
def rmock():
    with requests_mock.mock() as rmock:
        yield rmock


@pytest.fixture
def search_client():
    return SearchAPIClient('http://baseurl', 'auth-token', True)


@pytest.fixture
def service():
    """A stripped down G6-IaaS service"""
    return {
        "id": "1234567890123456",
        "lot": "IaaS",
        "title": "My Iaas Service",
        "lastUpdated": "2014-12-23T14:46:17Z",
        "lastUpdatedByEmail": "supplier@digital.cabinet-office.gov.uk",
        "lastCompleted": "2014-12-23T14:46:22Z",
        "lastCompletedByEmail": "supplier@digital.cabinet-office.gov.uk",
        "serviceTypes": [
            "Compute",
            "Storage"
        ],
        "serviceName": "My Iaas Service",
        "serviceSummary": "IaaS Service Summary",
        "serviceBenefits": [
            "Free lollipop to every 10th customer",
            "It's just lovely"
        ],
        "serviceFeatures": [
            "[To be completed]",
            "This is my second \"feture\""
        ],
    }


class TestSearchApiClient(object):
    def test_init_app_sets_attributes(self, search_client):
        app = mock.Mock()
        app.config = {
            "DM_SEARCH_API_URL": "http://example",
            "DM_SEARCH_API_AUTH_TOKEN": "example-token",
            "ES_ENABLED": False,
        }
        search_client.init_app(app)

        assert search_client.base_url == "http://example"
        assert search_client.auth_token == "example-token"
        assert not search_client.enabled

    def test_convert_service(self, search_client, service):
        converted = search_client._convert_service(
            service['id'], service, "Supplier Name")

        assert "service" in converted
        assert "service" in converted
        assert converted["service"]["id"] == "1234567890123456"
        assert converted["service"]["lot"] == "IaaS"
        assert converted["service"]["serviceName"] == "My Iaas Service"
        assert \
            converted["service"]["serviceSummary"] == "IaaS Service Summary"
        assert converted["service"]["serviceBenefits"] == [
            "Free lollipop to every 10th customer",
            "It's just lovely"
        ]
        assert converted["service"]["serviceFeatures"] == [
            "[To be completed]",
            "This is my second \"feture\""
        ]
        assert converted["service"]["serviceTypes"] == [
            "Compute",
            "Storage"
        ]
        assert converted["service"]["supplierName"] == "Supplier Name"

    def test_convert_service_with_minimum_fields_for_indexing(
            self, search_client, service):
        del service["serviceTypes"]
        del service["serviceBenefits"]
        del service["serviceFeatures"]

        converted = search_client._convert_service(
            service['id'], service, "Supplier Name")

        assert "service" in converted
        assert converted["service"]["id"] == "1234567890123456"
        assert converted["service"]["lot"] == "IaaS"
        assert converted["service"]["serviceName"] == "My Iaas Service"
        assert \
            converted["service"]["serviceSummary"] == "IaaS Service Summary"
        assert "serviceBenefits" not in converted
        assert "serviceFeatures" not in converted
        assert "serviceTypes" not in converted
        assert converted["service"]["supplierName"] == "Supplier Name"

    def test_post_to_index_with_type_and_service_id(
            self, search_client, rmock, service):
        rmock.put(
            'http://baseurl/g-cloud/services/12345',
            json={'message': 'acknowledged'},
            status_code=200)
        result = search_client.index("12345", service, "Supplier name")
        assert result == {'message': 'acknowledged'}

    def test_should_not_call_search_api_is_es_disabled(
            self, search_client, rmock, service):
        search_client.enabled = False
        rmock.put(
            'http://baseurl/g-cloud/services/12345',
            json={'message': 'acknowledged'},
            status_code=200)
        result = search_client.index("12345", service, "Supplier name")
        assert result is None
        assert not rmock.called

    def test_should_raise_requests_error_on_failure(
            self, search_client, rmock, service):
        with pytest.raises(requests.HTTPError):
            rmock.put(
                'http://baseurl/g-cloud/services/12345',
                json={'error': 'some error'},
                status_code=400)
            search_client.index("12345", service, "Supplier name")

    @staticmethod
    def load_example_listing(name):
        file_path = os.path.join("example_listings", "{}.json".format(name))
        with open(file_path) as f:
            return json.load(f)
