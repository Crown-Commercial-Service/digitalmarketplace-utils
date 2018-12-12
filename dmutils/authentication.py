from werkzeug.exceptions import Unauthorized


class UnauthorizedWWWAuthenticate(Unauthorized):
    """
    This is a near verbatim copy of an improvement to an as-yet-unreleased upstream version of werkzeug that allows
    us to specify a www_authenticate argument containing the contents of that field. We should get rid of this once
    we're able to upgrade past that version.

    From werkzeug 8ed5b3f9a285eca756c3ab33f8c370a88eab3842
    """
    def __init__(self, www_authenticate=None, description=None):
        super().__init__(description=description)
        if not isinstance(www_authenticate, (tuple, list)):
            www_authenticate = (www_authenticate,)
        self.www_authenticate = www_authenticate

    def get_headers(self, environ=None):
        headers = super().get_headers(environ)
        if self.www_authenticate:
            headers.append((
                'WWW-Authenticate',
                ', '.join([str(x) for x in self.www_authenticate])
            ))
        return headers
