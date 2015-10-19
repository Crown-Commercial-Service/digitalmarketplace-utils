from flask_featureflags.contrib.inline import InlineFeatureFlag
from . import config, logging, proxy_fix, request_id, formats


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
    request_id.init_app(application)

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

    application.add_template_filter(formats.timeformat)
    application.add_template_filter(formats.shortdateformat)
    application.add_template_filter(formats.dateformat)
    application.add_template_filter(formats.datetimeformat)


def init_manager(application, manager):
    @manager.command
    def list_routes():
        """List URLs of all application routes."""
        for rule in sorted(manager.app.url_map.iter_rules(), key=lambda r: r.rule):
            print("{:10} {}".format(", ".join(rule.methods - set(['OPTIONS', 'HEAD'])), rule.rule))
