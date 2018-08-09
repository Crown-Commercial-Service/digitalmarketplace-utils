from flask import redirect, render_template, url_for, flash, session, request, current_app
from flask_wtf.csrf import CSRFError


def csrf_handler(e):
    """
    Workaround for a bug in Flask 0.10.1.
    CSRFErrors are caught under 400 BadRequest exceptions, so this heavy-handed solution
     catches all 400s, and immediately discards non-CSRFError instances.

    :param e: CSRF exception instance
    :param session: Flask session instance
    :param request: Flask request instance
    :param logger: app logger instance
    :return: redirect to login with flashed error message
    """
    if not isinstance(e, CSRFError):
        return render_error_page(e)

    if 'user_id' not in session:
        current_app.logger.info(
            u'csrf.session_expired: Redirecting user to log in page'
        )
    else:
        current_app.logger.info(
            u'csrf.invalid_token: Aborting request, user_id: {user_id}',
            extra={'user_id': session['user_id']}
        )

    flash('Your session has expired. Please log in again.', "error")
    return redirect(url_for('external.render_login', next=request.path))


def render_error_page(e=None, status_code=None):
    """
    Either an exception or a status code must be supplied.
    :param e: exception instance, e.g. Forbidden()
    :param status_code: int status code, e.g. 403
    :return: Flask render_template response. The error templates must be present in the app (either
    copied from the FE Toolkit, or a custom template for that app).
    """
    if not e or status_code:
        # Something's gone wrong! To save going in an endless error loop let's just render a 500
        status_code = 500

    template_map = {
        400: "errors/400.html",
        404: "errors/404.html",
        500: "errors/500.html",
        503: "errors/500.html",
    }

    if not status_code or status_code not in template_map:
        status_code = 500 if e.code not in template_map else e.code

    return render_template(template_map[status_code]), status_code
