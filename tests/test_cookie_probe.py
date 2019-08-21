from werkzeug.http import parse_cookie

from dmutils import cookie_probe


def test_cookie_probe_cookie_present(app):
    cookie_probe.init_app(app)

    @app.route('/')
    def error_route():
        return "<html>Success</html>"

    client = app.test_client()
    assert not client.cookie_jar  # i.e. empty

    response = client.get('/')

    assert response.status_code == 200
    assert any(
        name == app.config["DM_COOKIE_PROBE_COOKIE_NAME"] and value == app.config["DM_COOKIE_PROBE_COOKIE_VALUE"]
        for name, value in (
            tuple(parse_cookie(raw).items())[0] for raw in response.headers.getlist("Set-Cookie")
        )
    )
