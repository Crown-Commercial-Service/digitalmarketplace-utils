from __future__ import absolute_import
import logging

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

import six
import requests
from flask import has_request_context, request, current_app


logger = logging.getLogger(__name__)


REQUEST_ERROR_STATUS_CODE = 503
REQUEST_ERROR_MESSAGE = "Request failed"


class APIError(Exception):
    def __init__(self, response=None, message=None):
        self.response = response
        self._message = message

    @property
    def message(self):
        try:
            return self.response.json()['error']
        except (TypeError, ValueError, AttributeError, KeyError):
            return self._message or REQUEST_ERROR_MESSAGE

    @property
    def status_code(self):
        try:
            return self.response.status_code
        except AttributeError:
            return REQUEST_ERROR_STATUS_CODE


class HTTPError(APIError):
    pass


class InvalidResponse(APIError):
    pass


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

    def _delete(self, url):
        return self._request("DELETE", url)

    def _request(self, method, url, data=None, params=None):
        if not self.enabled:
            return None

        url = urlparse.urljoin(self.base_url, url)

        logger.debug("API request %s %s", method, url)
        headers = {
            "Content-type": "application/json",
            "Authorization": "Bearer {}".format(self.auth_token),
        }
        headers = self._add_request_id_header(headers)

        try:
            response = requests.request(
                method, url,
                headers=headers, json=data, params=params)
            response.raise_for_status()
        except requests.RequestException as e:
            api_error = HTTPError(e.response)
            logger.warning(
                "API %s request on %s failed with %s '%s'",
                method, url, api_error.status_code, api_error.message)
            raise api_error
        try:
            return response.json()
        except ValueError as e:
            raise InvalidResponse(response,
                                  message="No JSON object could be decoded")

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
            return self._get("{}/_status".format(self.base_url))
        except APIError as e:
            try:
                return e.response.json()
            except (ValueError, AttributeError):
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
        return "/g-cloud/services{}".format(path)

    def index(self, service_id, service, supplier_name, framework_name):
        url = self._url("/{}".format(service_id))
        data = self._convert_service(
            service_id,
            service,
            supplier_name,
            framework_name)

        return self._put(url, data=data)

    def delete(self, service_id):
        url = self._url("/{}".format(service_id))

        try:
            return self._delete(url)
        except HTTPError as e:
            if e.status_code != 404:
                raise
        return None

    def search_services(self, q="", page=None, **filters):
        if isinstance(q, list):
            q = q[0]
        params = dict()
        if q != "":
            params['q'] = q

        if page:
            params['page'] = page

        for filter_name, filter_values in six.iteritems(filters):
            if filter_name == "minimumContractPeriod":
                filter_values = ','.join(filter_values)

            params['filter_{}'.format(filter_name)] = filter_values

        response = self._get(self._url("/search"), params=params)
        return response

    def _convert_service(
            self,
            service_id,
            service,
            supplier_name,
            framework_name):
        data = {k: service[k] for k in self.FIELDS if k in service}
        data['frameworkName'] = framework_name
        data['supplierName'] = supplier_name
        data['id'] = service_id

        return {
            "service": data
        }


class DataAPIClient(BaseAPIClient):
    def init_app(self, app):
        self.base_url = app.config['DM_DATA_API_URL']
        self.auth_token = app.config['DM_DATA_API_AUTH_TOKEN']

    def find_suppliers(self, prefix=None, page=None):
        params = {}
        if prefix:
            params["prefix"] = prefix
        if page is not None:
            params['page'] = page

        return self._get(
            "/suppliers",
            params=params
        )

    def get_supplier(self, supplier_id):
        return self._get(
            "/suppliers/{}".format(supplier_id)
        )

    def create_supplier(self, supplier_id, supplier):
        return self._put(
            "/suppliers/{}".format(supplier_id),
            data={"suppliers": supplier},
        )

    def get_service(self, service_id):
        try:
            return self._get(
                "/services/{}".format(service_id))
        except HTTPError as e:
            if e.status_code != 404:
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

    def create_service(self, service_id, service, user, reason):
        return self._put(
            "/services/{}".format(service_id),
            data={
                "update_details": {
                    "updated_by": user,
                    "update_reason": reason,
                },
                "services": service,
            })

    def update_service(self, service_id, service, user, reason):
        return self._post(
            "/services/{}".format(service_id),
            data={
                "update_details": {
                    "updated_by": user,
                    "update_reason": reason,
                },
                "services": service,
            })

    def update_service_status(self, service_id, status, user, reason):
        return self._post(
            "/services/{}/status/{}".format(service_id, status),
            data={
                "update_details": {
                    "updated_by": user,
                    "update_reason": reason,
                },
            })

    def create_user(self, user):
        return self._post(
            "/users",
            data={
                "users": user,
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
        except HTTPError as e:
            if e.status_code != 404:
                raise
        return None

    def authenticate_user(self, email_address, password, supplier=True):
        try:
            response = self._post(
                '/users/auth',
                data={
                    "authUsers": {
                        "emailAddress": email_address,
                        "password": password,
                    }
                })
            if not supplier or "supplier" in response['users']:
                return response
        except HTTPError as e:
            if e.status_code not in [400, 403, 404]:
                raise
        return None

    def update_user_password(self, user_id, new_password):
        try:
            self._post(
                '/users/{}'.format(user_id),
                data={"users": {"password": new_password}}
            )

            logger.info("Updated password for user %s", user_id)
            return True
        except HTTPError as e:
            logger.info("Password update failed for user %s: %s",
                        user_id, e.status_code)
            return False
