from __future__ import absolute_import
import logging

import six
import requests
from requests import ConnectionError  # noqa
from flask import has_request_context, request, current_app


logger = logging.getLogger(__name__)


class APIError(requests.HTTPError):
    def __init__(self, http_error):
        super(APIError, self).__init__(
            http_error,
            response=http_error.response,
            request=http_error.request)

    @property
    def response_message(self):
        try:
            return self.response.json()['error']
        except (TypeError, KeyError):
            return str(self.response.content)


class BaseAPIClient(object):
    def __init__(self, base_url=None, auth_token=None, enabled=True):
        self.base_url = base_url
        self.auth_token = auth_token
        self.enabled = enabled

    def _put(self, url, data):
        return self._request("PUT", url, data=data)

    def _get(self, url, params=None):
        return self._request("GET", url, params=params)

    def _post(self, url, data):
        return self._request("POST", url, data=data)

    def _request(self, method, url, data=None, params=None):
        if not self.enabled:
            return None
        try:
            logger.debug("API request %s %s", method, url)
            headers = {
                "Content-type": "application/json",
                "Authorization": "Bearer {}".format(self.auth_token),
            }
            headers = self._add_request_id_header(headers)
            response = requests.request(
                method, url,
                headers=headers, json=data, params=params)
            response.raise_for_status()

            return response.json()
        except requests.HTTPError as e:
            e = APIError(e)
            logger.warning(
                "API %s request on %s failed with %s '%s'",
                method, url, e.response.status_code, e.response_message)
            raise e
        except requests.RequestException as e:
            logger.exception(e.message)
            raise

    def _add_request_id_header(self, headers):
        if not has_request_context():
            return headers
        if 'DM_REQUEST_ID_HEADER' not in current_app.config:
            return headers
        header = current_app.config['DM_REQUEST_ID_HEADER']
        headers[header] = request.request_id
        return headers

    def get_status(self):
        try:
            return self._get(
                "{}/_status".format(self.base_url))
        except requests.RequestException as e:
            try:
                return e.response.json()
            except ValueError:
                return {
                    "status": "error",
                    "message": "{}".format(e.message),
                }


class SearchAPIClient(BaseAPIClient):
    FIELDS = [
        "lot",
        "serviceName",
        "serviceSummary",
        "serviceBenefits",
        "serviceFeatures",
        "serviceTypes",
        "supplierName",
        "freeOption",
        "trialOption",
        "minimumContractPeriod",
        "supportForThirdParties",
        "selfServiceProvisioning",
        "datacentresEUCode",
        "dataBackupRecovery",
        "dataExtractionRemoval",
        "networksConnected",
        "apiAccess",
        "openStandardsSupported",
        "openSource",
        "persistentStorage",
        "guaranteedResources",
        "elasticCloud",
    ]

    def init_app(self, app):
        self.base_url = app.config['DM_SEARCH_API_URL']
        self.auth_token = app.config['DM_SEARCH_API_AUTH_TOKEN']
        self.enabled = app.config['ES_ENABLED']

    def _url(self, path):
        return "{}/g-cloud/services{}".format(self.base_url, path)

    def index(self, service_id, service, supplier_name):
        url = self._url("/{}".format(service_id))
        data = self._convert_service(service_id, service, supplier_name)

        return self._put(url, data=data)

    def search_services(self, q="", **filters):
        if isinstance(q, list):
            q = q[0]
        params = {"q": q}

        for filter_name, filter_values in six.iteritems(filters):
            if filter_name == "minimumContractPeriod":
                filter_values = ','.join(filter_values)

            params['filter_{}'.format(filter_name)] = filter_values

        response = self._get(self._url("/search"), params=params)

        return response['search']

    def _convert_service(self, service_id, service, supplier_name):
        data = {k: service[k] for k in self.FIELDS if k in service}
        data['supplierName'] = supplier_name
        data['id'] = service_id

        return {
            "service": data
        }


class DataAPIClient(BaseAPIClient):
    def init_app(self, app):
        self.base_url = app.config['DM_DATA_API_URL']
        self.auth_token = app.config['DM_DATA_API_AUTH_TOKEN']

    def find_suppliers(self, prefix=None):
        params = None
        if prefix:
            params = {
                "prefix": prefix
            }
        return self._get(
            "{}/suppliers".format(self.base_url),
            params
        )

    def get_supplier(self, supplier_id):
        return self._get(
            "{}/suppliers/{}".format(self.base_url, supplier_id)
        )

    def get_service(self, service_id):
        try:
            return self._get(
                "{}/services/{}".format(self.base_url, service_id))
        except APIError as e:
            if e.response.status_code != 404:
                raise
        return None

    def find_services(self, supplier_id=None, page=None):
        params = {}
        if supplier_id is not None:
            params['supplier_id'] = supplier_id
        if page is not None:
            params['page'] = page

        return self._get(
            self.base_url + "/services",
            params=params)

    def update_service(self, service_id, service, user, reason):
        return self._post(
            "{}/services/{}".format(self.base_url, service_id),
            data={
                "update_details": {
                    "updated_by": user,
                    "update_reason": reason,
                },
                "services": service,
            })

    def get_user(self, user_id=None, email_address=None):
        if user_id is not None and email_address is not None:
            raise ValueError(
                "Cannot get user by both user_id and email_address")
        elif user_id is not None:
            url = "{}/users/{}".format(self.base_url, user_id)
            params = {}
        elif email_address is not None:
            url = "{}/users".format(self.base_url)
            params = {"email": email_address}
        else:
            raise ValueError("Either user_id or email_address must be set")

        try:
            return self._get(url, params=params)
        except APIError as e:
            if e.response.status_code != 404:
                raise
        return None

    def authenticate_user(self, email_address, password, supplier=True):
        try:
            response = self._post(
                '{}/users/auth'.format(self.base_url),
                data={
                    "authUsers": {
                        "emailAddress": email_address,
                        "password": password,
                    }
                })
            if not supplier or "supplier" in response['users']:
                return response
        except APIError as e:
            if e.response.status_code not in [400, 403, 404]:
                raise
        return None

    def update_user_password(self, user_id, new_password):
        try:
            self._post(
                '{}/users/{}'.format(self.base_url, user_id),
                data={"users": {"password": new_password}}
            )

            logger.info("Updated password for user %s", user_id)
            return True
        except APIError as e:
            logger.info("Password update failed for user %s: %s",
                        user_id, e.response.status_code)
            return False
