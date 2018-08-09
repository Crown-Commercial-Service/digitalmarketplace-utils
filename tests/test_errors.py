import mock
import pytest

from flask import session
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError, ServiceUnavailable, ImATeapot
from dmutils.errors import csrf_handler, render_error_page
from dmutils.external import external as external_blueprint


@pytest.mark.parametrize('user_session', (True, False))
@mock.patch('dmutils.errors.current_app')
def test_csrf_handler_redirects_to_login(current_app, user_session, app):

    with app.test_request_context('/'):
        app.config['WTF_CSRF_ENABLED'] = True
        app.register_blueprint(external_blueprint)

        if user_session:
            # Our user is logged in
            session['user_id'] = 1234

        response = csrf_handler(CSRFError())

        assert response.status_code == 302
        assert response.location == '/user/login?next=%2F'

        if user_session:
            assert current_app.logger.info.call_args_list == [
                mock.call('csrf.invalid_token: Aborting request, user_id: {user_id}', extra={'user_id': 1234})
            ]
        else:
            assert current_app.logger.info.call_args_list == [
                mock.call('csrf.session_expired: Redirecting user to log in page')
            ]


@mock.patch('dmutils.errors.render_template')
def test_csrf_handler_sends_other_400s_to_render_error_page(render_template, app):

    with app.test_request_context('/'):
        app.config['WTF_CSRF_ENABLED'] = True
        app.register_blueprint(external_blueprint)

        assert csrf_handler(BadRequest()) == (render_template.return_value, 400)
        assert render_template.call_args_list == [mock.call('errors/400.html')]


@pytest.mark.parametrize('exception, status_code, expected_template', [
    (BadRequest, 400, 'errors/400.html'),
    (NotFound, 404, 'errors/404.html'),
    (InternalServerError, 500, 'errors/500.html'),
    (ServiceUnavailable, 503, 'errors/500.html'),
])
@mock.patch('dmutils.errors.render_template')
def test_render_error_page(render_template, exception, status_code, expected_template, app):
    with app.test_request_context('/'):
        assert render_error_page(exception()) == (render_template.return_value, status_code)
        assert render_template.call_args_list == [mock.call(expected_template)]


@mock.patch('dmutils.errors.render_template')
def test_render_error_page_with_custom_http_exception(render_template, app):
    class CustomHTTPError(Exception):
        def __init__(self):
            self.status_code = 500

    with app.test_request_context('/'):
        assert render_error_page(CustomHTTPError()) == (render_template.return_value, 500)
        assert render_template.call_args_list == [mock.call('errors/500.html')]


@mock.patch('dmutils.errors.render_template')
def test_render_error_page_for_unknown_status_code_defaults_to_500(render_template, app):
    with app.test_request_context('/'):
        assert render_error_page(ImATeapot()) == (render_template.return_value, 500)
        assert render_template.call_args_list == [mock.call('errors/500.html')]
