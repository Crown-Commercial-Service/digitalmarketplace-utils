from pathlib import PurePath

from flask import url_for
import pytest

from dmutils.urls import SafePurePathConverter


@pytest.mark.parametrize("route_pattern,request_path", tuple(
    ("/beside/<safepurepath:some_path>/shakespeare", request_path) for request_path in (
        "/beside/../shakespeare",
        "/beside/../saxon/shakespeare",
        "/beside/saxon/../shakespeare",
        "/beside/saxon/../hamlet/shakespeare",
        "/beside/saxon/.../hamlet/shakespeare",
        "/beside/shakespeare",
        "/beside//shakespeare",
        "/beside/./shakespeare",
    )
) + tuple(
    ("/beside/shakespeare/<safepurepath:some_path>", request_path) for request_path in (
        "/beside/shakespeare/hamlet/../saxon.pdf",
        "/beside/shakespeare/../hamlet/bards",
        "/beside/shakespeare/saxon/hamlet/../bards.png",
        "/beside/shakespeare//hamlet/saxon.pdf",
    )
))
def test_safepurepath_undesirable_urls(app, route_pattern, request_path):
    app.url_map.converters["safepurepath"] = SafePurePathConverter

    @app.route(route_pattern)
    def some_view(some_path):
        assert False, f"View body not expected to be executed: {some_path!r}"

    with app.app_context():
        response = app.test_client().get(request_path)
        assert response.status_code == 404


@pytest.mark.parametrize("route_pattern,request_path,expected_arg", tuple(
    ("/beside/<safepurepath:some_path>/shakespeare", request_path, expected_arg) for request_path, expected_arg in (
        ("/beside/..saxon/shakespeare", PurePath('..saxon'),),
        ("/beside/saxon/hamlet123/shakespeare", PurePath('saxon/hamlet123'),),
        ("/beside/saxon/./shakespeare", PurePath('saxon'),),  # note empty part squashed out
        ("/beside/..saxon../hamlet//shakespeare", PurePath('..saxon../hamlet'),),
        ("/beside/hamlet-123/.saxon/shakespeare", PurePath('hamlet-123/.saxon'),),
        ("/beside/shakespeare/shakespeare", PurePath('shakespeare'),),
    )
) + tuple(
    ("/beside/shakespeare/<safepurepath:some_path>", request_path, expected_arg) for request_path, expected_arg in (
        ("/beside/shakespeare/hamlet//saxon.pdf", PurePath('hamlet/saxon.pdf'),),
        ("/beside/shakespeare/..hamlet/bards", PurePath('..hamlet/bards'),),
        ("/beside/shakespeare/hamlet/bard/", PurePath('hamlet/bard'),),
        ("/beside/shakespeare/saxon_/.ham/let/bards...png", PurePath('saxon_/.ham/let/bards...png'),),
    )
))
def test_safepurepath_acceptable_urls(app, route_pattern, request_path, expected_arg):
    app.url_map.converters["safepurepath"] = SafePurePathConverter

    @app.route(route_pattern)
    def some_view(some_path):
        assert some_path == expected_arg
        return "Success", 201

    with app.app_context():
        response = app.test_client().get(request_path)
        assert response.status_code == 201


@pytest.mark.parametrize("arg_value,expected_url", (
    ("hamlet/saxon", "http://eglington/beside/hamlet/saxon/shakespeare",),
    (PurePath("hamlet/saxon"), "http://eglington/beside/hamlet/saxon/shakespeare",),
    # in reality, requesting the following would 404
    (PurePath("."), "http://eglington/beside/./shakespeare",),
    (PurePath("../.."), "http://eglington/beside/../../shakespeare",),
    ("../../", "http://eglington/beside/../..//shakespeare",),
))
def test_safepurepath_url_reversing(app, arg_value, expected_url):
    app.config["SERVER_NAME"] = "eglington"
    app.url_map.converters["safepurepath"] = SafePurePathConverter

    @app.route("/beside/<safepurepath:some_path>/shakespeare")
    def some_view(some_path):
        pass

    with app.app_context():
        assert url_for("some_view", some_path=arg_value) == expected_url
