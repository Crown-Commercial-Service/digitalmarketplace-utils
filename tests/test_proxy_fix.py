from flask import request

from dmutils import proxy_fix


def test_proxy_fix(app):
    app.config['DM_HTTP_PROTO'] = 'foo'
    proxy_fix.init_app(app)

    @app.route("/")
    def foo():
        return request.environ['HTTP_X_FORWARDED_PROTO']

    with app.app_context():
        client = app.test_client()
        response = client.get('/')
        assert response.data.decode('utf-8') == 'foo'
