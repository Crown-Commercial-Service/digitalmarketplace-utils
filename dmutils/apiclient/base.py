from __future__ import absolute_import
import logging

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse

import requests
from flask import has_request_context, request, current_app

from .errors import APIError, HTTPError, InvalidResponse


logger = logging.getLogger(__name__)


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
