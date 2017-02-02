import time

import mock

from dmutils import metrics
from helpers import IsDatetime


@mock.patch('dmutils.metrics.connect_to_region')
def test_client_connects_to_region(connect_to_region):
    connect_to_region.return_value = "myconn"
    metrics.client("myregion", "mynamespace")

    connect_to_region.assert_called_with("myregion")


def test_client_default_dimensions_defaults_to_dict(cloudwatch):
    client = metrics.client("myregion", "mynamespace")

    assert client.default_dimensions == dict()


def test_put_metric(cloudwatch):
    client = metrics.client("myregion", "mynamespace")
    client._put_metric("foo", 1, unit="Count")

    cloudwatch.put_metric_data.assert_called_with(
        namespace="mynamespace",
        name="foo",
        value=1,
        timestamp=IsDatetime(),
        unit="Count",
        dimensions=dict(),
        statistics=None)


def test_timer(cloudwatch):
    client = metrics.client("myregion", "mynamespace")
    with client.timer("mytimer"):
        time.sleep(0.1)

    cloudwatch.put_metric_data.assert_called()
    args, kwargs = cloudwatch.put_metric_data.call_args

    assert 0 < kwargs['value'] < 150
    assert kwargs['unit'] == "Milliseconds"


def test_flask_client_returns_none_before_init():
    client = metrics.flask_client()

    assert client.client is None


def test_flask_client_returns_none_when_not_in_app_context(app, cloudwatch):
    client = metrics.flask_client()
    client.init_app(app)

    assert client.client is None


def test_flask_client_returns_client_when_in_app_context(app, cloudwatch):
    client = metrics.flask_client()
    client.init_app(app)

    with app.app_context():
        assert isinstance(client.client, metrics.CloudWatchClient)


def test_flask_client_adds_application_name_dimension(app, cloudwatch):
    client = metrics.flask_client()
    client.init_app(app)

    assert app.config['DM_METRICS_DIMENSIONS'] == {'applicationName': 'none'}


def test_flask_client_merges_configured_dimensions(app, cloudwatch):
    client = metrics.flask_client()
    app.config['DM_METRICS_DIMENSIONS'] = {
        "customDimension": "value",
    }
    client.init_app(app)

    assert app.config['DM_METRICS_DIMENSIONS'] == {
        "applicationName": "none",
        "customDimension": "value",
    }
