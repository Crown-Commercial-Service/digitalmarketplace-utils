from io import StringIO
import json
import logging
import os.path
import tempfile
import time

import mock

from flask import request
import pytest

from dmtestutils.comparisons import AnyStringMatching, AnySupersetOf, RestrictedAny

from dmutils.logging import init_app, JSONFormatter, CustomLogFormatter, configure_handler
from dmutils.logging import (LOG_FORMAT, get_json_log_format, AppNameFilter, RequestExtraContextFilter,
                             AppStackLocationFilter, AppInstanceFilter)


def test_configure_handler(app):
    handler = mock.Mock()
    configure_handler(handler, app, mock.Mock())
    filter_classes = [x[0][0].__class__ for x in handler.addFilter.call_args_list]
    assert AppNameFilter in filter_classes
    assert RequestExtraContextFilter in filter_classes
    assert AppStackLocationFilter in filter_classes
    assert AppInstanceFilter not in filter_classes


def test_configure_handler_has_instance_index_where_present(app, os_environ):
    os_environ.update({'CF_INSTANCE_INDEX': '1'})
    handler = mock.Mock()
    configure_handler(handler, app, mock.Mock())
    filter_classes = [x[0][0].__class__ for x in handler.addFilter.call_args_list]
    assert AppInstanceFilter in filter_classes


def test_request_extra_context_filter_not_in_app_context():
    # using spec_set to ensure no attribute-setting is attempted on this "record"
    result = RequestExtraContextFilter().filter(mock.Mock(spec_set=[]))
    assert result.called is False


def test_request_extra_context_filter_in_app_context(app):
    with app.test_request_context('/'):
        test_extra_log_context = {
            "poldy": "Old Ollebo, M. P.",
            "Dante": "Riordan",
            "farthing": None,
        }
        # add a simple mock callable instead of using our full custom request implementation
        request.get_extra_log_context = mock.Mock(spec_set=[])
        request.get_extra_log_context.return_value = test_extra_log_context

        # using spec_set to ensure only our listed keys are set on this "record"
        result = RequestExtraContextFilter().filter(mock.Mock(spec_set=list(test_extra_log_context.keys())))

        assert request.get_extra_log_context.call_args_list == [()]  # a single zero-arg call
        # ...and the mock record should have all its values set appropriately
        assert {
            k: getattr(result, k)
            for k in test_extra_log_context.keys()
        } == {
            k: v or None
            for k, v in test_extra_log_context.items()
        }


def test_request_extra_context_filter_no_method(app):
    with app.test_request_context('/'):
        # not adding a get_extra_log_context mock method to request to check we behave gracefully when not using a
        # request class that implements this

        # using spec_set to ensure no attribute-setting is attempted on this "record"
        result = RequestExtraContextFilter().filter(mock.Mock(spec_set=[]))
        assert result.called is False


def test_init_app_adds_stream_handler_without_log_path(app):

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


def test_init_app_only_adds_handlers_to_defined_loggers(app):
    for logger in logging.Logger.manager.loggerDict.values():
        logger.handlers = []

    init_app(app)

    loggers = {
        k for k, v in logging.Logger.manager.loggerDict.items() if v.handlers
        and isinstance(v.handlers[0], logging.StreamHandler)
    }

    assert loggers == {'flask.app', 'dmutils', 'dmapiclient', 'flask_wtf.csrf', 'urllib3.util.retry'}


def test_urllib3_retry_logger_not_configured_for_search_api(app):
    app.config['DM_APP_NAME'] = 'search-api'
    for logger in logging.Logger.manager.loggerDict.values():
        logger.handlers = []

    init_app(app)

    loggers = {
        k for k, v in logging.Logger.manager.loggerDict.items() if v.handlers
        and isinstance(v.handlers[0], logging.StreamHandler)
    }

    assert 'urllib3.util.retry' not in loggers


def _set_request_class_is_sampled(app, sampled):
    class _Request(app.request_class):
        is_sampled = sampled

    app.request_class = _Request


@pytest.mark.parametrize("is_sampled", (None, False))
def test_app_request_logs_responses_with_info_level_not_sampled(app_with_mocked_logger, is_sampled):
    if is_sampled is not None:
        _set_request_class_is_sampled(app_with_mocked_logger, is_sampled)

    app_with_mocked_logger.test_client().get('/')

    expected_call = mock.call(
        logging.INFO,
        '{method} {url} {status}',
        extra={
            "url": "http://localhost/",
            "status": 404,
            "method": "GET",
            "endpoint": None,
            "duration_real": RestrictedAny(lambda value: isinstance(value, float) and 0 < value),
            "duration_process": RestrictedAny(lambda value: isinstance(value, float) and 0 < value),
            "process_": RestrictedAny(lambda value: isinstance(value, int)),
            "thread_": RestrictedAny(lambda value: isinstance(value, (str, bytes,))),
        },
    )

    assert app_with_mocked_logger.logger.log.call_args_list == [expected_call]


def test_app_request_logs_responses_with_info_level_sampled(app_with_mocked_logger):
    _set_request_class_is_sampled(app_with_mocked_logger, True)

    app_with_mocked_logger.test_client().get('/')

    expected_call = mock.call(
        logging.DEBUG,
        'Received request {method} {url}',
        extra={
            "url": "http://localhost/",
            "method": "GET",
            "endpoint": None,
            "process_": RestrictedAny(lambda value: isinstance(value, int)),
            "thread_": RestrictedAny(lambda value: isinstance(value, (str, bytes,))),
        },
    )

    assert expected_call in app_with_mocked_logger.logger.log.call_args_list


@pytest.mark.parametrize("is_sampled", (None, False,))
def test_app_request_logs_5xx_responses_with_error_level_not_sampled(app_with_mocked_logger, is_sampled):
    if is_sampled is not None:
        _set_request_class_is_sampled(app_with_mocked_logger, is_sampled)

    @app_with_mocked_logger.route('/')
    def error_route():
        time.sleep(0.05)
        return 'error', 500

    app_with_mocked_logger.test_client().get('/')

    assert app_with_mocked_logger.logger.log.call_args_list == [
        mock.call(
            logging.ERROR,
            '{method} {url} {status}',
            extra={
                "url": "http://localhost/",
                "status": 500,
                "method": "GET",
                "endpoint": "error_route",
                "duration_real": RestrictedAny(lambda value: isinstance(value, float) and 0.05 <= value),
                "duration_process": RestrictedAny(lambda value: isinstance(value, float) and 0 < value),
                "process_": RestrictedAny(lambda value: isinstance(value, int)),
                "thread_": RestrictedAny(lambda value: isinstance(value, (str, bytes,))),
            },
        )
    ]


def test_app_request_logs_5xx_responses_with_error_level_sampled(app_with_mocked_logger):

    _set_request_class_is_sampled(app_with_mocked_logger, True)

    @app_with_mocked_logger.route('/')
    def error_route():
        time.sleep(0.05)
        return 'error', 500

    app_with_mocked_logger.test_client().get('/')

    expected_call = mock.call(
        logging.DEBUG,
        'Received request {method} {url}',
        extra={
            "url": "http://localhost/",
            "method": "GET",
            "endpoint": "error_route",
            "process_": RestrictedAny(lambda value: isinstance(value, int)),
            "thread_": RestrictedAny(lambda value: isinstance(value, (str, bytes,))),
        },
    )

    assert expected_call in app_with_mocked_logger.logger.log.call_args_list


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
        self.formatter = JSONFormatter(get_json_log_format())
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
        assert 'trace_id' not in result
        assert 'application' in result
        assert 'app_name' not in result
        assert 'spanId' in result
        assert 'span_id' not in result
        assert 'parentSpanId' in result
        assert 'parent_span_id' not in result
        assert 'isSampled' in result
        assert 'is_sampled' not in result
        assert 'debugFlag' in result
        assert 'debug_flag' not in result

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

    def test_log_message_shows_missing_key_if_fields_are_not_found(self):
        self.logger.info("hello {bar}")
        result = json.loads(self.buffer.getvalue())

        assert result['message'] == "hello {bar: missing key}"

    def test_missing_key_when_formatting_logs_a_warning(self):
        self.logger.info("hello {barry}")
        raw_result = self.dmbuffer.getvalue()
        result = json.loads(raw_result)

        assert result['message'].startswith("Missing keys when formatting log message: ('barry',)")
        assert result['levelname'] == 'WARNING'

    def test_two_missing_keys_when_formatting_logs_a_warning(self):
        self.logger.info("hello {barry} {paul}")
        raw_result = self.dmbuffer.getvalue()
        result = json.loads(raw_result)

        assert result['message'].startswith("Missing keys when formatting log message: ('barry', 'paul')")
        assert result['levelname'] == 'WARNING'

    def test_failed_log_message_formatting_logs_an_error(self):
        self.logger.info("hello {one} {two} {three} {four} {five} {six}")
        raw_result = self.dmbuffer.getvalue()
        result = json.loads(raw_result)

        assert result['message'].startswith("Too many missing keys when attempting to format")


@pytest.mark.parametrize("is_sampled", (False, True,))
def test_log_context_handling_in_initialized_app_high_level(app_with_stream_logger, is_sampled):
    app, stream = app_with_stream_logger

    def _logging_call_site(app):
        app.logger.info(
            "Charming day {ankles}, {underleaves}, {parent_span_id}",
            extra={"underleaves": "ample"},
        )

        _set_request_class_is_sampled(app_with_stream_logger, is_sampled)

        with app.test_request_context('/'):
            test_extra_log_context = {
                "ankles": "thinsocked",
                "span_id": "beesWaxed",
            }

            request.get_extra_log_context = mock.Mock(spec_set=[])
            request.get_extra_log_context.return_value = test_extra_log_context

            # we perform the log call in a specifically designated & named function to exercise & be able to reliably
            # assert the behaviour of the introspective aspects of our logging
            _logging_call_site(app)

        all_lines = tuple(json.loads(line) for line in stream.read().splitlines())

        assert all_lines == (
            AnySupersetOf({
                "message": "Missing keys when formatting log message: ('parent_span_id',)",
                # it may seem foolish and a bit fragile to include the following parameters in our assertions but
                # properly testing introspective behaviour is always going to get a bit weird and meta in that regard.
                "app_funcName": "_logging_call_site",
                "app_pathname": os.path.normcase(_logging_call_site.__code__.co_filename),
                "app_lineno": RestrictedAny(lambda value: isinstance(value, int)),
                "lineno": RestrictedAny(lambda value: isinstance(value, int)),
                "pathname": AnyStringMatching(r".+\/dmutils\/logging\.pyc?"),
            }),
            AnySupersetOf({
                "time": mock.ANY,
                "application": mock.ANY,
                "message": "Charming day thinsocked, ample, {parent_span_id: missing key}",
                "underleaves": "ample",
                "ankles": "thinsocked",
                "spanId": "beesWaxed",
                "parentSpanId": None,
                "requestId": None,
                "debugFlag": None,
                "isSampled": None,
                # as above, these parameters are included in the assertion to ensure our modifications haven't affected
                # the regular logging introspection features
                "lineno": RestrictedAny(lambda value: isinstance(value, int)),
                "pathname": os.path.normcase(_logging_call_site.__code__.co_filename),
                **({
                    "app_funcName": "_logging_call_site",
                    "app_pathname": os.path.normcase(_logging_call_site.__code__.co_filename),
                    "app_lineno": RestrictedAny(lambda value: isinstance(value, int)),
                } if is_sampled else {}),
            }),
        )

        if not is_sampled:
            # AppStackLocationFilter shouldn't have included information in this low-urgency message
            for unexpected_key in (
                "app_funcName",
                "app_lineno",
                "app_pathname",
            ):
                assert unexpected_key not in all_lines[1]

        for unexpected_key in (
            "span_id",
            "trace_id",
            "traceId",
            "request_id",
            "debug_flag",
            "is_sampled",
            "parent_span_id",  # also ensuring "missing key" functionality didn't add a value for this
        ):
            assert not any(unexpected_key in line for line in all_lines)


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
        self.formatter = CustomLogFormatter(LOG_FORMAT)
        self.logger, self.buffer = self._create_logger('logging-test', self.formatter)
        self.dmlogger, self.dmbuffer = self._create_logger('dmutils', self.formatter)

    def teardown(self):
        del self.logger.handlers[:]
        del self.dmlogger.handlers[:]

    def test_log_message_gets_formatted(self):
        self.logger.info("hello {foo}", extra={'foo': 'bar'})
        result = self.buffer.getvalue()

        assert '"hello bar"' in result

    def test_log_message_none_substituted(self):
        self.logger.info("hello 123", extra={"app_name": None})
        result = self.buffer.getvalue()

        assert result.split()[2] == "-"

    def test_log_message_is_unchanged_if_fields_are_not_found(self):
        self.logger.info("hello {bar}")
        result = self.buffer.getvalue()

        assert '"hello {bar}"' in result

    def test_log_message_doesnt_include_json_extra_keys(self):
        self.logger.info("hello {foo}", extra={'foo': 'bar', "span_id": "1234"})
        result = self.buffer.getvalue()

        assert '1234' not in result

    def test_failed_log_message_formatting_logs_an_error(self):
        self.logger.info("hello {barry}")
        result = self.dmbuffer.getvalue()

        assert 'failed to format log message' in result

    def test_failed_log_message_formatting_still_logs(self):
        self.logger.info("hello {")

        assert 'failed to format log message' in self.dmbuffer.getvalue()
        assert 'hello {' in self.buffer.getvalue()
