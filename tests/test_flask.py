from dmutils.flask import DMGzipMiddleware


class TestDMGzipMiddleware:
    def test_with_compression_safe_header(self, app):
        DMGzipMiddleware(app, compress_by_default=False)

        @app.route('/')
        def some_route():
            return "!" * 9000, 200, {"X-Compression-Safe": "1"}

        response = app.test_client().get('/', headers={"Accept-Encoding": "gzip"})
        assert response.status_code == 200
        assert response.headers["Content-Encoding"] == "gzip"
        assert len(response.get_data()) < 9000
        assert "X-Compression-Safe" not in response.headers

    def test_with_compression_unsafe_header(self, app):
        DMGzipMiddleware(app, compress_by_default=False)

        @app.route('/')
        def some_route():
            return "!" * 9000, 200, {"X-Compression-Safe": "0"}

        response = app.test_client().get('/', headers={"Accept-Encoding": "gzip"})
        assert response.status_code == 200
        assert response.headers.get("Content-Encoding") != "gzip"
        assert len(response.get_data()) == 9000
        assert "X-Compression-Safe" not in response.headers

    def test_with_compression_default_false(self, app):
        DMGzipMiddleware(app)

        @app.route('/')
        def some_route():
            return "!" * 9000, 200

        response = app.test_client().get('/', headers={"Accept-Encoding": "gzip"})
        assert response.status_code == 200
        assert response.headers.get("Content-Encoding") != "gzip"
        assert len(response.get_data()) == 9000
        assert "X-Compression-Safe" not in response.headers

    def test_with_compression_default_true(self, app):
        DMGzipMiddleware(app, compress_by_default=True)

        @app.route('/')
        def some_route():
            return "!" * 9000, 200

        response = app.test_client().get('/', headers={"Accept-Encoding": "gzip"})
        assert response.status_code == 200
        assert response.headers["Content-Encoding"] == "gzip"
        assert len(response.get_data()) < 9000
        assert "X-Compression-Safe" not in response.headers
