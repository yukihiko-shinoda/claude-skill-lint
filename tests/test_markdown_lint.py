"""Tests for csklint.markdown_lint."""

from __future__ import annotations

from typing import TYPE_CHECKING

from csklint.markdown_lint import MarkdownlintConfigResolver

if TYPE_CHECKING:
    from pathlib import Path


class TestMarkdownlintConfigResolver:
    """Tests for MarkdownlintConfigResolver.resolve()."""

    def test_resolve_finds_config_in_skills_dir(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        config = skills_dir / ".markdownlint-cli2.jsonc"
        config.write_text("{}")
        assert MarkdownlintConfigResolver(skills_dir).resolve() == config

    def test_resolve_prefers_skills_dir_over_parent(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        (tmp_path / ".markdownlint-cli2.jsonc").write_text("{}")
        config = skills_dir / ".markdownlint-cli2.jsonc"
        config.write_text("{}")
        assert MarkdownlintConfigResolver(skills_dir).resolve() == config

    def test_resolve_finds_config_in_parent_when_absent_from_skills_dir(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills" / "hello-world"
        skills_dir.mkdir(parents=True)
        config = tmp_path / "skills" / ".markdownlint-cli2.jsonc"
        config.write_text("{}")
        assert MarkdownlintConfigResolver(skills_dir).resolve() == config

    def test_resolve_returns_none_when_no_config_anywhere(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        assert MarkdownlintConfigResolver(skills_dir).resolve() is None

    def test_resolve_recognizes_yaml_variant(self, tmp_path: Path) -> None:
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        config = skills_dir / ".markdownlint-cli2.yaml"
        config.write_text("")
        assert MarkdownlintConfigResolver(skills_dir).resolve() == config

    def test_resolve_at_filesystem_root_does_not_error(self, tmp_path: Path) -> None:
        """Guard the skills_dir == skills_dir.parent case (e.g. filesystem root) against double-checking."""
        root = tmp_path.parents[-1]
        assert MarkdownlintConfigResolver(root).resolve() is None
