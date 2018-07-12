import pytest

from dmutils.external import external


@pytest.mark.parametrize(
    'url', [
        '/suppliers/opportunities',
        '/suppliers/opportunities/1234'
    ]
)
def test_external_routes_raise_404_if_suppliers_given_as_framework_family(app, url):
    app.register_blueprint(external)
    client = app.test_client()
    with app.app_context():
        resp = client.get(url)
        assert resp.status_code == 404


@pytest.mark.parametrize(
    'url', [
        '/digital-outcomes-and-specialists/opportunities',
        '/digital-outcomes-and-specialists/opportunities/1234',
        '/foo/opportunities',
        '/foo/opportunities/1234'
    ]
)
def test_external_routes_raise_500_if_anything_else_given_as_framework_family(app, url):
    app.register_blueprint(external)
    client = app.test_client()
    with app.app_context():
        resp = client.get(url)
        assert resp.status_code == 500
