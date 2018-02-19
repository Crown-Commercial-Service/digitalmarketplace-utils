import functools
import pytest

from flask import Blueprint
from flask_login import LoginManager

from dmutils.access_control import require_login
from dmutils.user import User
from dmtestutils.login import login_for_tests, USERS


@pytest.fixture
def access_controlled_app(app):
    """
    An app where all the routes are access-controlled to the 'buyer' role, and there are some login routes if we need.
    """
    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        # simulate loading a user from the API
        return User.from_json({"users": USERS[user_id]})

    app.register_blueprint(login_for_tests)
    app.secret_key = 'secret'

    main = Blueprint('main', 'main')

    @main.route('/')
    def simple_route():
        return "Hello"

    main.before_request(functools.partial(require_login, role='buyer'))
    app.register_blueprint(main)

    return app


def test_all_routes_require_login(access_controlled_app):
    """
    Check that routes where we are applying our "require_login" function are actually protected from anonymous access
    - in this case with a 401 rather than a redirect-to-login, because we don't set a login page for our test client.
    """

    client = access_controlled_app.test_client()
    response = client.get('/')
    assert response.status_code == 401


def test_access_deny_for_wrong_role(access_controlled_app):
    client = access_controlled_app.test_client()
    response = client.get("/auto-supplier-login")
    assert response.status_code == 200

    response = client.get('/')
    assert response.status_code == 401


def test_access_allow_for_correct_role(access_controlled_app):
    client = access_controlled_app.test_client()
    response = client.get("/auto-buyer-login")
    assert response.status_code == 200

    response = client.get('/')
    assert response.status_code == 200
