from app.services.list_service import list_lists, get_list, create_list, parse_items


def test_parse_items_from_markdown():
    md = "# Shopping\n- milk\n- bananas\n- chicken breast\n"
    assert parse_items(md) == ["milk", "bananas", "chicken breast"]


def test_parse_items_ignores_non_list_lines():
    md = "# Title\nSome text\n- item one\n\n- item two\n"
    assert parse_items(md) == ["item one", "item two"]


def test_list_lists_empty(tmp_data_dir):
    assert list_lists() == []


def test_list_lists_finds_md(tmp_data_dir):
    (tmp_data_dir / "lists" / "master.md").write_text("- milk\n")
    (tmp_data_dir / "lists" / "weekly.md").write_text("- bread\n")
    names = list_lists()
    assert "master" in names
    assert "weekly" in names


def test_get_list(tmp_data_dir):
    (tmp_data_dir / "lists" / "master.md").write_text("- milk\n- bread\n")
    items = get_list("master")
    assert items == ["milk", "bread"]


def test_get_list_not_found(tmp_data_dir):
    assert get_list("nonexistent") is None


def test_create_list_from_master(tmp_data_dir):
    (tmp_data_dir / "lists" / "master.md").write_text("- milk\n- bread\n")
    create_list("monday", from_master=True)
    assert get_list("monday") == ["milk", "bread"]


def test_create_list_empty(tmp_data_dir):
    create_list("tuesday", from_master=False)
    content = (tmp_data_dir / "lists" / "tuesday.md").read_text()
    assert content == ""
