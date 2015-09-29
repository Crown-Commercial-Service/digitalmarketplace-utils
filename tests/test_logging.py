from __future__ import absolute_import
import tempfile
import logging
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import json

from dmutils import request_id
from dmutils.logging import init_app, RequestIdFilter, JSONFormatter, CustomLogFormatter
from dmutils.logging import LOG_FORMAT, TIME_FORMAT


def test_request_id_filter_not_in_app_context():
    assert RequestIdFilter().request_id == 'no-request-id'


def test_formatter_request_id(app_with_logging):
    headers = {'DM-Request-Id': 'generated'}
    request_id.init_app(app_with_logging)  # set CustomRequest class
    with app_with_logging.test_request_context('/', headers=headers):
        assert RequestIdFilter().request_id == 'generated'


def test_formatter_request_id_in_non_logging_app(app):
    with app.test_request_context('/', headers={'DM-Request-Id': 'generated'}):
        assert RequestIdFilter().request_id == 'no-request-id'


def test_init_app_adds_stream_handler_in_debug(app):
    app.config['DEBUG'] = True
    init_app(app)

    assert len(app.logger.handlers) == 1
    assert isinstance(app.logger.handlers[0], logging.StreamHandler)


def test_init_app_adds_file_handlers_in_non_debug(app):
    with tempfile.NamedTemporaryFile() as f:
        app.config['DEBUG'] = False
        app.config['DM_LOG_PATH'] = f.name
        init_app(app)

        assert len(app.logger.handlers) == 2
        assert isinstance(app.logger.handlers[0], logging.FileHandler)
        assert isinstance(app.logger.handlers[0].formatter, CustomLogFormatter)
        assert isinstance(app.logger.handlers[1], logging.FileHandler)
        assert isinstance(app.logger.handlers[1].formatter, JSONFormatter)


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
