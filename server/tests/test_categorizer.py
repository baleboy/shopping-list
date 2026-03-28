import json
from unittest.mock import patch, MagicMock
from app.services.categorizer import categorize_items, get_or_create_categorized_list
from app.models import ShopProfile


def test_categorize_items_calls_llm():
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = json.dumps({
        "milk": "dairy",
        "bananas": "produce"
    })

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("app.services.categorizer._get_client", return_value=mock_client):
        result = categorize_items(
            items=["milk", "bananas"],
            sections=["produce", "dairy", "bakery"]
        )

    assert result == {"milk": "dairy", "bananas": "produce"}
    mock_client.messages.create.assert_called_once()


def test_get_or_create_categorized_list_caches(tmp_data_dir):
    shop = ShopProfile(id="test-shop", name="Test", sections=["produce", "dairy"])
    (tmp_data_dir / "lists" / "weekly.md").write_text("- milk\n- bananas\n")

    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = json.dumps({
        "milk": "dairy",
        "bananas": "produce"
    })
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("app.services.categorizer._get_client", return_value=mock_client):
        result1 = get_or_create_categorized_list("weekly", shop)
        result2 = get_or_create_categorized_list("weekly", shop)

    # LLM called only once — second call uses cache
    assert mock_client.messages.create.call_count == 1
    assert result1.list_name == "weekly"
    assert result1.shop == "test-shop"
    assert len(result1.sections) == 2


def test_get_or_create_categorized_list_structure(tmp_data_dir):
    shop = ShopProfile(id="test-shop", name="Test", sections=["produce", "dairy"])
    (tmp_data_dir / "lists" / "weekly.md").write_text("- milk\n- bananas\n")

    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = json.dumps({
        "milk": "dairy",
        "bananas": "produce"
    })
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("app.services.categorizer._get_client", return_value=mock_client):
        result = get_or_create_categorized_list("weekly", shop)

    section_names = [s.name for s in result.sections]
    assert "produce" in section_names
    assert "dairy" in section_names
    dairy = next(s for s in result.sections if s.name == "dairy")
    assert dairy.items[0].name == "milk"
