from flask.signals import got_request_exception, request_finished

from gds_metrics import GDSMetrics


class DMGDSMetrics(GDSMetrics):
    """Custom metrics class to prevent metrics endpoint being bound to base application object.

    The config setup on the base application object enforces `require_login` on views there. We don't want this on
    the metrics endpoint.

    This class removes the `app.add_url_rule` call found in the original `init_app`:
    github.com/alphagov/gds_metrics_python/blob/a724653fd7970c47265f6d483541af590deac99b/gds_metrics/__init__.py#L33

    We should then call `add_url_rule` on our metrics blueprint instead (see github.com/alphagov/digitalmarketplace-brief-responses-frontend/blob/a0e89b3c84d6c49393b2264e6b4ca6508e7286d9/app/metrics/__init__.py#L31). # NOQA
    This binds our initialised metrics object's endpoint to the blueprint rather than the base application object.
    """

    def init_app(self, app):
        app.before_request(self.before_request)
        request_finished.connect(self.teardown_request, sender=app)
        got_request_exception.connect(self.handle_exception, sender=app)
