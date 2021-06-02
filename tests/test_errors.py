import json
from unittest import mock
import pytest

from flask import session
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import (
    BadRequest, Forbidden, NotFound, Gone, InternalServerError, ServiceUnavailable, ImATeapot
)
from werkzeug.http import dump_cookie
from jinja2.exceptions import TemplateNotFound

from dmutils.authentication import UnauthorizedWWWAuthenticate
from dmutils.errors.frontend import csrf_handler, redirect_to_login, render_error_page
from dmutils.errors.api import json_error_handler, validation_error_handler, ValidationError
from dmutils.external import external as external_blueprint


@pytest.mark.parametrize('cookie_probe_expect_present', (True, False))
@pytest.mark.parametrize('user_session', (True, False))
def test_csrf_handler_redirects_to_login(user_session, app, cookie_probe_expect_present):
    with app.test_request_context('/', environ_base={
        "HTTP_COOKIE": dump_cookie("foo", "bar"),
    }):
        app.logger = mock.MagicMock()
        app.config.update({
            "DM_COOKIE_PROBE_COOKIE_NAME": "foo",
            "DM_COOKIE_PROBE_COOKIE_VALUE": "bar",
            "DM_COOKIE_PROBE_EXPECT_PRESENT": cookie_probe_expect_present,
            "WTF_CSRF_ENABLED": True,
        })
        app.register_blueprint(external_blueprint)

        if user_session:
            # Our user is logged in
            session['user_id'] = 1234

        response = csrf_handler(CSRFError())

        assert response.status_code == 302
        assert response.location == '/user/login?next=%2F'

        if user_session:
            assert app.logger.info.call_args_list == [
                mock.call('csrf.invalid_token: Aborting request, user_id: {user_id}', extra={'user_id': 1234})
            ]
        else:
            assert app.logger.info.call_args_list == [
                mock.call('csrf.session_expired: Redirecting user to log in page')
            ]


@pytest.mark.parametrize('cookie_kv', (
    ("boo", "par",),
    ("foo", "blah",),
    None,
))
@mock.patch('dmutils.errors.frontend.render_template')
def test_cookie_probe_incorrect(render_template, app, cookie_kv):
    render_template.return_value = "<html>Oh dear</html>"

    with app.test_request_context('/', environ_base=cookie_kv and {
        "HTTP_COOKIE": dump_cookie(*cookie_kv),
    }):
        app.config.update({
            "DM_COOKIE_PROBE_COOKIE_NAME": "foo",
            "DM_COOKIE_PROBE_COOKIE_VALUE": "bar",
            "DM_COOKIE_PROBE_EXPECT_PRESENT": True,
            "WTF_CSRF_ENABLED": True,
        })
        app.register_blueprint(external_blueprint)

        response, status_code = csrf_handler(CSRFError())

        assert response == render_template.return_value
        assert status_code == 400
        assert render_template.mock_calls == [
            mock.call(
                "errors/400.html",
                error_message="This feature requires cookies to be enabled for correct operation",
            )
        ]


def test_unauthorised_redirects_to_login(app):
    with app.test_request_context('/'):
        app.register_blueprint(external_blueprint)

        response = redirect_to_login(Forbidden)

        assert response.status_code == 302
        assert response.location == '/user/login?next=%2F'


@pytest.mark.parametrize('exception,expected_status_code,expected_template,expect_log_call', [
    (BadRequest, 400, 'errors/400.html', False),
    (NotFound, 404, 'errors/404.html', False),
    (Gone, 410, 'errors/410.html', False),
    (InternalServerError, 500, 'errors/500.html', True),
    (ServiceUnavailable, 503, 'errors/500.html', True),
    (mock.Mock(code=None), 500, 'errors/500.html', True),
])
@mock.patch('dmutils.errors.frontend.render_template')
def test_render_error_page_with_exception(
    render_template,
    exception,
    expected_status_code,
    expected_template,
    expect_log_call,
    app_with_mocked_logger,
):
    with app_with_mocked_logger.test_request_context('/'):
        exc_instance = exception()
        assert render_error_page(exc_instance) == (render_template.return_value, expected_status_code)
        assert render_template.call_args_list == [
            mock.call(expected_template, error_message=None)
        ]
        assert app_with_mocked_logger.logger.warning.mock_calls == ([
            mock.call(
                'Rendering error page',
                exc_info=True,
                extra={
                    'e': exc_instance,
                    'status_code': None,
                    'error_message': None,
                },
            )
        ] if expect_log_call else [])


@pytest.mark.parametrize('status_code,expected_template,expect_log_call', [
    (400, 'errors/400.html', False,),
    (404, 'errors/404.html', False,),
    (410, 'errors/410.html', False,),
    (500, 'errors/500.html', True,),
    (503, 'errors/500.html', True,),
])
@mock.patch('dmutils.errors.frontend.render_template')
def test_render_error_page_with_status_code(
    render_template,
    status_code,
    expected_template,
    expect_log_call,
    app_with_mocked_logger,
):
    with app_with_mocked_logger.test_request_context('/'):
        assert render_error_page(status_code=status_code) == (render_template.return_value, status_code)
        assert render_template.call_args_list == [mock.call(expected_template, error_message=None)]
        assert app_with_mocked_logger.logger.warning.mock_calls == ([
            mock.call(
                'Rendering error page',
                exc_info=True,
                extra={
                    'e': None,
                    'status_code': status_code,
                    'error_message': None,
                },
            )
        ] if expect_log_call else [])


@mock.patch('dmutils.errors.frontend.render_template')
def test_render_error_page_with_custom_http_exception(render_template, app_with_mocked_logger):
    class CustomHTTPError(Exception):
        def __init__(self):
            self.status_code = 500

    with app_with_mocked_logger.test_request_context('/'):
        exc_instance = CustomHTTPError()
        assert render_error_page(exc_instance) == (render_template.return_value, 500)
        assert render_template.call_args_list == [mock.call('errors/500.html', error_message=None)]
        assert app_with_mocked_logger.logger.warning.mock_calls == [
            mock.call(
                'Rendering error page',
                exc_info=True,
                extra={
                    'e': exc_instance,
                    'status_code': None,
                    'error_message': None,
                },
            )
        ]


@mock.patch('dmutils.errors.frontend.render_template')
def test_render_error_page_for_unknown_status_code_defaults_to_500(render_template, app_with_mocked_logger):
    with app_with_mocked_logger.test_request_context('/'):
        exc_instance = ImATeapot()
        assert render_error_page(exc_instance) == (render_template.return_value, 500)
        assert render_template.call_args_list == [mock.call('errors/500.html', error_message=None)]
        assert app_with_mocked_logger.logger.warning.mock_calls == [
            mock.call(
                'Rendering error page',
                exc_info=True,
                extra={
                    'e': exc_instance,
                    'status_code': None,
                    'error_message': None,
                },
            )
        ]


@mock.patch('dmutils.errors.frontend.render_template')
def test_render_error_page_falls_back_to_toolkit_templates(render_template, app_with_mocked_logger):
    render_template.side_effect = [TemplateNotFound('Oh dear'), "successful rendering"]
    with app_with_mocked_logger.test_request_context('/'):
        exc_instance = ImATeapot()
        assert render_error_page(exc_instance) == ("successful rendering", 500)
        assert render_template.call_args_list == [
            mock.call('errors/500.html', error_message=None),
            mock.call('toolkit/errors/500.html', error_message=None)
        ]
        assert app_with_mocked_logger.logger.warning.mock_calls == [
            mock.call(
                'Rendering error page',
                exc_info=True,
                extra={
                    'e': exc_instance,
                    'status_code': None,
                    'error_message': None,
                },
            )
        ]


@mock.patch('dmutils.errors.frontend.render_template')
def test_render_error_page_passes_error_message_as_context(render_template, app_with_mocked_logger):
    render_template.side_effect = [TemplateNotFound('Oh dear'), "successful rendering"]
    with app_with_mocked_logger.test_request_context('/'):
        exc_instance = ImATeapot()
        assert render_error_page(exc_instance, error_message="Hole in Teapot") == ("successful rendering", 500)
        assert render_template.call_args_list == [
            mock.call('errors/500.html', error_message="Hole in Teapot"),
            mock.call('toolkit/errors/500.html', error_message="Hole in Teapot")
        ]
        assert app_with_mocked_logger.logger.warning.mock_calls == [
            mock.call(
                'Rendering error page',
                exc_info=True,
                extra={
                    'e': exc_instance,
                    'status_code': None,
                    'error_message': "Hole in Teapot",
                },
            )
        ]


def test_api_json_error_handler(app_with_mocked_logger):
    with app_with_mocked_logger.test_request_context('/'):
        try:
            raise ImATeapot("Simply teapot all over me!")
        except ImATeapot as e:
            response = json_error_handler(e)
            assert json.loads(response.get_data()) == {
                "error": "Simply teapot all over me!",
            }
            assert response.status_code == 418
            assert app_with_mocked_logger.logger.warning.mock_calls == []


def test_api_validation_error_handler(app_with_mocked_logger):
    with app_with_mocked_logger.test_request_context('/'):
        try:
            raise ValidationError("Hippogriff")
        except ValidationError as e:
            response = validation_error_handler(e)
            assert json.loads(response.get_data()) == {
                "error": "Hippogriff",
            }
            assert response.status_code == 400
            assert app_with_mocked_logger.logger.warning.mock_calls == []


def test_api_unauth(app_with_mocked_logger):
    with app_with_mocked_logger.test_request_context('/'):
        try:
            raise UnauthorizedWWWAuthenticate(www_authenticate="lemur", description="Bogeyman's trick")
        except UnauthorizedWWWAuthenticate as e:
            response = json_error_handler(e)
            assert json.loads(response.get_data()) == {
                "error": "Bogeyman's trick",
            }
            assert response.status_code == 401
            assert response.headers["www-authenticate"] == "lemur"
            assert app_with_mocked_logger.logger.warning.mock_calls == []


def test_api_internal_server_error(app_with_mocked_logger):
    with app_with_mocked_logger.test_request_context('/'):
        try:
            raise InternalServerError(description="Bip!")
        except InternalServerError as e:
            response = json_error_handler(e)
            assert json.loads(response.get_data()) == {
                "error": "Bip!",
            }
            assert response.status_code == 500
            assert app_with_mocked_logger.logger.warning.mock_calls == [
                mock.call('Generating error response', exc_info=True, extra={'e': e})
            ]
