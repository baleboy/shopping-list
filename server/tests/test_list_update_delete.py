from app.services.list_service import update_list, delete_list, get_list


def test_update_list(tmp_data_dir):
    (tmp_data_dir / "lists" / "weekly.md").write_text("- milk\n")
    update_list("weekly", ["eggs", "bread", "butter"])
    assert get_list("weekly") == ["eggs", "bread", "butter"]


def test_update_list_writes_markdown(tmp_data_dir):
    (tmp_data_dir / "lists" / "weekly.md").write_text("")
    update_list("weekly", ["eggs", "bread"])
    content = (tmp_data_dir / "lists" / "weekly.md").read_text()
    assert content == "- eggs\n- bread\n"


def test_update_list_not_found(tmp_data_dir):
    result = update_list("nonexistent", ["eggs"])
    assert result is None


def test_delete_list(tmp_data_dir):
    (tmp_data_dir / "lists" / "weekly.md").write_text("- milk\n")
    assert delete_list("weekly") is True
    assert get_list("weekly") is None


def test_delete_list_not_found(tmp_data_dir):
    assert delete_list("nonexistent") is False


def test_delete_list_removes_cache(tmp_data_dir):
    (tmp_data_dir / "lists" / "weekly.md").write_text("- milk\n")
    cache_dir = tmp_data_dir / "cache"
    cache_dir.mkdir()
    (cache_dir / "weekly_test-shop.json").write_text("{}")
    delete_list("weekly")
    assert not (cache_dir / "weekly_test-shop.json").exists()
