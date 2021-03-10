import logging
from typing import Union, cast

import requests
from requests import HTTPError


class DirectPlusError(Exception):
    pass


# See https://directplus.documentation.dnb.com/errorsAndInformationMessages.html
class DUNSNumberNotFound(DirectPlusError):
    status_code = 404


class DUNSNumberInvalid(DirectPlusError):
    status_code = 400


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

    def get_organization_by_duns_number(self, duns_number: Union[str, int]) -> dict:
        """
        Request a organization by D-U-N-S number from the Direct+ API

        :return: the organization details corresponding to the DUNS number
        :raises DUNSNumberNotFound: if there is no organization for the DUNS number
        :raises DUNSNumberInvalid: if `duns_number` is not a valid DUNS number
        :raises DirectPlusError: if there is an unexpected error response from the API
        """

        # request the company profile, linkage, and executives (v2)
        # https://directplus.documentation.dnb.com/openAPI.html?apiID=cmpelkv2
        response = self._direct_plus_request(
            f'data/duns/{duns_number}', payload={'productId': 'cmpelk', 'versionId': 'v2'}
        )

        try:
            response.raise_for_status()
        except HTTPError as exception:
            try:
                error = response.json()["error"]
            except (ValueError, KeyError) as e:
                error_message = f"Unable to parse Direct+ API response: {response}: {e}"
                raise DirectPlusError(error_message, exception)

            error_message = (
                f"Unable to get supplier for DUNS number '{duns_number}' (HTTP error {response.status_code}): {error}"
            )

            if response.status_code in [DUNSNumberInvalid.status_code, DUNSNumberNotFound.status_code]:
                self.logger.warning(error_message)

                if response.status_code == DUNSNumberInvalid.status_code:
                    raise DUNSNumberInvalid(error_message, exception)
                if response.status_code == DUNSNumberNotFound.status_code:
                    raise DUNSNumberNotFound(error_message, exception)

            else:
                self.logger.error(error_message)
                raise DirectPlusError(error_message, exception)

        try:
            organization = cast(dict, response.json()['organization'])
        except (ValueError, KeyError) as e:
            # this should never happen, so let's propogate it so it is noisy
            self.logger.error(
                f"Unable to parse Direct+ API response: {response}: {e}"
            )
            raise

        return organization
