import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.config import settings
from app.main import app


@pytest.fixture
def tmp_data_dir(tmp_path):
    lists_dir = tmp_path / "lists"
    lists_dir.mkdir()
    shops_dir = tmp_path / "shops"
    shops_dir.mkdir()
    original = settings.data_dir
    settings.data_dir = tmp_path
    yield tmp_path
    settings.data_dir = original


@pytest.fixture
def client(tmp_data_dir):
    settings.api_key = ""
    return TestClient(app)
