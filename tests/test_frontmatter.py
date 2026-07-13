"""Tests for csklint.frontmatter."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

import pytest
from pydantic import ValidationError

from csklint.frontmatter import FrontmatterError
from csklint.frontmatter import SkillFrontmatter
from csklint.frontmatter import SkillMarkdownFile
from csklint.frontmatter import SkillsDirectoryLinter

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

VALID_FULL_FRONTMATTER: dict[str, Any] = {
    "name": "kitchen-sink",
    "description": "Exercise every statically-checkable field.",
    "when_to_use": "Only in tests.",
    "argument-hint": "[filename] [format]",
    "arguments": ["filename", "format"],
    "disable-model-invocation": True,
    "user-invocable": False,
    "allowed-tools": ["Read", "Grep"],
    "disallowed-tools": "Bash",
    "model": "inherit",
    "effort": "xhigh",
    "context": "fork",
    "agent": "general-purpose",
    "hooks": {"PostToolUse": []},
    "paths": "docs/, src/",
    "shell": "powershell",
}

VALID_SKILL_MD = "---\nname: sample\ndescription: A sample skill.\neffort: high\n---\n\n# Sample\n"


class TestSkillFrontmatter:
    """Tests for the SkillFrontmatter schema."""

    def test_model_validate_full_valid(self) -> None:
        frontmatter = SkillFrontmatter.model_validate(VALID_FULL_FRONTMATTER)
        assert frontmatter.effort == "xhigh"
        assert frontmatter.disable_model_invocation is True
        assert frontmatter.allowed_tools == ["Read", "Grep"]

    def test_model_validate_defaults(self) -> None:
        frontmatter = SkillFrontmatter.model_validate({})
        assert frontmatter.name is None
        assert frontmatter.disable_model_invocation is False
        assert frontmatter.user_invocable is True

    def test_model_validate_allows_unknown_fields(self) -> None:
        """Mirror skill-validator's --allow-extra-frontmatter flag: unknown keys must not fail validation."""
        SkillFrontmatter.model_validate({"description": "x", "totally-unknown-field": 42})

    @pytest.mark.parametrize(
        "frontmatter",
        [
            {"effort": "extreme"},
            {"shell": "zsh"},
            {"context": "spoon"},
            {"disable-model-invocation": "maybe"},
            {"user-invocable": 3},
            {"description": ["not", "a", "string"]},
            {"name": {"nested": "mapping"}},
            {"argument-hint": 7},
            {"paths": 5},
            {"hooks": "not-a-mapping"},
        ],
    )
    def test_model_validate_rejects_invalid(self, frontmatter: dict[str, Any]) -> None:
        """Assert each malformed field value raises ValidationError."""
        with pytest.raises(ValidationError):
            SkillFrontmatter.model_validate(frontmatter)


class TestSkillMarkdownFile:
    """Tests for SkillMarkdownFile frontmatter extraction and validation."""

    def test_has_frontmatter_true(self, write_skill_md: Callable[[str, str], Path]) -> None:
        skill_md = write_skill_md("sample", VALID_SKILL_MD)
        assert SkillMarkdownFile(skill_md).has_frontmatter() is True

    def test_has_frontmatter_false_without_block(self, write_skill_md: Callable[[str, str], Path]) -> None:
        skill_md = write_skill_md("sample", "# Sample\n\nNo frontmatter here.\n")
        assert SkillMarkdownFile(skill_md).has_frontmatter() is False

    def test_has_frontmatter_false_for_empty_file(self, write_skill_md: Callable[[str, str], Path]) -> None:
        skill_md = write_skill_md("sample", "")
        assert SkillMarkdownFile(skill_md).has_frontmatter() is False

    def test_validate_frontmatter_valid(self, write_skill_md: Callable[[str, str], Path]) -> None:
        skill_md = write_skill_md("sample", VALID_SKILL_MD)
        frontmatter = SkillMarkdownFile(skill_md).validate_frontmatter()
        assert frontmatter.name == "sample"
        assert frontmatter.effort == "high"

    def test_validate_frontmatter_empty_block(self, write_skill_md: Callable[[str, str], Path]) -> None:
        """Validate an empty frontmatter block as all-defaults instead of failing."""
        skill_md = write_skill_md("sample", "---\n---\n\n# Sample\n")
        frontmatter = SkillMarkdownFile(skill_md).validate_frontmatter()
        assert frontmatter.name is None

    def test_validate_frontmatter_unclosed_block(self, write_skill_md: Callable[[str, str], Path]) -> None:
        skill_md = write_skill_md("sample", "---\nname: sample\n\n# Sample\n")
        with pytest.raises(FrontmatterError, match="never closed"):
            SkillMarkdownFile(skill_md).validate_frontmatter()

    def test_validate_frontmatter_invalid_yaml(self, write_skill_md: Callable[[str, str], Path]) -> None:
        skill_md = write_skill_md("sample", "---\nname: [unclosed\n---\n\n# Sample\n")
        with pytest.raises(FrontmatterError, match="not valid YAML"):
            SkillMarkdownFile(skill_md).validate_frontmatter()

    def test_validate_frontmatter_not_mapping(self, write_skill_md: Callable[[str, str], Path]) -> None:
        skill_md = write_skill_md("sample", "---\n- a\n- b\n---\n\n# Sample\n")
        with pytest.raises(FrontmatterError, match="must be a YAML mapping"):
            SkillMarkdownFile(skill_md).validate_frontmatter()

    def test_validate_frontmatter_invalid_field(self, write_skill_md: Callable[[str, str], Path]) -> None:
        skill_md = write_skill_md("sample", "---\nname: sample\neffort: extreme\n---\n\n# Sample\n")
        with pytest.raises(FrontmatterError, match="effort"):
            SkillMarkdownFile(skill_md).validate_frontmatter()


class TestSkillsDirectoryLinter:
    """Tests for SkillsDirectoryLinter.collect_failures()."""

    def test_collect_failures_reports_only_invalid_skills(
        self,
        tmp_path: Path,
        write_skill_md: Callable[[str, str], Path],
    ) -> None:
        """Assert only the frontmatter-invalid skill is reported, by path and offending field."""
        write_skill_md("valid-skill", VALID_SKILL_MD)
        write_skill_md("no-frontmatter-skill", "# Plain\n\nNo frontmatter, skipped silently.\n")
        invalid_md = write_skill_md("invalid-skill", "---\nshell: zsh\n---\n\n# Invalid\n")
        failures = SkillsDirectoryLinter(tmp_path).collect_failures()
        assert len(failures) == 1
        assert str(invalid_md) in failures[0]
        assert "shell" in failures[0]

    def test_collect_failures_empty_for_valid_tree(
        self,
        tmp_path: Path,
        write_skill_md: Callable[[str, str], Path],
    ) -> None:
        write_skill_md("valid-skill", VALID_SKILL_MD)
        assert not SkillsDirectoryLinter(tmp_path).collect_failures()
