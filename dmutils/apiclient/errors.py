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
