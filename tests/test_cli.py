"""Tests for claudeskilllint.cli."""

from __future__ import annotations

import subprocess  # nosec B404 - subprocess intentionally runs the csklint console script end-to-end
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


class TestRun:
    """Test ``csklint run`` end-to-end with the real skill-validator and markdownlint-cli2 binaries."""

    @pytest.mark.slow
    def test_bundled_suite_passes_against_fixture_skills(
        self,
        csklint_command: str,
        fixture_skills_dir: Path,
    ) -> None:
        """Assert ``csklint run`` exits 0 for the fixture skills directory using the real tools.

        Requires skill-validator and markdownlint-cli2 on PATH (installed by ``csklint install``): the devcontainer
        image installs them at build time, and CI installs them via the reusable test workflow's post-sync-command-
        linux hook before the test step runs.
        """
        # Reason: The executable path is resolved via shutil.which in the csklint_command fixture and the
        # arguments are a hardcoded literal plus a repository-controlled path; shell=False prevents injection.
        result = subprocess.run(  # noqa: S603  # nosec B603
            [csklint_command, "run", str(fixture_skills_dir)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, (
            f"csklint run failed (exit {result.returncode}):\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
