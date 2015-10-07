import six

from .base import BaseAPIClient
from .errors import HTTPError


# TODO remove default value once apps pass the index value to SearchAPIClient method calls
DEFAULT_SEARCH_INDEX = 'g-cloud'


class SearchAPIClient(BaseAPIClient):
    def init_app(self, app):
        self.base_url = app.config['DM_SEARCH_API_URL']
        self.auth_token = app.config['DM_SEARCH_API_AUTH_TOKEN']
        self.enabled = app.config['ES_ENABLED']

    def _url(self, index, path):
        return u"/{}/services/{}".format(index, path)

    def create_index(self, index_name):
        return self._put(
            '/{}'.format(index_name),
            data={'type': 'index'}
        )

    def set_alias(self, alias_name, target_index):
        return self._put(
            '/{}'.format(alias_name),
            data={'type': 'alias', 'target': target_index}
        )

    def index(self, service_id, service, index=DEFAULT_SEARCH_INDEX):
        url = self._url(index, service_id)
        return self._put(url, data={'service': service})

    def delete(self, service_id, index=DEFAULT_SEARCH_INDEX):
        url = self._url(index, service_id)

        try:
            return self._delete(url)
        except HTTPError as e:
            if e.status_code != 404:
                raise
        return None

    def search_services(self, q=None, page=None, index=DEFAULT_SEARCH_INDEX, **filters):
        params = {}
        if q is not None:
            params['q'] = q

        if page:
            params['page'] = page

        for filter_name, filter_values in six.iteritems(filters):
            params[u'filter_{}'.format(filter_name)] = filter_values

        response = self._get(self._url(index, "search"), params=params)
        return response
