import mock

from dmutils import metrics
from .helpers import IsDatetime


@mock.patch('dmutils.metrics.connect_to_region')
def test_client_connects_to_region(connect_to_region):
    connect_to_region.return_value = "myconn"
    metrics.client("myregion", "mynamespace")

    connect_to_region.assert_called_with("myregion")


def test_client_default_dimensions_defaults_to_dict(cloudwatch):
    client = metrics.client("myregion", "mynamespace")

    assert client.default_dimensions == dict()


def test_inc_produces_a_counter(cloudwatch):
    client = metrics.client("myregion", "mynamespace")
    client.inc("foo")

    cloudwatch.put_metric_data.assert_called_with(
        namespace="mynamespace",
        name="foo",
        value=1,
        timestamp=IsDatetime(),
        unit="Count",
        dimensions=dict(),
        statistics=None)
