from __future__ import absolute_import
import logging
import uuid
import sys

from flask import request, current_app
from flask.wrappers import Request
from flask.ctx import has_request_context

LOG_FORMAT = '%(asctime)s %(app_name)s %(name)s %(levelname)s ' \
             '%(request_id)s "%(message)s" [in %(pathname)s:%(lineno)d]'
TIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


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
                                request.path,
                                response.status_code)
        return response

    logging.getLogger().addHandler(logging.NullHandler())

    del app.logger.handlers[:]

    handler = get_handler(app)
    loglevel = logging.getLevelName(app.config['DM_LOG_LEVEL'])
    loggers = [app.logger, logging.getLogger('dmutils')]
    for logger in loggers:
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


def configure_handler(handler, app):
    handler.setLevel(logging.getLevelName(app.config['DM_LOG_LEVEL']))
    handler.setFormatter(logging.Formatter(LOG_FORMAT, TIME_FORMAT))
    handler.addFilter(AppNameFilter(app.config['DM_APP_NAME']))
    handler.addFilter(RequestIdFilter())

    return handler


def get_handler(app):
    handler = None
    if app.debug:
        handler = logging.StreamHandler(sys.stderr)
    else:
        handler = logging.FileHandler(app.config['DM_LOG_PATH'])
    return configure_handler(handler, app)


class AppNameFilter(logging.Filter):
    def __init__(self, app_name):
        self.app_name = app_name

    def filter(self, record):
        record.app_name = self.app_name

        return record


class RequestIdFilter(logging.Filter):
    @property
    def request_id(self):
        if not has_request_context():
            return 'no-request-id'
        else:
            return request.request_id

    def filter(self, record):
        record.request_id = self.request_id

        return record
