import copy
from datetime import datetime

from boto.ec2.cloudwatch import connect_to_region
from flask import current_app, _app_ctx_stack as stack
from contextlib import ContextDecorator
from monotonic import monotonic


def flask_client():
    return CloudWatchFlaskClient()


class CloudWatchFlaskClient(object):
    def init_app(self, app):
        c = app.config
        c.setdefault('DM_METRICS_REGION', 'eu-west-1')
        c.setdefault('DM_METRICS_NAMESPACE', c.get('DM_ENVIRONMENT', 'none'))
        dimensions = {
            "applicationName": c.get('DM_APP_NAME', 'none'),
        }
        dimensions.update(c.get('DM_METRICS_DIMENSIONS', dict()))
        c['DM_METRICS_DIMENSIONS'] = dimensions

    @property
    def client(self):
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'dmutils_metrics_client'):
                ctx.dmutils_metrics_client = client(
                    current_app.config['DM_METRICS_REGION'],
                    current_app.config['DM_METRICS_NAMESPACE'],
                    current_app.config['DM_METRICS_DIMENSIONS'])
            return ctx.dmutils_metrics_client


def client(region, namespace, default_dimensions=None):
    return CloudWatchClient(region, namespace, default_dimensions)


class CloudWatchClient(object):
    def __init__(self, region, namespace, default_dimensions=None):
        self._conn = connect_to_region(region)
        self.namespace = namespace
        if default_dimensions is None:
            default_dimensions = dict()
        self.default_dimensions = default_dimensions

    def dimensions(self, dimensions):
        _dimensions = copy.copy(self.default_dimensions)
        if dimensions is not None:
            _dimensions.update(dimensions)
        return _dimensions

    def _put_metric(self, name, value=None, timestamp=None, unit=None,
                    dimensions=None, statistics=None):
        if timestamp is None:
            timestamp = datetime.utcnow()
        self._conn.put_metric_data(
            namespace=self.namespace,
            name=name,
            value=value,
            timestamp=timestamp,
            unit=unit,
            dimensions=self.dimensions(dimensions),
            statistics=statistics)

    def timer(self, name):
        return Timer(self, name)


class Timer(ContextDecorator):
    def __init__(self, client, name):
        self.client = client
        self.name = name

    def __enter__(self):
        self.start = monotonic()

    def __exit__(self, *exc):
        elapsed = monotonic() - self.start
        self.client._put_metric(
            self.name,
            int(elapsed * 1000),
            unit="Milliseconds")
