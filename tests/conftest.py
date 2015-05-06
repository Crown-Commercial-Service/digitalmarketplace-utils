import tempfile

import pytest
from flask import Flask

from dmutils.logging import init_app


@pytest.fixture
def app():
    return Flask(__name__)


@pytest.yield_fixture
def app_with_logging(app):
    with tempfile.NamedTemporaryFile() as f:
        app.config['DM_LOG_PATH'] = f.name
        init_app(app)
        yield app
