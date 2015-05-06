# -*- coding: utf-8 -*-
import os
import json

import requests_mock
import pytest
import mock

from dmutils.apiclient import SearchAPIClient, DataAPIClient, APIError


@pytest.yield_fixture
def rmock():
    with requests_mock.mock() as rmock:
        yield rmock


@pytest.fixture
def search_client():
    return SearchAPIClient('http://baseurl', 'auth-token', True)


@pytest.fixture
def data_client():
    return DataAPIClient('http://baseurl', 'auth-token', True)


@pytest.fixture
def service():
    """A stripped down G6-IaaS service"""
    return {
        "id": "1234567890123456",
        "supplierId": 1,
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
        "minimumContractPeriod": "Month",
        "terminationCost": True,
        "priceInterval": "",
        "trialOption": True,
        "priceUnit": "Person",
        "educationPricing": True,
        "vatIncluded": False,
        "priceString": "£10.0067 per person",
        "priceMin": 10.0067,
        "freeOption": False,
        "openStandardsSupported": True,
        "supportForThirdParties": False,
        "supportResponseTime": "3 weeks.",
        "incidentEscalation": True,
        "serviceOffboarding": True,
        "serviceOnboarding": False,
        "analyticsAvailable": False,
        "persistentStorage": True,
        "elasticCloud": True,
        "guaranteedResources": False,
        "selfServiceProvisioning": False,
        "openSource": False,
        "apiType": "SOAP, Rest | JSON",
        "apiAccess": True,
        "networksConnected": [
            "Public Services Network (PSN)",
            "Government Secure intranet (GSi)"
        ],
        "offlineWorking": True,
        "dataExtractionRemoval": False,
        "dataBackupRecovery": True,
        "datacentreTier": "TIA-942 Tier 3",
        "datacentresSpecifyLocation": True,
        "datacentresEUCode": False,
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

    def test_get_status(self, data_client, rmock):
        rmock.get(
            "http://baseurl/_status",
            json={"status": "ok"},
            status_code=200)

        result = data_client.get_status()
        print("result = {}".format(result))

        assert result['status'] == "ok"
        assert rmock.called

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
        assert not converted["service"]["freeOption"]
        assert converted["service"]["trialOption"]
        assert converted["service"]["minimumContractPeriod"] == "Month"
        assert not converted["service"]["supportForThirdParties"]
        assert not converted["service"]["selfServiceProvisioning"]
        assert not converted["service"]["datacentresEUCode"]
        assert converted["service"]["dataBackupRecovery"]
        assert not converted["service"]["dataExtractionRemoval"]
        assert converted["service"]["networksConnected"] == [
            "Public Services Network (PSN)",
            "Government Secure intranet (GSi)"
        ]
        assert converted["service"]["apiAccess"]
        assert converted["service"]["openStandardsSupported"]
        assert not converted["service"]["openSource"]
        assert converted["service"]["persistentStorage"]
        assert not converted["service"]["guaranteedResources"]
        assert converted["service"]["elasticCloud"]

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

    def test_should_raise_error_on_failure(
            self, search_client, rmock, service):
        with pytest.raises(APIError):
            rmock.put(
                'http://baseurl/g-cloud/services/12345',
                json={'error': 'some error'},
                status_code=400)
            search_client.index("12345", service, "Supplier name")

    def test_search_services(self, search_client, rmock):
        rmock.get(
            'http://baseurl/g-cloud/services/search?q=foo&'
            'filter_minimumContractPeriod=a,b&'
            'filter_something=a&filter_something=b',
            json={'search': "myresponse"},
            status_code=200)
        result = search_client.search_services(
            q='foo',
            minimumContractPeriod=['a', 'b'],
            something=['a', 'b'])
        assert result == "myresponse"

    @staticmethod
    def load_example_listing(name):
        file_path = os.path.join("example_listings", "{}.json".format(name))
        with open(file_path) as f:
            return json.load(f)


class TestDataApiClient(object):
    def test_init_app_sets_attributes(self, data_client):
        app = mock.Mock()
        app.config = {
            "DM_DATA_API_URL": "http://example",
            "DM_DATA_API_AUTH_TOKEN": "example-token",
        }
        data_client.init_app(app)

        assert data_client.base_url == "http://example"
        assert data_client.auth_token == "example-token"

    def test_get_status(self, data_client, rmock):
            rmock.get(
                "http://baseurl/_status",
                json={"status": "ok"},
                status_code=200)

            result = data_client.get_status()

            assert result['status'] == "ok"
            assert rmock.called

    def test_get_service(self, data_client, rmock):
        rmock.get(
            "http://baseurl/services/123",
            json={"services": "result"},
            status_code=200)

        result = data_client.get_service(123)

        assert result == "result"
        assert rmock.called

    def test_find_service(self, data_client, rmock):
        rmock.get(
            "http://baseurl/services",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_service()

        assert result == "result"
        assert rmock.called

    def test_find_service_adds_page_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/services?page=2",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_service(page=2)

        assert result == "result"
        assert rmock.called

    def test_find_service_adds_supplier_id_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/services?supplier_id=1",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_service(supplier_id=1)

        assert result == "result"
        assert rmock.called

    def test_update_service(self, data_client, rmock):
        rmock.post(
            "http://baseurl/services/123",
            json={"services": "result"},
            status_code=200,
        )

        result = data_client.update_service(
            123, {"foo": "bar"}, "person", "reason")

        assert result == {"services": "result"}
        assert rmock.called
