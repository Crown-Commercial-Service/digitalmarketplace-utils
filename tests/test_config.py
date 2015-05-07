from flask import Flask
import pytest
import mock

from dmutils.config import init_app


@pytest.fixture
def app():
    return Flask(__name__)


@pytest.fixture
def os_environ(request):
    env_patch = mock.patch('os.environ', {})
    request.addfinalizer(env_patch.stop)

    return env_patch.start()


def test_init_app_updates_known_config_options(app, os_environ):
    with app.app_context():
        app.config['MY_SETTING'] = 'foo'
        os_environ.update({'MY_SETTING': 'bar'})

        init_app(app)

        assert app.config['MY_SETTING'] == 'bar'


def test_init_app_ignores_unknown_options(app, os_environ):
    with app.app_context():
        os_environ.update({'MY_SETTING': 'bar'})

        init_app(app)

        assert 'MY_SETTING' not in app.config


def test_init_app_converts_truthy_to_bool(app, os_environ):
    with app.app_context():
        app.config['MY_SETTING'] = True
        os_environ.update({'MY_SETTING': 'false'})

        init_app(app)

        assert app.config['MY_SETTING'] is False
