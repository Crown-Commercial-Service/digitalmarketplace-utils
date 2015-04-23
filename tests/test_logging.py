from __future__ import absolute_import
import tempfile
import logging

from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request
import mock
from flask import Flask, g
import pytest

from dmutils.logging import get_request_id, CustomFormatter, init_app


def test_get_request_id_from_request_id_header():
    builder = EnvironBuilder()
    builder.headers['DM-REQUEST-ID'] = 'from-header'
    builder.headers['DOWNSTREAM-REQUEST-ID'] = 'from-downstream'
    request = Request(builder.get_environ())

    request_id = get_request_id(request,
                                'DM-REQUEST-ID', 'DOWNSTREAM-REQUEST-ID')

    assert request_id == 'from-header'


def test_get_request_id_from_downstream_header():
    builder = EnvironBuilder()
    builder.headers['DOWNSTREAM-REQUEST-ID'] = 'from-downstream'
    request = Request(builder.get_environ())

    request_id = get_request_id(request,
                                'DM-REQUEST-ID', 'DOWNSTREAM-REQUEST-ID')

    assert request_id == 'from-downstream'


@mock.patch('dmutils.logging.uuid.uuid4')
def test_get_request_id_with_no_downstream_header_configured(uuid4_mock):
    builder = EnvironBuilder()
    builder.headers[''] = 'from-downstream'
    request = Request(builder.get_environ())
    uuid4_mock.return_value = 'generated'

    request_id = get_request_id(request,
                                'DM-REQUEST-ID', '')

    uuid4_mock.assert_called_once()
    assert request_id == 'generated'


@mock.patch('dmutils.logging.uuid.uuid4')
def test_get_request_id_generates_id(uuid4_mock):
    builder = EnvironBuilder()
    request = Request(builder.get_environ())
    uuid4_mock.return_value = 'generated'

    request_id = get_request_id(request,
                                'DM-REQUEST-ID', 'DOWNSTREAM-REQUEST-ID')

    uuid4_mock.assert_called_once()
    assert request_id == 'generated'


class MatchingRecord(object):
    def __init__(self, **kwargs):
        self._kwargs = kwargs

    def __eq__(self, other):
        return all(getattr(other, key) == value
                   for key, value in self._kwargs.items())

    def __ne__(self, other):
        return not self.__eq__(other)


@pytest.fixture
def app():
    return Flask(__name__)


@mock.patch('dmutils.logging.get_request_id')
def test_request_id_is_set_on_response(mock_get_request_id, app):
    with tempfile.NamedTemporaryFile() as f:
        app.config['DM_LOG_PATH'] = f.name
        client = app.test_client()
        mock_get_request_id.return_value = 'generated'

        init_app(app)
        with app.app_context():
            response = client.get('/')
            assert response.headers['DM-REQUEST-ID'] == 'generated'


def test_formatter_request_id_not_in_app_context():
    formatter = CustomFormatter('test', 'test')
    assert formatter._get_request_id() == 'not-in-request'


def test_formatter_no_request_id(app):
    formatter = CustomFormatter('test', 'test')
    with app.app_context():
        assert formatter._get_request_id() == 'no-request-id'


def test_formatter_request_id(app):
    formatter = CustomFormatter('test', 'test')
    with app.app_context():
        g.request_id = 'generated'
        assert formatter._get_request_id() == 'generated'


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
