import tempfile

import pytest
from flask import Flask
import mock
from boto.ec2.cloudwatch import CloudWatchConnection

from dmutils.logging import init_app


@pytest.fixture
def app():
    return Flask(__name__)


@pytest.yield_fixture
def app_with_logging(app):
    with tempfile.NamedTemporaryFile() as f:
        app.config['DM_LOG_PATH'] = f.name
        init_app(app)
        yield app


@pytest.yield_fixture
def cloudwatch():
    with mock.patch('dmutils.metrics.connect_to_region') as connect_to_region:
        conn = mock.Mock(spec=CloudWatchConnection)
        connect_to_region.return_value = conn
        yield conn


@pytest.fixture
def os_environ(request):
    env_patch = mock.patch('os.environ', {})
    request.addfinalizer(env_patch.stop)

    return env_patch.start()


@pytest.fixture
def user_json():
    return {
        "users": {
            "id": 123,
            "emailAddress": "test@example.com",
            "name": "name",
            "role": "supplier",
            "locked": False,
            "active": True,
            "supplier": {
                "supplierId": 321,
                "name": "test supplier",
            }
        }
    }
