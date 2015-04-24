from __future__ import absolute_import
import tempfile
import logging

from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request
import mock
from flask import Flask
import pytest

from dmutils.logging import init_app, RequestIdFilter, CustomRequest


def test_get_request_id_from_request_id_header():
    builder = EnvironBuilder()
    builder.headers['DM-REQUEST-ID'] = 'from-header'
    builder.headers['DOWNSTREAM-REQUEST-ID'] = 'from-downstream'
    request = CustomRequest(builder.get_environ())

    request_id = request._get_request_id('DM-REQUEST-ID',
                                         'DOWNSTREAM-REQUEST-ID')

    assert request_id == 'from-header'


def test_get_request_id_from_downstream_header():
    builder = EnvironBuilder()
    builder.headers['DOWNSTREAM-REQUEST-ID'] = 'from-downstream'
    request = CustomRequest(builder.get_environ())

    request_id = request._get_request_id('DM-REQUEST-ID',
                                         'DOWNSTREAM-REQUEST-ID')

    assert request_id == 'from-downstream'


@mock.patch('dmutils.logging.uuid.uuid4')
def test_get_request_id_with_no_downstream_header_configured(uuid4_mock):
    builder = EnvironBuilder()
    builder.headers[''] = 'from-downstream'
    request = CustomRequest(builder.get_environ())
    uuid4_mock.return_value = 'generated'

    request_id = request._get_request_id('DM-REQUEST-ID', '')

    uuid4_mock.assert_called_once()
    assert request_id == 'generated'


@mock.patch('dmutils.logging.uuid.uuid4')
def test_get_request_id_generates_id(uuid4_mock):
    builder = EnvironBuilder()
    request = CustomRequest(builder.get_environ())
    uuid4_mock.return_value = 'generated'

    request_id = request._get_request_id('DM-REQUEST-ID',
                                         'DOWNSTREAM-REQUEST-ID')

    uuid4_mock.assert_called_once()
    assert request_id == 'generated'


@pytest.fixture
def app():
    return Flask(__name__)


@pytest.yield_fixture
def inited_app(app):
    with tempfile.NamedTemporaryFile() as f:
        app.config['DM_LOG_PATH'] = f.name
        init_app(app)
        yield app


def test_request_id_is_set_on_response(inited_app):
    client = inited_app.test_client()

    with inited_app.app_context():
        response = client.get('/', headers={'DM-REQUEST-ID': 'generated'})
        assert response.headers['DM-Request-ID'] == 'generated'


def test_request_id_filter_not_in_app_context():
    assert RequestIdFilter().request_id == 'no-request-id'


def test_formatter_request_id(inited_app):
    headers = {'DM-Request-Id': 'generated'}
    with inited_app.test_request_context('/', headers=headers):
        assert RequestIdFilter().request_id == 'generated'


def test_init_app_adds_stream_handler_in_debug(app):
    app.config['DEBUG'] = True
    init_app(app)

    assert len(app.logger.handlers) == 1
    assert isinstance(app.logger.handlers[0], logging.StreamHandler)


def test_init_app_adds_file_handler_in_non_debug(app):
    with tempfile.NamedTemporaryFile() as f:
        app.config['DEBUG'] = False
        app.config['DM_LOG_PATH'] = f.name
        init_app(app)

        assert len(app.logger.handlers) == 1
        assert isinstance(app.logger.handlers[0], logging.FileHandler)
