"""Extraction and schema validation of Claude Code SKILL.md frontmatter.

The schema follows the frontmatter reference at https://code.claude.com/docs/en/skills#frontmatter-reference
(fetched 2026-07-13). Only static structural checks are implemented: field types, fixed enums, and
string-or-list shapes. Checks that depend on external or time-varying state — whether ``model`` names a
currently-valid model alias, whether ``agent`` names an existing subagent definition on disk, or the deep
``hooks`` schema — are intentionally out of scope.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import Literal
from typing import Optional
from typing import Union

import yaml
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import ValidationError

if TYPE_CHECKING:
    from pathlib import Path

_DELIMITER = "---"


class FrontmatterError(ValueError):
    """Raised when a SKILL.md frontmatter block is malformed or fails schema validation."""


class SkillFrontmatter(BaseModel):
    """Schema for the YAML frontmatter block of a Claude Code SKILL.md file.

    All fields are optional per the official reference. ``extra="allow"`` mirrors the ``--allow-extra-frontmatter``
    flag the bundled suite already passes to skill-validator: unknown keys are accepted, never rejected. Pydantic runs
    in default (lax) mode, so YAML-native scalars validate as-is while quoted scalars such as ``"true"`` still coerce
    to booleans, mirroring lenient runtime parsing.

    Field annotations use ``Optional``/``Union`` instead of PEP 604 ``X | Y`` because Pydantic evaluates them at
    runtime and PEP 604 unions raise ``TypeError`` on Python 3.9, the minimum supported version.
    """

    model_config = ConfigDict(extra="allow")

    name: Optional[str] = None
    description: Optional[str] = None
    when_to_use: Optional[str] = None
    argument_hint: Optional[str] = Field(default=None, alias="argument-hint")
    arguments: Optional[Union[str, list[str]]] = None
    disable_model_invocation: bool = Field(default=False, alias="disable-model-invocation")
    user_invocable: bool = Field(default=True, alias="user-invocable")
    allowed_tools: Optional[Union[str, list[str]]] = Field(default=None, alias="allowed-tools")
    disallowed_tools: Optional[Union[str, list[str]]] = Field(default=None, alias="disallowed-tools")
    model: Optional[str] = None
    effort: Optional[Literal["low", "medium", "high", "xhigh", "max"]] = None
    context: Optional[Literal["fork"]] = None
    agent: Optional[str] = None
    hooks: Optional[dict[str, Any]] = None
    paths: Optional[Union[str, list[str]]] = None
    shell: Optional[Literal["bash", "powershell"]] = None


class SkillMarkdownFile:
    """Splits a SKILL.md file into its YAML frontmatter block and validates that block's schema."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.text = path.read_text(encoding="utf-8")

    def has_frontmatter(self) -> bool:
        """Return True when the file's first line is the ``---`` frontmatter delimiter."""
        return self.text.splitlines()[:1] == [_DELIMITER]

    def validate_frontmatter(self) -> SkillFrontmatter:
        """Parse and validate this file's frontmatter block.

        Callers must ensure ``has_frontmatter()`` is true first.

        Raises:
            FrontmatterError: If the block is unclosed, is not valid YAML, is not a mapping,
                or fails schema validation.
        """
        try:
            return SkillFrontmatter.model_validate(self._parse())
        except ValidationError as error:
            raise FrontmatterError(str(error)) from error

    def _yaml_block(self) -> str:
        """Return the text between the opening and closing ``---`` delimiter lines.

        Raises:
            FrontmatterError: If no closing delimiter line exists.
        """
        lines = self.text.splitlines()
        try:
            end = lines.index(_DELIMITER, 1)
        except ValueError as error:
            message = "frontmatter opened with '---' but never closed"
            raise FrontmatterError(message) from error
        return "\n".join(lines[1:end])

    def _parse(self) -> dict[str, Any]:
        """Return the frontmatter block parsed as a YAML mapping (an empty block parses to ``{}``).

        Raises:
            FrontmatterError: If the block is not valid YAML or parses to a non-mapping value.
        """
        try:
            parsed = yaml.safe_load(self._yaml_block())
        except yaml.YAMLError as error:
            message = f"frontmatter is not valid YAML: {error}"
            raise FrontmatterError(message) from error
        if parsed is None:
            return {}
        if not isinstance(parsed, dict):
            message = f"frontmatter must be a YAML mapping, got {type(parsed).__name__}"
            raise FrontmatterError(message)
        return parsed


class SkillsDirectoryLinter:
    """Validates the frontmatter of every SKILL.md under a skills directory."""

    def __init__(self, skills_dir: Path) -> None:
        self.skills_dir = skills_dir

    def collect_failures(self) -> list[str]:
        """Return one ``<path>: <error>`` message per SKILL.md whose existing frontmatter fails validation.

        Files without a frontmatter block are skipped: presence/structure checking is skill-validator's job;
        this linter only adds field-schema validation on top of frontmatter that exists.
        """
        failures: list[str] = []
        for skill_md in sorted(self.skills_dir.rglob("SKILL.md")):
            failure = self._check(skill_md)
            if failure is not None:
                failures.append(failure)
        return failures

    @staticmethod
    def _check(skill_md: Path) -> str | None:
        """Return a failure message for ``skill_md``, or None when it passes or has no frontmatter."""
        skill_file = SkillMarkdownFile(skill_md)
        if not skill_file.has_frontmatter():
            return None
        try:
            skill_file.validate_frontmatter()
        except FrontmatterError as error:
            return f"{skill_md}: {error}"
        return None
