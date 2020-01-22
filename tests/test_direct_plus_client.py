import mock
import pytest
import requests_mock

from dmutils.direct_plus_client import DirectPlusClient


@pytest.fixture
def direct_plus_client():
    yield DirectPlusClient('username', 'password')


@pytest.fixture
def r_mock_with_token_request():
    with requests_mock.mock() as r_mock:
        r_mock.post(
            'https://plus.dnb.com/v2/token',
            json={'access_token': 'test_access_token', 'expiresIn': 86400},
            status_code=200
        )
        yield r_mock


class TestGetOrganizationByDunsNumber:

    expected_headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Bearer test_access_token'
    }

    @pytest.mark.parametrize('duns_number', ('123456', 'qwerty', 'test1'))
    @mock.patch('dmutils.direct_plus_client.DirectPlusClient._dnb_request', autospec=True)
    def test_calls_dnb_request(self, _dnb_request, duns_number, direct_plus_client):
        direct_plus_client.get_organization_by_duns_number(duns_number)
        _dnb_request.assert_called_once_with(
            direct_plus_client,
            f'data/duns/{duns_number}',
            payload={'productId': 'cmpelk', 'versionId': 'v2'}
        )

    @pytest.mark.parametrize('duns_number', ('123456', 'qwerty', 'test1'))
    def test_requests_call(self, duns_number, direct_plus_client, r_mock_with_token_request):
        r_mock_with_token_request.get = mock.MagicMock()

        with mock.patch('dmutils.direct_plus_client.requests.get', autospec=True) as get:
            direct_plus_client.get_organization_by_duns_number(duns_number)

        get.assert_called_once_with(
            f'https://plus.dnb.com/v1/data/duns/{duns_number}',
            headers=self.expected_headers,
            params={'productId': 'cmpelk', 'versionId': 'v2'}
        )

    def test_404_returns_none(self, direct_plus_client, r_mock_with_token_request):
        r_mock_with_token_request.get(
            'https://plus.dnb.com/v1/data/duns/123456789',
            json={'error': {"errorMessage": 'DUNS not found', "errorCode": '10001'}},
            status_code=404
        )
        assert direct_plus_client.get_organization_by_duns_number(123456789) is None

    def test_400_returns_none(self, direct_plus_client, r_mock_with_token_request):
        r_mock_with_token_request.get(
            'https://plus.dnb.com/v1/data/duns/123456789',
            json={'error': {"errorMessage": 'Supplied DUNS number format is invalid', "errorCode": '10003'}},
            status_code=400
        )
        assert direct_plus_client.get_organization_by_duns_number(123456789) is None

    def test_500_raises(self, direct_plus_client, r_mock_with_token_request):
        r_mock_with_token_request.get(
            'https://plus.dnb.com/v1/data/duns/123456789',
            json={'error': {"errorMessage": 'Server Error'}},
            status_code=500
        )
        with pytest.raises(KeyError):
            direct_plus_client.get_organization_by_duns_number(123456789)


class TestResetAccessToken:

    @mock.patch('dmutils.direct_plus_client.requests.auth._basic_auth_str', autospec=True)
    @mock.patch('dmutils.direct_plus_client.DirectPlusClient._dnb_request', autospec=True)
    def test_encodes_username_and_password(
        self,
        _dnb_request_mock,
        auth_mock,
        direct_plus_client,
        r_mock_with_token_request
    ):
        direct_plus_client._reset_access_token()
        auth_mock.assert_called_once_with('username', 'password')

    @mock.patch('dmutils.direct_plus_client.DirectPlusClient._dnb_request', autospec=True)
    def test_makes_dnb_request(self, _dnb_request_mock, direct_plus_client):
        direct_plus_client._reset_access_token()
        _dnb_request_mock.assert_called_once_with(
            direct_plus_client,
            'token',
            allow_access_token_reset=False,
            extra_headers=(('Authorization', 'Basic dXNlcm5hbWU6cGFzc3dvcmQ='),),
            method='post',
            payload={'grant_type': 'client_credentials'},
            version='v2'
        )

    def test_sets_access_token_on_class(self, direct_plus_client, r_mock_with_token_request):
        assert direct_plus_client.access_token is None
        direct_plus_client._reset_access_token()
        assert direct_plus_client.access_token == 'test_access_token'

    def test_sets_access_token_header(self, direct_plus_client, r_mock_with_token_request):
        assert direct_plus_client.required_headers == (
            ('Content-Type', 'application/json'),
            ('Accept', 'application/json'),
        )
        direct_plus_client._reset_access_token()
        assert direct_plus_client.required_headers == (
            ('Content-Type', 'application/json'),
            ('Accept', 'application/json'),
            ('Authorization', 'Bearer test_access_token')
        )


class TestDnbRequest:

    @mock.patch('dmutils.direct_plus_client.DirectPlusClient._reset_access_token', autospec=True)
    @mock.patch('dmutils.direct_plus_client.requests', autospec=True)
    def test_attempts_token_reset_if_no_token(self, requests_mock, reset_access_token_mock, direct_plus_client):
        direct_plus_client._dnb_request('dnb/endpoint')
        reset_access_token_mock.assert_called_once()

    @mock.patch('dmutils.direct_plus_client.DirectPlusClient._reset_access_token', autospec=True)
    @mock.patch('dmutils.direct_plus_client.requests', autospec=True)
    def test_does_not_attempt_token_reset_when_disallowed(
            self,
            requests_mock,
            reset_access_token_mock,
            direct_plus_client
    ):
        direct_plus_client._dnb_request('dnb/endpoint', allow_access_token_reset=False)
        reset_access_token_mock.assert_not_called()

    @pytest.mark.parametrize(
        ('protocol', 'domain', 'version', 'endpoint', 'expected_result'),
        (
            ('https', 'plus.dnb.com', 'v2', 'token', 'https://plus.dnb.com/v2/token'),
            ('http', 'plusone.dnb.com', 'v1', 'some/endpoint', 'http://plusone.dnb.com/v1/some/endpoint'),
            ('ftp', 'test.com', 'v100', 'test/token/test', 'ftp://test.com/v100/test/token/test'),
            ('test', 'test', 'test', 'test', 'test://test/test/test'),
        )
    )
    @mock.patch('dmutils.direct_plus_client.DirectPlusClient._reset_access_token', autospec=True)
    @mock.patch('dmutils.direct_plus_client.requests', autospec=True)
    def test_construct_url(
        self,
        requests_mock,
        reset_access_token_mock,
        protocol,
        domain,
        version,
        endpoint,
        expected_result,
        direct_plus_client,
    ):
        direct_plus_client.protocol = protocol
        direct_plus_client.domain = domain
        direct_plus_client._dnb_request(endpoint, version=version)
        requests_mock.get.assert_called_once_with(expected_result, headers=mock.ANY, params=mock.ANY)

    @pytest.mark.parametrize(
        ('extra_headers', 'expected_headers'),
        (
            (
                (('Cache-Control', 'no-cache'),),  # Add Cache-Control
                {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization': 'Bearer test_access_token',
                    'Cache-Control': 'no-cache'
                }
            ), (
                (('Host', 'en.wikipedia.org'), ('Accept-Language', 'en-US')),  # Add Host and Accept-Language
                {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization': 'Bearer test_access_token',
                    'Host': 'en.wikipedia.org',
                    'Accept-Language': 'en-US'
                }
            ), (
                (('Accept', 'image/jpeg'), ('Accept-Encoding', 'gzip')),  # Overwrite Accept add Accept-Encoding
                {
                    'Content-Type': 'application/json',
                    'Accept': 'image/jpeg',
                    'Authorization': 'Bearer test_access_token',
                    'Accept-Encoding': 'gzip'
                }
            ), (
                (('Content-Type', 'application/xml'),),  # Override Content-Type
                {
                    'Content-Type': 'application/xml',
                    'Accept': 'application/json',
                    'Authorization': 'Bearer test_access_token'
                }
            ),
        )
    )
    @mock.patch('dmutils.direct_plus_client.requests.get', autospec=True)
    def test_combines_headers(
        self,
        requests_get_mock,
        extra_headers,
        expected_headers,
        direct_plus_client,
        r_mock_with_token_request
    ):
        direct_plus_client._dnb_request('endpoint', extra_headers=extra_headers)
        requests_get_mock.assert_called_once_with(mock.ANY, headers=expected_headers, params=mock.ANY)

    @pytest.mark.parametrize('method', ('get', 'post', 'put', 'patch', 'delete', 'head'))
    @mock.patch('dmutils.direct_plus_client.DirectPlusClient._reset_access_token', autospec=True)
    @mock.patch('dmutils.direct_plus_client.requests', autospec=True)
    def test_calls_correct_requests_method(self, requests_mock, reset_access_token_mock, method, direct_plus_client):
        direct_plus_client._dnb_request('endpoint', method=method)
        getattr(requests_mock, method).assert_called_once()
        for uncalled_method in {'get', 'post', 'put', 'patch', 'delete', 'head'} - {method}:
            getattr(requests_mock, uncalled_method).assert_not_called()

    @mock.patch('dmutils.direct_plus_client.DirectPlusClient._reset_access_token', autospec=True)
    @mock.patch('dmutils.direct_plus_client.requests', autospec=True)
    def test_fails_with_non_existent_method(self, requests_mock, reset_access_token_mock, direct_plus_client):
        with pytest.raises(AttributeError, match="Mock object has no attribute 'foo'"):
            direct_plus_client._dnb_request('endpoint', method='foo')

    def test_request_is_retried_once_if_token_invalid(self, r_mock_with_token_request, direct_plus_client):
        unsuccessful_token_response = {
            'status_code': 401,
            'json': {
                'error': {
                    "errorMessage": (
                        'You are not currently authorised to access this product. '
                        'Please contact your D&B account representative'
                    ),
                    "errorCode": '00004'
                }
            }
        }
        successful_token_response = {
            'status_code': 200,
            'json': {'organization': {'duns': '291346567', 'primaryName': 'TEST COMPANY (UK) LIMITED'}}
        }
        r_mock_with_token_request.get(
            'https://plus.dnb.com/v1/data/duns/291346567?productId=cmpelk&versionId=v2',
            [unsuccessful_token_response, successful_token_response]
        )

        resp = direct_plus_client._dnb_request(
            f'data/duns/291346567', payload={'productId': 'cmpelk', 'versionId': 'v2'}
        )

        # r_mock_with_token_request calls '/v2/token' on setup
        # '/v1/data/duns/291346567' then returns a 401 error (unsuccessful_token_response)
        # causing another call to '/v2/token' to refresh the token
        # and a final call to '/v1/data/duns/291346567' which returns a 200 and our json (successful_token_response)
        expected_requests = ['/v2/token', '/v1/data/duns/291346567', '/v2/token', '/v1/data/duns/291346567']
        assert [i.path for i in r_mock_with_token_request.request_history] == expected_requests

        # We are returned the final, successful response
        assert resp.status_code == 200
        assert resp.json() == {'organization': {'duns': '291346567', 'primaryName': 'TEST COMPANY (UK) LIMITED'}}

    def test_request_returns_after_two_tries(self, r_mock_with_token_request, direct_plus_client):
        status_code = 401
        json = {
            'error': {
                "errorMessage": (
                    'You are not currently authorised to access this product. '
                    'Please contact your D&B account representative'
                ),
                "errorCode": '00004'
            }
        }
        unsuccessful_token_response = {'status_code': status_code, 'json': json}
        r_mock_with_token_request.get(
            'https://plus.dnb.com/v1/data/duns/291346567?productId=cmpelk&versionId=v2',
            [unsuccessful_token_response, unsuccessful_token_response]
        )

        resp = direct_plus_client._dnb_request(
            f'data/duns/291346567', payload={'productId': 'cmpelk', 'versionId': 'v2'}
        )

        # r_mock_with_token_request calls '/v2/token' on setup
        # '/v1/data/duns/291346567' then returns a 401 error (unsuccessful_token_response)
        # causing another call to '/v2/token' to refresh the token
        # and a final call to '/v1/data/duns/291346567' which returns another 401 error
        expected_requests = ['/v2/token', '/v1/data/duns/291346567', '/v2/token', '/v1/data/duns/291346567']
        assert [i.path for i in r_mock_with_token_request.request_history] == expected_requests

        # We are returned the final, unsuccessful response
        assert resp.status_code == status_code == 401
        assert resp.json() == json
