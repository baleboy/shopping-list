import yaml
from app.services.shop_service import list_shops, get_shop


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
