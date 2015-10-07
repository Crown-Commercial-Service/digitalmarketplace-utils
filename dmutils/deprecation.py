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
            message = "Calling deprecated view '{view_name}'. Dies in {time_left}."
            time_left = dies_at - datetime.utcnow()
            extra = {'view_name': view.__name__, 'time_left': time_left}
            if time_left < timedelta(days=7):
                current_app.logger.error(message, extra=extra)
            else:
                current_app.logger.warning(message, extra=extra)
            response = view(*args, **kwargs)
            response.headers['DM-Deprecated'] = "Dies in {}".format(time_left)
            return response

        return func

    return decorator
