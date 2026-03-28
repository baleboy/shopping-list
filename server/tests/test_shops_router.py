import yaml


def test_get_shops_empty(client):
    response = client.get("/shops")
    assert response.status_code == 200
    assert response.json() == []


def test_get_shops(client, tmp_data_dir):
    shop_data = {"name": "Test Shop", "sections": ["produce", "dairy"]}
    (tmp_data_dir / "shops" / "test-shop.yaml").write_text(yaml.dump(shop_data))
    response = client.get("/shops")
    assert response.status_code == 200
    shops = response.json()
    assert len(shops) == 1
    assert shops[0]["id"] == "test-shop"


def test_get_shop_by_id(client, tmp_data_dir):
    shop_data = {"name": "Test Shop", "sections": ["produce", "dairy"]}
    (tmp_data_dir / "shops" / "test-shop.yaml").write_text(yaml.dump(shop_data))
    response = client.get("/shops/test-shop")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Shop"


def test_get_shop_not_found(client):
    response = client.get("/shops/nonexistent")
    assert response.status_code == 404
