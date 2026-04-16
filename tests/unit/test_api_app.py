from pathlib import Path

import pytest

from interfaces.api.app import resolve_web_dist, validate_web_dist


def test_resolve_web_dist_returns_absolute_path_for_custom_input(repo_tmp_path: Path) -> None:
    web_dist = repo_tmp_path / "web-dist"
    web_dist.mkdir()

    resolved = resolve_web_dist(web_dist)

    assert resolved == web_dist.resolve()


def test_validate_web_dist_accepts_directory_with_index_html(repo_tmp_path: Path) -> None:
    web_dist = repo_tmp_path / "web-dist"
    web_dist.mkdir()
    (web_dist / "index.html").write_text("<!doctype html><html></html>", encoding="utf-8")

    validated = validate_web_dist(web_dist)

    assert validated == web_dist.resolve()


def test_validate_web_dist_rejects_missing_index_html(repo_tmp_path: Path) -> None:
    web_dist = repo_tmp_path / "web-dist"
    web_dist.mkdir()

    with pytest.raises(ValueError, match="UI build not found"):
        validate_web_dist(web_dist)
