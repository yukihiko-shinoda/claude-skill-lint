"""Lint the Markdown content of Claude Code skills by delegating to ``markdownlint-cli2``."""

from __future__ import annotations

import subprocess  # nosec B404 - subprocess is used intentionally to invoke the markdownlint-cli2 binary
from typing import TYPE_CHECKING

import pytest

from csklint._tests.tool_requirement import assert_tool_on_path
from csklint.markdown_lint import MarkdownlintConfigResolver

if TYPE_CHECKING:
    from pathlib import Path


class TestMarkdownlintCli2:
    """Lint Markdown files in Claude Code skills using markdownlint-cli2."""

    def test_skills_markdown_pass(self, skills_dir: Path) -> None:
        """Assert that markdownlint-cli2 exits 0 for every Markdown file in the target directory.

        The ``**/*.md`` glob is passed as a literal argument (``shell=False``); markdownlint-cli2 expands it itself.
        Running with ``cwd=skills_dir`` still lets markdownlint-cli2 merge any skill-local config overrides and
        resolves the glob against the right root, but a shared config is now resolved and passed explicitly via
        ``--config``: markdownlint-cli2's own search never looks above its cwd, so when csklint is invoked against a
        single skill directory (one of skill-validator's two supported target shapes), a shared config placed in that
        skill's parent -- the top-level skills directory -- would otherwise be invisible.
        """
        assert_tool_on_path("markdownlint-cli2")
        if not skills_dir.is_dir():
            pytest.fail(f"Skills directory does not exist: {skills_dir}")
        args = ["markdownlint-cli2", "**/*.md"]
        config = MarkdownlintConfigResolver(skills_dir).resolve()
        if config is not None:
            args.extend(["--config", str(config)])
        # Reason: All args are hardcoded strings or a resolved config path; the glob is expanded by
        # markdownlint-cli2 itself, not a shell (shell=False prevents injection). The partial executable
        # path is intentional for cross-environment portability; assert_tool_on_path above verifies the
        # binary exists.
        result = subprocess.run(  # noqa: S603  # nosec B603
            args,
            capture_output=True,
            text=True,
            check=False,
            cwd=str(skills_dir),
        )
        assert result.returncode == 0, (
            f"markdownlint-cli2 failed (exit {result.returncode}):\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
