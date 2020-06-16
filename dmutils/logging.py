from __future__ import absolute_import
import logging
import sys
import re
from os import getpid
import os.path
from threading import get_ident as get_thread_ident
import time

from flask import request, current_app
from flask.ctx import has_request_context

from pythonjsonlogger.jsonlogger import JsonFormatter as BaseJSONFormatter

LOG_FORMAT = '%(asctime)s %(app_name)s %(name)s %(levelname)s ' \
             '%(trace_id)s "%(message)s" [in %(pathname)s:%(lineno)d]'


# fields named in LOG_FORMAT and LOG_FORMAT_EXTRA_JSON_KEYS will always be included in json log output even if
# no such field was supplied in the log record, substituting a None value if necessary.
LOG_FORMAT_EXTRA_JSON_KEYS = (
    "span_id",
    "parent_span_id",
    "is_sampled",
    "debug_flag",
)


logger = logging.getLogger(__name__)


def _common_request_extra_log_context():
    return {
        "method": request.method,
        "url": request.url,
        "endpoint": request.endpoint,
        # pid and thread ident are both available on LogRecord by default, as `process` and `thread`
        # respectively but I don't see a straightforward way of selectively including them only in certain
        # log messages - they are designed to be included when the formatter is being configured. This is why
        # I'm manually grabbing them and putting them in as `extra` here, avoiding the existing parameter names
        # to prevent LogRecord from complaining
        "process_": getpid(),
        # stringifying this as it could potentially be a long that json is unable to represent accurately
        "thread_": str(get_thread_ident()),
    }


def init_app(app):
    app.config.setdefault('DM_LOG_LEVEL', 'INFO')
    app.config.setdefault('DM_APP_NAME', 'none')

    @app.before_request
    def before_request():
        # annotating these onto request instead of flask.g as they probably shouldn't be inheritable from a request-less
        # application context
        request.before_request_real_time = time.perf_counter()
        request.before_request_process_time = time.process_time()

        if getattr(request, "is_sampled", False):
            # emit an early log message to record that the request was received by the app
            current_app.logger.log(
                logging.DEBUG,
                "Received request {method} {url}",
                extra=_common_request_extra_log_context(),
            )

    @app.after_request
    def after_request(response):
        current_app.logger.log(
            logging.ERROR if response.status_code // 100 == 5 else logging.INFO,
            '{method} {url} {status}',
            extra={
                "status": response.status_code,
                "duration_real": (
                    (time.perf_counter() - request.before_request_real_time)
                    if hasattr(request, "before_request_real_time") else None
                ),
                "duration_process": (
                    (time.process_time() - request.before_request_process_time)
                    if hasattr(request, "before_request_process_time") else None
                ),
                **_common_request_extra_log_context(),
            },
        )
        return response

    logging.getLogger().addHandler(logging.NullHandler())
    handlers = [logging.StreamHandler(sys.stdout)]

    del app.logger.handlers[:]

    if app.config.get('DM_PLAIN_TEXT_LOGS'):
        formatter = CustomLogFormatter(LOG_FORMAT)
    else:
        formatter = JSONFormatter(get_json_log_format())

    if app.config.get('DM_LOG_PATH'):
        handlers.append(logging.FileHandler(app.config['DM_LOG_PATH']))

    for handler in handlers:
        configure_handler(handler, app, formatter)

    loglevel = logging.getLevelName(app.config['DM_LOG_LEVEL'])
    loggers = [
        app.logger,
        logging.getLogger('dmutils'),
        logging.getLogger('dmapiclient'),
        logging.getLogger('flask_wtf.csrf'),
    ]
    #  The Elasticsearch client used by the search-api uses urllib3 directly and manages retries itself.
    #  This results in more logging than we want from urllib3, so we don't configure the logger for the search-api.
    if app.config['DM_APP_NAME'] != 'search-api':
        loggers.append(logging.getLogger('urllib3.util.retry'))

    for logger_ in loggers:
        for handler in handlers:
            logger_.addHandler(handler)
        logger_.setLevel(loglevel)
    app.logger.info('Logging configured')


def configure_handler(handler, app, formatter):
    handler.setLevel(logging.getLevelName(app.config['DM_LOG_LEVEL']))
    handler.setFormatter(formatter)
    handler.addFilter(AppNameFilter(app.config['DM_APP_NAME']))
    handler.addFilter(RequestExtraContextFilter())
    handler.addFilter(AppStackLocationFilter("app_", app.root_path))
    if os.environ.get('CF_INSTANCE_INDEX'):
        handler.addFilter(AppInstanceFilter())

    return handler


def get_json_log_format():
    return LOG_FORMAT + "".join(f" %({key})s" for key in LOG_FORMAT_EXTRA_JSON_KEYS)


class AppNameFilter(logging.Filter):
    def __init__(self, app_name):
        self.app_name = app_name

    def filter(self, record):
        record.app_name = self.app_name

        return record


class AppInstanceFilter(logging.Filter):
    def __init__(self):
        self.instance_index = os.environ['CF_INSTANCE_INDEX']

    def filter(self, record):
        record.instance_index = self.instance_index

        return record


class BaseExtraStackLocationFilter(logging.Filter):
    def __init__(self, param_prefix):
        self._param_prefix = param_prefix

    def is_interesting_frame(self, frame):
        raise NotImplementedError

    def enabled_for_record(self, record):
        return True

    def _findCaller(self):
        """
        Cut down copy of Python 3.6.6's logging.Logger.findCaller()

        Find the stack frame of the caller so that we can note the source
        file name, line number and function name.
        """
        f = logging.currentframe()
        if f is not None:
            f = f.f_back
        while hasattr(f, "f_code"):
            co = f.f_code
            try:
                # do this in a try block to protect ourselves from faulty is_interesting_frame implementations
                is_interesting_frame = self.is_interesting_frame(f)
            except:  # noqa
                is_interesting_frame = False
            if is_interesting_frame:
                return co.co_filename, f.f_lineno, co.co_name
            f = f.f_back
        return None, None, None

    def filter(self, record):
        if not self.enabled_for_record(record):
            return record

        rv = self._findCaller()

        if rv != (None, None, None,):
            for attr_name, attr_value in zip(("pathname", "lineno", "funcName",), rv):
                setattr(record, self._param_prefix + attr_name, attr_value)

        return record


class AppStackLocationFilter(BaseExtraStackLocationFilter):
    """
        Filter which includes extra information on the first stack frame
        that is from a module *within* the "app", based on the code location's
        filename and a provided base file_path_prefix for the "app"
    """
    def __init__(self, param_prefix, file_path_prefix):
        self._file_path_prefix = os.path.normcase(file_path_prefix)
        super().__init__(param_prefix)

    def is_interesting_frame(self, frame):
        filename = os.path.normcase(frame.f_code.co_filename)
        return os.path.commonpath(
            # regarding abspath here: there is a possibility due to https://bugs.python.org/issue20443 that absolutizing
            # these file paths won't work correctly if our python process has done a chdir. I don't think we generally
            # do that but a better solution might be to outlaw relative imports.
            (os.path.abspath(self._file_path_prefix), os.path.abspath(filename))
        ) == self._file_path_prefix

    def enabled_for_record(self, record):
        return record.levelno >= logging.WARNING or (has_request_context() and getattr(request, "is_sampled", False))


class RequestExtraContextFilter(logging.Filter):
    """
        Filter which will pull extra context from the current request's `get_extra_log_context` method (if present)
        and make this available on log records
    """
    def filter(self, record):
        if has_request_context() and callable(getattr(request, "get_extra_log_context", None)):
            for key, value in request.get_extra_log_context().items():
                setattr(record, key, value)

        return record


class CustomLogFormatter(logging.Formatter):
    """Accepts a format string for the message and formats it with the extra fields"""

    FORMAT_STRING_FIELDS_PATTERN = re.compile(r'\((.+?)\)')

    def add_fields(self, record):
        """Ensure all values found in our `fmt` have non-None entries in `record`"""
        for field in self.FORMAT_STRING_FIELDS_PATTERN.findall(self._fmt):
            # slightly clunky - this is so we catch explicitly-set Nones too and turn them into "-"
            fetched_value = record.__dict__.get(field)
            record.__dict__[field] = fetched_value if fetched_value is not None else "-"

    def format(self, record):
        self.add_fields(record)
        msg = super(CustomLogFormatter, self).format(record)

        try:
            msg = msg.format(**record.__dict__)
        except:  # noqa
            # We know that KeyError, ValueError and IndexError are all possible things that can go
            # wrong here - there is no guarantee that the message passed into the logger is
            # actually suitable to be used as a format string. This is particularly so where an
            # we are logging arbitrary exception that may reference code.
            #
            # We catch all exceptions rather than just those three, because _any_ failure to format the
            # message must not result in an error, otherwise the original log message will never be
            # returned and written to the logs, and that might be important info such as an
            # exception.
            #
            # NB do not attempt to log either the exception or `msg` here, or you will
            # find that too fails and you end up with an infinite recursion / stack overflow.
            logger.info("failed to format log message")
        return msg


class JSONFormatter(BaseJSONFormatter):
    def __init__(self, *args, max_missing_key_attempts=5, **kwargs):
        super().__init__(*args, **kwargs)
        self._max_missing_key_attempts = max_missing_key_attempts

    def process_log_record(self, log_record):
        for key, newkey in (
            ("asctime", "time",),
            ("trace_id", "requestId",),
            ("span_id", "spanId",),
            ("parent_span_id", "parentSpanId",),
            ("app_name", "application",),
            ("is_sampled", "isSampled",),
            ("debug_flag", "debugFlag",),
        ):
            try:
                log_record[newkey] = log_record.pop(key)
            except KeyError:
                pass

        log_record['logType'] = "application"

        missing_keys = {}
        for attempt in range(self._max_missing_key_attempts):
            try:
                log_record['message'] = log_record['message'].format(**log_record, **missing_keys)
            except KeyError as e:
                missing_keys[e.args[0]] = f"{{{e.args[0]}: missing key}}"
            else:
                # execution should only ever reach this point once - when the .format() succeeds
                if missing_keys:
                    logger.warning("Missing keys when formatting log message: {}".format(tuple(missing_keys.keys())))

                break

        else:
            logger.exception("Too many missing keys when attempting to format log message: gave up")

        return log_record
