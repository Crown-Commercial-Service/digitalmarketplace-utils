import copy
from datetime import datetime

from boto.ec2.cloudwatch import connect_to_region


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
            timestamp = datetime.now()
        self._conn.put_metric_data(
            namespace=self.namespace,
            name=name,
            value=value,
            timestamp=timestamp,
            unit=unit,
            dimensions=self.dimensions(dimensions),
            statistics=statistics)

    def inc(self, name, value=1, timestamp=None, dimensions=None):
        self._put_metric(name,
                         value=value,
                         timestamp=timestamp,
                         unit="Count",
                         dimensions=dimensions)
