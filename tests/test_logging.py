from __future__ import absolute_import
from flask import Flask
import tempfile
import logging
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import json

import mock

from dmutils import request_id
from dmutils.logging import init_app, RequestIdFilter, JSONFormatter, CustomLogFormatter
from dmutils.logging import LOG_FORMAT, TIME_FORMAT


def test_request_id_filter_not_in_app_context():
    assert RequestIdFilter().request_id == 'no-request-id'


def test_formatter_request_id(app):
    headers = {'DM-Request-Id': 'generated'}
    request_id.init_app(app)  # set CustomRequest class
    with app.test_request_context('/', headers=headers):
        assert RequestIdFilter().request_id == 'generated'


def test_formatter_request_id_in_non_logging_app(app):
    with app.test_request_context('/', headers={'DM-Request-Id': 'generated'}):
        assert RequestIdFilter().request_id == 'no-request-id'


def test_init_app_adds_stream_handler_without_log_path(app):
    init_app(app)

    assert len(app.logger.handlers) == 1
    assert isinstance(app.logger.handlers[0], logging.StreamHandler)
    assert isinstance(app.logger.handlers[0].formatter, JSONFormatter)


def test_init_app_adds_file_handler_with_log_path(app):
    with tempfile.NamedTemporaryFile() as f:
        app.config['DM_LOG_PATH'] = f.name
        init_app(app)

        assert len(app.logger.handlers) == 1
        assert isinstance(app.logger.handlers[0], logging.FileHandler)
        assert isinstance(app.logger.handlers[0].formatter, JSONFormatter)


def test_init_app_adds_stream_handler_with_plain_text_format_when_config_env_set(app):
    app.config['DM_PLAIN_TEXT_LOGS'] = True
    init_app(app)

    assert len(app.logger.handlers) == 1
    assert isinstance(app.logger.handlers[0], logging.StreamHandler)
    assert isinstance(app.logger.handlers[0].formatter, CustomLogFormatter)


def test_app_after_request_logs_responses_with_info_level(app):
    # since app.logger is a read-only property we need to patch the Flask class
    with mock.patch('flask.Flask.logger') as logger:
        app.test_client().get('/')

        logger.log.assert_called_once_with(
            logging.INFO,
            '{method} {url} {status}',
            extra={'url': u'http://localhost/', 'status': 404, 'method': 'GET'}
        )


def test_app_after_request_logs_5xx_responses_with_error_level(app):
    @app.route('/')
    def error_route():
        return 'error', 500

    # since app.logger is a read-only property we need to patch the Flask class
    with mock.patch('flask.Flask.logger') as logger:
        app.test_client().get('/')

        logger.log.assert_called_once_with(
            logging.ERROR,
            '{method} {url} {status}',
            extra={'url': u'http://localhost/', 'status': 500, 'method': 'GET'}
        )


class TestJSONFormatter(object):
    def _create_logger(self, name, formatter):
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        buffer = StringIO()
        handler = logging.StreamHandler(buffer)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger, buffer

    def setup(self):
        self.formatter = JSONFormatter(LOG_FORMAT, TIME_FORMAT)
        self.logger, self.buffer = self._create_logger('logging-test', self.formatter)
        self.dmlogger, self.dmbuffer = self._create_logger('dmutils', self.formatter)

    def teardown(self):
        del self.logger.handlers[:]
        del self.dmlogger.handlers[:]

    def test_json_formatter_renames_fields(self):
        self.logger.info("hello")
        result = json.loads(self.buffer.getvalue())
        self.dmbuffer.getvalue()

        assert 'time' in result
        assert 'asctime' not in result
        assert 'requestId' in result
        assert 'request_id' not in result
        assert 'application' in result
        assert 'app_name' not in result

    def test_log_type_is_set_to_application(self):
        self.logger.info("hello")
        result = json.loads(self.buffer.getvalue())
        self.dmbuffer.getvalue()

        assert result['logType'] == 'application'

    def test_log_message_gets_formatted(self):
        self.logger.info("hello {foo}", extra={'foo': 'bar'})
        result = json.loads(self.buffer.getvalue())
        self.dmbuffer.getvalue()

        assert result['message'] == "hello bar"

    def test_log_message_is_unchanged_if_fields_are_not_found(self):
        self.logger.info("hello {bar}")
        result = json.loads(self.buffer.getvalue())

        assert result['message'] == "hello {bar}"

    def test_failed_log_message_formatting_logs_an_error(self):
        self.logger.info("hello {barry}")
        raw_result = self.dmbuffer.getvalue()
        result = json.loads(raw_result)

        assert result['message'].startswith("failed to format log message")


class TestCustomLogFormatter(object):
    def _create_logger(self, name, formatter):
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG)
        buffer = StringIO()
        handler = logging.StreamHandler(buffer)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger, buffer

    def setup(self):
        self.formatter = CustomLogFormatter(LOG_FORMAT, TIME_FORMAT)
        self.logger, self.buffer = self._create_logger('logging-test', self.formatter)
        self.dmlogger, self.dmbuffer = self._create_logger('dmutils', self.formatter)

    def teardown(self):
        del self.logger.handlers[:]
        del self.dmlogger.handlers[:]

    def test_log_message_gets_formatted(self):
        self.logger.info("hello {foo}", extra={'foo': 'bar'})
        result = self.buffer.getvalue()

        assert '"hello bar"' in result

    def test_log_message_is_unchanged_if_fields_are_not_found(self):
        self.logger.info("hello {bar}")
        result = self.buffer.getvalue()

        assert '"hello {bar}"' in result

    def test_failed_log_message_formatting_logs_an_error(self):
        self.logger.info("hello {barry}")
        result = self.dmbuffer.getvalue()

        assert 'failed to format log message' in result

    def test_failed_log_message_formatting_still_logs(self):
        self.logger.info("hello {")

        assert 'failed to format log message' in self.dmbuffer.getvalue()
        assert 'hello {' in self.buffer.getvalue()
