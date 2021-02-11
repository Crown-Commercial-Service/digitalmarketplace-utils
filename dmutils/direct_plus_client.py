import logging
from typing import Optional, cast

import requests
from requests import HTTPError

# See https://directplus.documentation.dnb.com/errorsAndInformationMessages.html
DUNS_NUMBER_NOT_FOUND = 404, "10001"
DUNS_NUMBER_INVALID = 400, "10003"


class DirectPlusClient(object):
    """Client to interface with Dun and Bradstreet's Direct Plus API."""

    access_token = None
    protocol = 'https'
    domain = 'plus.dnb.com'
    required_headers = (
        ('Content-Type', 'application/json'),
        ('Accept', 'application/json'),
    )

    def __init__(self, username, password, logger=None):
        self.username = username
        self.password = password
        self.logger = logger if logger else logging.getLogger(__name__)

    def _reset_access_token(self):
        """
        Set the access token and header authorisation parameter for requests to use.
        """
        basic_auth_string = requests.auth._basic_auth_str(self.username, self.password)
        response = self._direct_plus_request(
            'token',
            method='post',
            version='v2',
            payload={'grant_type': 'client_credentials'},
            extra_headers=(('Authorization', basic_auth_string),),
            allow_access_token_reset=False
        )
        self.access_token = response.json().get('access_token')
        self.required_headers += (('Authorization', f'Bearer {self.access_token}'),)

    def _direct_plus_request(
        self,
        endpoint,
        method='get',
        version='v1',
        payload=None,
        extra_headers=(),
        allow_access_token_reset=True
    ):
        """
        Make a request to the Direct Plus API
        """
        if self.access_token is None and allow_access_token_reset is True:
            self._reset_access_token()

        url = f'{self.protocol}://{self.domain}/{version}/{endpoint}'
        headers = {**dict(self.required_headers), **dict(extra_headers)}

        if method != 'get':
            response = getattr(requests, method)(url, headers=headers, json=payload)
        else:
            response = requests.get(url, headers=headers, params=payload)

        if response.status_code == 401 and allow_access_token_reset is True:
            # If access token invalid (401) refresh access token manually
            # and retry request with allow_access_token_reset = False
            self._reset_access_token()
            response = self._direct_plus_request(
                endpoint,
                method=method,
                version=version,
                payload=payload,
                extra_headers=extra_headers,
                allow_access_token_reset=False
            )
        return response

    def get_organization_by_duns_number(self, duns_number) -> Optional[dict]:
        """
        Request a supplier by duns number from the Direct Plus API

        :return the organisation corresponding to the DUNS number; or `None` if the number is invalid or no
                corresponding organisation exists.
        :raises KeyError on unexpected failure if the response body is JSON.
        :raises ValueError on unexpected failure if the response body is not valid JSON.
        """
        response = self._direct_plus_request(
            f'data/duns/{duns_number}', payload={'productId': 'cmpelk', 'versionId': 'v2'}
        )

        try:
            response.raise_for_status()
        except HTTPError as exception:
            try:
                error = response.json()['error']

                if (response.status_code, error["errorCode"]) in [DUNS_NUMBER_INVALID, DUNS_NUMBER_NOT_FOUND]:
                    return None

                self.logger.error(f"Unable to get supplier by DUNS number: {error}")
            except (ValueError, KeyError):
                self.logger.error(f"Unable to get supplier by DUNS number: {exception}")
        return cast(dict, response.json()['organization'])
