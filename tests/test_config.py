import pytest
from dmutils.config import init_app


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


def test_init_app_fails_if_boolean_field_is_not_truthy(app, os_environ):
    with app.app_context():
        app.config['MY_SETTING'] = True
        os_environ.update({'MY_SETTING': 'not truthy'})

        with pytest.raises(ValueError):
            init_app(app)


def test_init_app_converts_inty_to_integers(app, os_environ):
    with app.app_context():
        app.config['MY_SETTING'] = 123
        os_environ.update({'MY_SETTING': "312"})

        init_app(app)

        assert app.config['MY_SETTING'] == 312


def test_init_app_fails_if_integer_field_is_not_inty(app, os_environ):
    with app.app_context():
        app.config['MY_SETTING'] = 123
        os_environ.update({'MY_SETTING': 'not-numeric'})

        with pytest.raises(ValueError):
            init_app(app)
