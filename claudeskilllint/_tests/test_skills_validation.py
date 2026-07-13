"""Validate Claude Code skills by delegating to the ``skill-validator`` binary."""

from __future__ import annotations

import subprocess  # nosec B404 - subprocess is used intentionally to invoke the skill-validator binary
from typing import TYPE_CHECKING

from claudeskilllint._tests.tool_requirement import assert_tool_on_path

if TYPE_CHECKING:
    from pathlib import Path


class TestSkillValidator:
    """Validate Claude Code skills using the skill-validator binary."""

    def test_skills_pass(self, skills_dir: Path) -> None:
        """Assert that skill-validator exits 0 for all skills in the target directory."""
        assert_tool_on_path("skill-validator")
        # Reason: All args are hardcoded strings or a developer-supplied path; shell=False prevents injection.
        # The partial executable path is intentional for cross-environment portability;
        # assert_tool_on_path above verifies the binary exists before execution.
        result = subprocess.run(  # noqa: S603  # nosec B603, B607
            [  # noqa: S607
                "skill-validator",
                "validate",
                "structure",
                "--allow-extra-frontmatter",
                "--strict",
                str(skills_dir),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, (
            f"skill-validator failed (exit {result.returncode}):\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
