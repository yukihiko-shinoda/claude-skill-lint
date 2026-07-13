"""Lint the Markdown content of Claude Code skills by delegating to ``markdownlint-cli2``."""

from __future__ import annotations

import subprocess  # nosec B404 - subprocess is used intentionally to invoke the markdownlint-cli2 binary
from typing import TYPE_CHECKING

import pytest

from csklint._tests.tool_requirement import assert_tool_on_path

if TYPE_CHECKING:
    from pathlib import Path


class TestMarkdownlintCli2:
    """Lint Markdown files in Claude Code skills using markdownlint-cli2."""

    def test_skills_markdown_pass(self, skills_dir: Path) -> None:
        """Assert that markdownlint-cli2 exits 0 for every Markdown file in the target directory.

        The ``**/*.md`` glob is passed as a literal argument (``shell=False``); markdownlint-cli2 expands it itself.
        Running with ``cwd=skills_dir`` lets markdownlint-cli2 auto-discover a ``.markdownlint-cli2.jsonc`` (or
        similar) config inside the skills tree, falling back to its built-in default ruleset otherwise.
        """
        assert_tool_on_path("markdownlint-cli2")
        if not skills_dir.is_dir():
            pytest.fail(f"Skills directory does not exist: {skills_dir}")
        # Reason: All args are hardcoded strings; the glob is expanded by markdownlint-cli2 itself,
        # not a shell (shell=False prevents injection). The partial executable path is intentional
        # for cross-environment portability; assert_tool_on_path above verifies the binary exists.
        result = subprocess.run(  # nosec B603, B607
            ["markdownlint-cli2", "**/*.md"],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
            cwd=str(skills_dir),
        )
        assert result.returncode == 0, (
            f"markdownlint-cli2 failed (exit {result.returncode}):\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
