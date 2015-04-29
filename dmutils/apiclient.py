from __future__ import absolute_import
import requests
import logging


logger = logging.getLogger(__name__)


class BaseAPIClient(object):
    def __init__(self, base_url=None, auth_token=None, enabled=None):
        self.base_url = base_url
        self.auth_token = auth_token
        self.enabled = enabled

    def _put(self, url, data):
        return self._request("PUT", url, data=data)

    def _get(self, url, params):
        return self._request("GET", url, params=params)

    def _request(self, method, url, data=None, params=None):
        if self.enabled:
            logger.debug("API request %s %s", method, url)
            headers = {
                "Content-type": "application/json",
                "Authorization": "Bearer {}".format(self.auth_token),
            }
            response = requests.request(
                method, url,
                headers=headers, data=data, params=params)
            response.raise_for_status()

            return response.json()


class SearchAPIClient(BaseAPIClient):
    FIELDS = [
        "lot",
        "serviceName",
        "serviceSummary",
        "serviceBenefits",
        "serviceFeatures",
        "serviceTypes",
        "supplierName",
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

        return self._put(url, data)

    def _convert_service(self, service_id, service, supplier_name):
        data = {k: service[k] for k in self.FIELDS if k in service}
        data['supplierName'] = supplier_name
        data['id'] = service_id

        return {
            "service": data
        }
