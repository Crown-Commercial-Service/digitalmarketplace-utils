from . import logging, config, proxy_fix, formats
from datetime import datetime
import flask_featureflags
from flask_featureflags.contrib.inline import InlineFeatureFlag

__version__ = '3.5.1'


def init_app(
        application,
        config_object,
        bootstrap=None,
        data_api_client=None,
        db=None,
        feature_flags=None,
        login_manager=None,
        search_api_client=None,
):

    application.config.from_object(config_object)
    if hasattr(config_object, 'init_app'):
        config_object.init_app(application)

    # all belong to dmutils
    config.init_app(application)
    logging.init_app(application)
    proxy_fix.init_app(application)

    if bootstrap:
        bootstrap.init_app(application)
    if data_api_client:
        data_api_client.init_app(application)
    if db:
        db.init_app(application)
    if feature_flags:
        # Standardize FeatureFlags, only accept inline config variables
        feature_flags.init_app(application)
        feature_flags.clear_handlers()
        feature_flags.add_handler(InlineFeatureFlag())
    if login_manager:
        login_manager.init_app(application)
    if search_api_client:
        search_api_client.init_app(application)

    @application.after_request
    def add_header(response):
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @application.template_filter('timeformat')
    def timeformat(value):
        if not isinstance(value, datetime):
            value = datetime.strptime(value, formats.DATETIME_FORMAT)
        return value.strftime(formats.DISPLAY_TIME_FORMAT)

    @application.template_filter('dateformat')
    def dateformat(value):
        if not isinstance(value, datetime):
            value = datetime.strptime(value, formats.DATETIME_FORMAT)
        return value.strftime(formats.DISPLAY_DATE_FORMAT)

    @application.template_filter('datetimeformat')
    def datetimeformat(value):
        if not isinstance(value, datetime):
            value = datetime.strptime(value, formats.DATETIME_FORMAT)
        return value.strftime(formats.DISPLAY_DATETIME_FORMAT)
