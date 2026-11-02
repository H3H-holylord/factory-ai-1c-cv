from pathlib import Path


def test_standalone_github_pages_index_html_is_complete():
    index_path = Path("e:/4/index.html")
    assert index_path.exists()
    content = index_path.read_text(encoding="utf-8")
    assert "ДАШБОРД ПРЕДПРИЯТИЯ" in content
    assert "camConveyor" in content
    assert "camWelding" in content
    assert "Replica1CDatabase" in content or "productionData" in content
