from collections import OrderedDict
import os
from types import MappingProxyType

from dmutils import config, logging, proxy_fix, request_id, formats, filters, cookie_probe
from dmutils.errors import api as api_errors, frontend as fe_errors
from dmutils.urls import SafePurePathConverter
import dmutils.session
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import default_exceptions


frontend_error_handlers = MappingProxyType(OrderedDict((
    (CSRFError, fe_errors.csrf_handler,),
    (400, fe_errors.render_error_page,),
    (401, fe_errors.redirect_to_login,),
    (403, fe_errors.redirect_to_login,),
    (404, fe_errors.render_error_page,),
    (410, fe_errors.render_error_page,),
    (503, fe_errors.render_error_page,),
    (500, fe_errors.render_error_page,),
)))


api_error_handlers = MappingProxyType(OrderedDict(
    (
        (api_errors.ValidationError, api_errors.validation_error_handler,),
    ) + tuple(
        (code, api_errors.json_error_handler) for code in default_exceptions
    ),
))


def init_app(
        application,
        config_object,
        bootstrap=None,
        data_api_client=None,
        db=None,
        login_manager=None,
        search_api_client=None,
        error_handlers=frontend_error_handlers,
):

    application.config.from_object(config_object)
    if hasattr(config_object, 'init_app'):
        config_object.init_app(application)

    application.config.from_object(__name__)

    # all belong to dmutils
    config.init_app(application)
    logging.init_app(application)
    proxy_fix.init_app(application)
    request_id.init_app(application)
    cookie_probe.init_app(application)

    if bootstrap:
        bootstrap.init_app(application)
    if data_api_client:
        data_api_client.init_app(application)
    if db:
        db.init_app(application)
    if login_manager:
        login_manager.init_app(application)
        dmutils.session.init_app(application)
    if search_api_client:
        search_api_client.init_app(application)

    # allow us to use <safepurepath:...> components in route patterns
    application.url_map.converters["safepurepath"] = SafePurePathConverter

    @application.after_request
    def add_header(response):
        # Block sites from rendering our views inside <iframe>, <embed>, etc by default.
        # Individual views may set their own value (e.g. 'SAMEORIGIN')
        if not response.headers.get('X-Frame-Options'):
            response.headers.setdefault('X-Frame-Options', 'DENY')
        return response

    # Make filters accessible in templates.
    application.add_template_filter(filters.capitalize_first)
    application.add_template_filter(filters.format_links)
    application.add_template_filter(filters.nbsp)
    application.add_template_filter(filters.smartjoin)
    application.add_template_filter(filters.preserve_line_breaks)
    application.add_template_filter(filters.sub_country_codes)
    # Make select formats available in templates.
    application.add_template_filter(formats.dateformat)
    application.add_template_filter(formats.datetimeformat)
    application.add_template_filter(formats.datetodatetimeformat)
    application.add_template_filter(formats.displaytimeformat)
    application.add_template_filter(formats.shortdateformat)
    application.add_template_filter(formats.timeformat)
    application.add_template_filter(formats.utcdatetimeformat)
    application.add_template_filter(formats.utctoshorttimelongdateformat)

    @application.context_processor
    def inject_global_template_variables():
        return dict(
            pluralize=pluralize,
            **(application.config['BASE_TEMPLATE_DATA'] or {}))

    for exc_or_code, handler in error_handlers.items():
        application.register_error_handler(exc_or_code, handler)


def pluralize(count, singular, plural):
    return singular if count == 1 else plural


def get_extra_files(paths):
    for path in paths:
        for dirname, dirs, files in os.walk(path):
            for filename in files:
                filename = os.path.join(dirname, filename)
                if os.path.isfile(filename):
                    yield filename
