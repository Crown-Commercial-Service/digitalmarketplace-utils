import mock
import pytest

from flask import Flask
from io import StringIO
from logging import Logger, StreamHandler

from boto.ec2.cloudwatch import CloudWatchConnection

from dmutils.logging import init_app as logging_init_app


def create_app(request):
    app = Flask(__name__)
    app.root_path = request.fspath.dirname
    logging_init_app(app)
    app.config['SECRET_KEY'] = 'secret_key'
    return app


@pytest.fixture
def app(request):
    return create_app(request)


@pytest.fixture
def app_with_stream_logger(request):
    """Force StreamHandler to use our StringIO object.

    In the dmutils.logging.get_handler method we default to StreamHandler(sys.stdout), if we override sys.stdout to our
    stream it is possible to check the contents of the stream for the correct log entries.
    """
    stream = StringIO()
    with mock.patch('dmutils.logging.logging.StreamHandler', return_value=StreamHandler(stream)):
        # Use the above app fixture method to return the app and return our stream
        yield create_app(request), stream


@pytest.fixture
def app_with_mocked_logger(request):
    """Patch `create_logger` to return a mock logger that is made accessible on `app.logger`
    """
    with mock.patch('flask.app.create_logger', return_value=mock.Mock(spec=Logger('flask.app'), handlers=[])):
        # Use the above app fixture method to return the app
        yield create_app(request)


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
