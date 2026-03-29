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


def test_create_shop(client):
    response = client.post("/shops", json={"name": "New Shop"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Shop"
    assert data["id"] == "new-shop"
    assert len(data["sections"]) > 0


def test_update_shop(client, tmp_data_dir):
    client.post("/shops", json={"name": "Test Shop"})
    response = client.put("/shops/test-shop", json={
        "name": "Renamed",
        "sections": ["frozen", "dairy"]
    })
    assert response.status_code == 200
    assert response.json()["name"] == "Renamed"
    assert response.json()["sections"] == ["frozen", "dairy"]


def test_update_shop_not_found(client):
    response = client.put("/shops/nonexistent", json={
        "name": "X",
        "sections": ["a"]
    })
    assert response.status_code == 404


def test_delete_shop(client):
    client.post("/shops", json={"name": "To Delete"})
    response = client.delete("/shops/to-delete")
    assert response.status_code == 200
    response = client.get("/shops/to-delete")
    assert response.status_code == 404


def test_delete_shop_not_found(client):
    response = client.delete("/shops/nonexistent")
    assert response.status_code == 404
