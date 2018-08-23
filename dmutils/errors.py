from flask import redirect, render_template, url_for, flash, session, request, current_app
from jinja2.exceptions import TemplateNotFound


def csrf_handler(csrf_error):
    """
    :param csrf_error: CSRF exception instance
    :param session: Flask session instance
    :param request: Flask request instance
    :param logger: app logger instance
    :return: redirect to login with flashed error message
    """
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
    return redirect_to_login(csrf_error)


def redirect_to_login(e):
    if request.method == 'GET':
        return redirect(url_for('external.render_login', next=request.path))
    else:
        return redirect(url_for('external.render_login'))


def render_error_page(e=None, status_code=None, error_message=None):
    """
    Either an exception or a status code must be supplied.
    :param e: exception instance, e.g. Forbidden()
    :param status_code: int status code, e.g. 403
    :return: Flask render_template response. The error templates must be present in the app (either
    copied from the FE Toolkit, or a custom template for that app).
    """
    if not (e or status_code):
        # Something's gone wrong! To save going in an endless error loop let's just render a 500
        status_code = 500

    template_map = {
        400: "errors/400.html",
        404: "errors/404.html",
        410: "errors/410.html",
        500: "errors/500.html",
        503: "errors/500.html",
    }

    if not status_code:
        # Handle exceptions with .status_code, not .code (e.g. dmapiclient.HTTPError)
        if hasattr(e, 'status_code'):
            status_code = e.status_code
        elif hasattr(e, 'code'):
            status_code = e.code
        else:
            # Map unknown status codes to 500
            status_code = 500

    if status_code not in template_map:
        status_code = 500

    try:
        # Try app error templates first
        return render_template(template_map[status_code], error_message=error_message), status_code
    except TemplateNotFound:
        # Fall back to toolkit error templates
        return render_template("toolkit/{}".format(template_map[status_code]), error_message=error_message), status_code
