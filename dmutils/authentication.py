from werkzeug.exceptions import Unauthorized


class UnauthorizedWWWAuthenticate(Unauthorized):
    """
    This class exists for back-compatibility. We originally needed it to add support for `www_authenticate` before
    werkzeug added it to Unauthorized. Users should switch to use Unauthorized directly.
    """
    def __init__(self, www_authenticate=None, description=None):
        if not isinstance(www_authenticate, (tuple, list)):
            www_authenticate = (www_authenticate,)
        super().__init__(description=description, www_authenticate=www_authenticate)
