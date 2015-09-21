from __future__ import absolute_import
import logging
import uuid
import sys
import re
from itertools import product

from flask import request, current_app
from flask.wrappers import Request
from flask.ctx import has_request_context

from pythonjsonlogger.jsonlogger import JsonFormatter as BaseJSONFormatter

LOG_FORMAT = '%(asctime)s %(app_name)s %(name)s %(levelname)s ' \
             '%(request_id)s "%(message)s" [in %(pathname)s:%(lineno)d]'
TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'

logger = logging.getLogger(__name__)


def init_app(app):
    app.config.setdefault('DM_LOG_LEVEL', 'INFO')
    app.config.setdefault('DM_APP_NAME', 'none')
    app.config.setdefault('DM_LOG_PATH', './log/application.log')
    app.config.setdefault('DM_REQUEST_ID_HEADER', 'DM-Request-ID')
    app.config.setdefault('DM_DOWNSTREAM_REQUEST_ID_HEADER', '')

    app.request_class = CustomRequest

    @app.after_request
    def after_request(response):
        request_id_header = current_app.config['DM_REQUEST_ID_HEADER']
        response.headers[request_id_header] = request.request_id

        current_app.logger.info('%s %s %s',
                                request.method,
                                request.url,
                                response.status_code)
        return response

    logging.getLogger().addHandler(logging.NullHandler())

    del app.logger.handlers[:]

    handlers = get_handlers(app)
    loglevel = logging.getLevelName(app.config['DM_LOG_LEVEL'])
    loggers = [app.logger, logging.getLogger('dmutils')]
    for logger, handler in product(loggers, handlers):
        logger.addHandler(handler)
        logger.setLevel(loglevel)

    app.logger.info("Logging configured")


class CustomRequest(Request):
    _request_id = None

    @property
    def request_id(self):
        if self._request_id is None:
            self._request_id = self._get_request_id(
                current_app.config['DM_REQUEST_ID_HEADER'],
                current_app.config['DM_DOWNSTREAM_REQUEST_ID_HEADER'])
        return self._request_id

    def _get_request_id(self, request_id_header, downstream_header):
        if request_id_header in self.headers:
            return self.headers.get(request_id_header)
        elif downstream_header and downstream_header in self.headers:
            return self.headers.get(downstream_header)
        else:
            return str(uuid.uuid4())


def configure_handler(handler, app, formatter):
    handler.setLevel(logging.getLevelName(app.config['DM_LOG_LEVEL']))
    handler.setFormatter(formatter)
    handler.addFilter(AppNameFilter(app.config['DM_APP_NAME']))
    handler.addFilter(RequestIdFilter())

    return handler


def get_handlers(app):
    handlers = []
    standard_formatter = CustomLogFormatter(LOG_FORMAT, TIME_FORMAT)
    json_formatter = JSONFormatter(LOG_FORMAT, TIME_FORMAT)

    if app.debug:
        handler = logging.StreamHandler(sys.stderr)
        handlers.append(configure_handler(handler, app, standard_formatter))
    else:
        handler = logging.FileHandler(app.config['DM_LOG_PATH'])
        handlers.append(configure_handler(handler, app, standard_formatter))

        handler = logging.FileHandler(app.config['DM_LOG_PATH'] + '.json')
        handlers.append(configure_handler(handler, app, json_formatter))

    return handlers


class AppNameFilter(logging.Filter):
    def __init__(self, app_name):
        self.app_name = app_name

    def filter(self, record):
        record.app_name = self.app_name

        return record


class RequestIdFilter(logging.Filter):
    @property
    def request_id(self):
        if has_request_context() and hasattr(request, 'request_id'):
            return request.request_id
        else:
            return 'no-request-id'

    def filter(self, record):
        record.request_id = self.request_id

        return record


class CustomLogFormatter(logging.Formatter):
    """Accepts a format string for the message and formats it with the extra fields"""

    FORMAT_STRING_FIELDS_PATTERN = re.compile(r'\((.+?)\)', re.IGNORECASE)

    def add_fields(self, record):
        for field in self.FORMAT_STRING_FIELDS_PATTERN.findall(self._fmt):
            record.__dict__[field] = record.__dict__.get(field)
        return record

    def format(self, record):
        record = self.add_fields(record)
        try:
            record.msg = record.msg.format(**record.__dict__)
        except KeyError as e:
            logger.exception("failed to format log message: {} not found".format(e))
        return super(CustomLogFormatter, self).format(record)


class JSONFormatter(BaseJSONFormatter):
    def process_log_record(self, log_record):
        rename_map = {
            "asctime": "time",
            "request_id": "requestId",
            "app_name": "application",
        }
        for key, newkey in rename_map.items():
            log_record[newkey] = log_record.pop(key)
        log_record['logType'] = "application"
        try:
            log_record['message'] = log_record['message'].format(**log_record)
        except KeyError as e:
            logger.exception("failed to format log message: {} not found".format(e))
        return log_record
