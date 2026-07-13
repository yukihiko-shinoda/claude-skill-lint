"""Validate the YAML frontmatter of Claude Code skills against the documented field schema."""

from __future__ import annotations

from typing import TYPE_CHECKING

from csklint.frontmatter import SkillsDirectoryLinter

if TYPE_CHECKING:
    from pathlib import Path


class TestFrontmatter:
    """Validate SKILL.md frontmatter blocks in-process using the bundled Pydantic schema (no external tool)."""

    def test_skills_frontmatter_pass(self, skills_dir: Path) -> None:
        """Assert every existing SKILL.md frontmatter block under the target directory matches the field schema.

        Files without a frontmatter block are skipped: presence/structure checking is skill-validator's job; this
        check adds field-schema validation (types, fixed enums, string-or-list shapes) on top of frontmatter that
        exists.
        """
        failures = SkillsDirectoryLinter(skills_dir).collect_failures()
        report = "\n\n".join(failures)
        assert not failures, f"Frontmatter validation failed for {len(failures)} file(s):\n{report}"
