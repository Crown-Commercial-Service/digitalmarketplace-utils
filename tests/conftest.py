import tempfile

import pytest
from flask import Flask
import mock
from boto.ec2.cloudwatch import CloudWatchConnection

from dmutils.logging import init_app


@pytest.fixture
def app():
    app = Flask(__name__)
    init_app(app)
    return app


# it's deceptively difficult to capture & inspect *actual* log output in pytest (no, capfd doesn't seem to work)
@pytest.fixture
def app_logtofile():
    with tempfile.NamedTemporaryFile() as f:
        app = Flask(__name__)
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
            },
            "userResearchOptedIn": True,
        }
    }
