import json
import yaml
from app.services.shop_service import list_shops, get_shop, create_shop, update_shop, delete_shop


def test_list_shops_empty(tmp_data_dir):
    assert list_shops() == []


def test_list_shops_finds_yaml(tmp_data_dir):
    shop_data = {"name": "Test Shop", "sections": ["produce", "dairy"]}
    (tmp_data_dir / "shops" / "test-shop.yaml").write_text(yaml.dump(shop_data))
    shops = list_shops()
    assert len(shops) == 1
    assert shops[0].id == "test-shop"
    assert shops[0].name == "Test Shop"


def test_get_shop(tmp_data_dir):
    shop_data = {"name": "Test Shop", "sections": ["produce", "dairy"]}
    (tmp_data_dir / "shops" / "test-shop.yaml").write_text(yaml.dump(shop_data))
    shop = get_shop("test-shop")
    assert shop is not None
    assert shop.sections == ["produce", "dairy"]


def test_get_shop_not_found(tmp_data_dir):
    assert get_shop("nonexistent") is None


def test_list_shops_merges_yaml_and_cache(tmp_data_dir):
    shop_data = {"name": "YAML Shop", "sections": ["produce", "dairy"]}
    (tmp_data_dir / "shops" / "yaml-shop.yaml").write_text(yaml.dump(shop_data))
    cache_dir = tmp_data_dir / "cache" / "shops"
    cache_dir.mkdir(parents=True)
    cached = {"id": "cached-shop", "name": "Cached Shop", "sections": ["frozen"]}
    (cache_dir / "cached-shop.json").write_text(json.dumps(cached))
    shops = list_shops()
    names = [s.name for s in shops]
    assert "YAML Shop" in names
    assert "Cached Shop" in names


def test_cached_shop_overrides_yaml(tmp_data_dir):
    shop_data = {"name": "Original", "sections": ["produce"]}
    (tmp_data_dir / "shops" / "my-shop.yaml").write_text(yaml.dump(shop_data))
    cache_dir = tmp_data_dir / "cache" / "shops"
    cache_dir.mkdir(parents=True)
    cached = {"id": "my-shop", "name": "Updated", "sections": ["dairy", "produce"]}
    (cache_dir / "my-shop.json").write_text(json.dumps(cached))
    shop = get_shop("my-shop")
    assert shop.name == "Updated"
    assert shop.sections == ["dairy", "produce"]


def test_create_shop(tmp_data_dir):
    shop = create_shop("My New Shop")
    assert shop.id == "my-new-shop"
    assert shop.name == "My New Shop"
    assert len(shop.sections) > 0
    assert get_shop("my-new-shop") is not None


def test_create_shop_generates_unique_id(tmp_data_dir):
    create_shop("Test Shop")
    shop2 = create_shop("Test Shop")
    assert shop2.id != "test-shop"


def test_update_shop(tmp_data_dir):
    create_shop("Original")
    updated = update_shop("original", name="Renamed", sections=["frozen", "dairy"])
    assert updated.name == "Renamed"
    assert updated.sections == ["frozen", "dairy"]
    fetched = get_shop("original")
    assert fetched.name == "Renamed"


def test_update_shop_not_found(tmp_data_dir):
    result = update_shop("nonexistent", name="X", sections=["a"])
    assert result is None


def test_delete_shop_cached(tmp_data_dir):
    create_shop("To Delete")
    assert delete_shop("to-delete") is True
    assert get_shop("to-delete") is None


def test_delete_shop_yaml(tmp_data_dir):
    shop_data = {"name": "YAML Shop", "sections": ["produce"]}
    (tmp_data_dir / "shops" / "yaml-shop.yaml").write_text(yaml.dump(shop_data))
    assert delete_shop("yaml-shop") is True
    assert get_shop("yaml-shop") is None


def test_delete_shop_not_found(tmp_data_dir):
    assert delete_shop("nonexistent") is False
