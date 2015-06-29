import six

from .base import BaseAPIClient
from .errors import HTTPError


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

    def search_services(self, q=None, page=None, **filters):
        params = {}
        if q is not None:
            params['q'] = q

        if page:
            params['page'] = page

        for filter_name, filter_values in six.iteritems(filters):
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
