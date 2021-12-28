# Copyright (c) 2021 Lucia Pisarenco, Berlin, Germany
import os
from app import app
import pytest

@pytest.fixture(name="db")
def fixture_db():
    try:
        app.setup()
        yield
    finally:
        os.unlink(app.DB_LOCATION)
