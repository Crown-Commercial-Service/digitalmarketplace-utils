from functools import wraps
from datetime import datetime, timedelta

from flask import current_app


def deprecated(dies_at):
    """Mark a flask view as deprecated

    Usage:
    @deprecated(dies_at=datetime(2015, 8, 1))
    """
    def decorator(view):
        @wraps(view)
        def func(*args, **kwargs):
            message = "Calling deprecated view '%s'. Dies in %s."
            time_left = dies_at - datetime.now()
            if time_left < timedelta(days=7):
                current_app.logger.error(message, view.__name__, time_left)
            else:
                current_app.logger.warning(message, view.__name__, time_left)
            response = view(*args, **kwargs)
            response.headers['DM-Deprecated'] = "Dies in {}".format(time_left)
            return response

        return func

    return decorator
