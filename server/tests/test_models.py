from app.models import ShopProfile, ShoppingItem, CategorizedSection, CategorizedList


def test_shop_profile():
    shop = ShopProfile(id="lidl", name="Lidl Main Street", sections=["produce", "dairy"])
    assert shop.id == "lidl"
    assert shop.sections == ["produce", "dairy"]


def test_shopping_item_defaults_unchecked():
    item = ShoppingItem(name="milk")
    assert item.checked is False


def test_categorized_list_structure():
    lst = CategorizedList(
        list_name="weekly",
        shop="lidl",
        sections=[
            CategorizedSection(
                name="dairy",
                items=[ShoppingItem(name="milk")]
            )
        ]
    )
    assert lst.sections[0].items[0].name == "milk"
    assert lst.sections[0].items[0].checked is False
