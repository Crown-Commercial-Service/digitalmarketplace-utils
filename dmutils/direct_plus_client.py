import logging
import requests


class DirectPlusClient(object):

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
        response = self._dnb_request(
            'token',
            method='post',
            version='v2',
            payload={'grant_type': 'client_credentials'},
            extra_headers=(('Authorization', basic_auth_string),),
            allow_access_token_reset=False
        )
        self.access_token = response.json().get('access_token')
        self.required_headers += (('Authorization', f'Bearer {self.access_token}'),)

    def _dnb_request(
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
            response = self._dnb_request(
                endpoint,
                method=method,
                version=version,
                payload=payload,
                extra_headers=extra_headers,
                allow_access_token_reset=False
            )
        return response

    def get_organization_by_duns_number(self, duns_number):
        """
        Request a supplier by duns number from the Direct Plus API
        """
        response = self._dnb_request(
            f'data/duns/{duns_number}', payload={'productId': 'cmpelk', 'versionId': 'v2'}
        )

        if response.status_code in (404, 400):
            # 404 - DUNs number not found
            # 400 - Incorrect format
            return None
        return response.json()['organization']
