import flask_session
from flask import Flask
from dmutils import session
import mock


class TestSession:

    def setup(self):
        self.application = Flask("mytestapp")

    @mock.patch("flask_session.Session", autospec=True)
    def test_session_initialises_flask_redis_session(self, _mock_session):
        self.application.config['DM_ENVIRONMENT'] = 'development'
        session.init_app(self.application)
        flask_session.Session.assert_called_once()
        assert type(self.application.config.get('SESSION_REDIS')).__name__ == 'Redis'

    @mock.patch("flask_session.Session", autospec=True)
    def test_session_initialises_flask_redis_session_with_credentials(self, _mock_session):
        self.application.config['DM_REDIS_SERVICE_NAME'] = 'digitalmarketplace_redis'
        self.application.config['VCAP_SERVICES'] = """
    {
        "redis": [{
            "binding_name": null,
            "credentials": {"uri": "redis://username:password@example.com:6379"},
            "instance_name": "digitalmarketplace_redis",
            "label": "splunk",
            "name": "digitalmarketplace_redis",
            "plan": "unlimited",
            "provider": null,
            "tags": [],
            "volume_mounts": []
        }]
    }
            """
        session.init_app(self.application)
        flask_session.Session.assert_called_once()
        expected_dict = {'host': 'example.com', 'port': 6379, 'username': 'username', 'password': 'password', 'db': 0}
        assert self.application.config["SESSION_REDIS"].connection_pool.connection_kwargs == expected_dict
