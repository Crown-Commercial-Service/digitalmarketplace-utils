import uuid
from itertools import chain

from flask import request, current_app


class RequestIdRequestMixin(object):
    @property
    def request_id(self):
        return self.trace_id

    @property
    def trace_id(self):
        if not hasattr(self, "_trace_id"):
            self._trace_id = self._get_first_header(current_app.config['DM_TRACE_ID_HEADERS']) or str(uuid.uuid4())
        return self._trace_id

    @property
    def span_id(self):
        if not hasattr(self, "_span_id"):
            self._span_id = self._get_first_header(current_app.config['DM_SPAN_ID_HEADERS'])
        return self._span_id

    @property
    def parent_span_id(self):
        if not hasattr(self, "_parent_span_id"):
            self._parent_span_id = self._get_first_header(current_app.config['DM_PARENT_SPAN_ID_HEADERS'])
        return self._parent_span_id

    def _get_first_header(self, header_names):
        """
        Returns value of request's first present (and Truthy) header from header_names
        """
        for header_name in header_names:
            if header_name in self.headers and self.headers[header_name]:
                return self.headers[header_name]
        else:
            return None

    def get_onwards_request_headers(self):
        """
            Headers to add to any further (internal) http api requests we perform if we want that request to be
            considered part of this "trace id"
        """
        return dict(chain(
            (
                (header_name, self.trace_id)
                for header_name in current_app.config['DM_TRACE_ID_HEADERS']
                if self.trace_id
            ),
            (
                (header_name, self.span_id)
                for header_name in current_app.config['DM_SPAN_ID_HEADERS']
                if self.span_id
            ),
        ))


class ResponseHeaderMiddleware(object):
    def __init__(self, app, trace_id_headers):
        self.app = app
        self.trace_id_headers = trace_id_headers

    def __call__(self, environ, start_response):
        def rewrite_response_headers(status, headers, exc_info=None):
            headers = headers + [
                (header_name, str(request.request_id),)
                for header_name in self.trace_id_headers
                if header_name not in dict(headers)
            ]

            return start_response(status, headers, exc_info)

        return self.app(environ, rewrite_response_headers)


def init_app(app):
    app.config.setdefault("DM_TRACE_ID_HEADERS", (
        (app.config.get("DM_REQUEST_ID_HEADER") or "DM-Request-ID"),
        (app.config.get("DM_DOWNSTREAM_REQUEST_ID_HEADER") or "X-B3-TraceId"),
    ))
    app.config.setdefault("DM_SPAN_ID_HEADERS", ("X-B3-SpanId",))
    app.config.setdefault("DM_PARENT_SPAN_ID_HEADERS", ("X-B3-ParentSpan",))

    # dynamically define this class as we don't necessarily know how request_class may have already been modified by
    # another init_app
    class _RequestIdRequest(RequestIdRequestMixin, app.request_class):
        pass
    app.request_class = _RequestIdRequest
    app.wsgi_app = ResponseHeaderMiddleware(app.wsgi_app, app.config['DM_TRACE_ID_HEADERS'])
