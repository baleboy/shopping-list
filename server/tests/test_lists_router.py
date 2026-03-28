import json
from unittest.mock import patch, MagicMock
import yaml


def test_get_lists_empty(client):
    response = client.get("/lists")
    assert response.status_code == 200
    assert response.json() == []


def test_get_lists(client, tmp_data_dir):
    (tmp_data_dir / "lists" / "master.md").write_text("- milk\n")
    response = client.get("/lists")
    assert response.status_code == 200
    assert "master" in response.json()


def test_get_list_by_name(client, tmp_data_dir):
    (tmp_data_dir / "lists" / "weekly.md").write_text("- milk\n- bread\n")
    response = client.get("/lists/weekly")
    assert response.status_code == 200
    assert response.json() == {"name": "weekly", "items": ["milk", "bread"]}


def test_get_list_not_found(client):
    response = client.get("/lists/nonexistent")
    assert response.status_code == 404


def test_create_list_empty(client, tmp_data_dir):
    response = client.post("/lists", json={"name": "tuesday"})
    assert response.status_code == 201
    assert response.json() == {"name": "tuesday", "items": []}


def test_create_list_from_master(client, tmp_data_dir):
    (tmp_data_dir / "lists" / "master.md").write_text("- milk\n- bread\n")
    response = client.post("/lists?from=master", json={"name": "monday"})
    assert response.status_code == 201
    assert response.json()["items"] == ["milk", "bread"]


def test_prepare_list(client, tmp_data_dir):
    (tmp_data_dir / "lists" / "weekly.md").write_text("- milk\n- bananas\n")
    shop_data = {"name": "Test Shop", "sections": ["produce", "dairy"]}
    (tmp_data_dir / "shops" / "test-shop.yaml").write_text(yaml.dump(shop_data))

    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = json.dumps({
        "milk": "dairy",
        "bananas": "produce"
    })
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("app.services.categorizer._get_client", return_value=mock_client):
        response = client.post("/lists/weekly/prepare?shop=test-shop")

    assert response.status_code == 200
    data = response.json()
    assert data["list_name"] == "weekly"
    assert data["shop"] == "test-shop"


def test_toggle_item(client, tmp_data_dir):
    (tmp_data_dir / "lists" / "weekly.md").write_text("- milk\n- bananas\n")
    shop_data = {"name": "Test Shop", "sections": ["produce", "dairy"]}
    (tmp_data_dir / "shops" / "test-shop.yaml").write_text(yaml.dump(shop_data))

    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = json.dumps({
        "milk": "dairy",
        "bananas": "produce"
    })
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("app.services.categorizer._get_client", return_value=mock_client):
        client.post("/lists/weekly/prepare?shop=test-shop")

    response = client.patch("/lists/weekly/items/milk?shop=test-shop")
    assert response.status_code == 200
    assert response.json()["checked"] is True

    response = client.patch("/lists/weekly/items/milk?shop=test-shop")
    assert response.status_code == 200
    assert response.json()["checked"] is False
