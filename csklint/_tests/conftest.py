"""Pytest configuration for the bundled skills-validation suite."""

from __future__ import annotations

from pathlib import Path

import pytest

DEFAULT_SKILLS_DIR = Path.home() / ".claude" / "skills"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register the ``--skills-dir`` option so ``csklint`` can pass a skills directory."""
    parser.addoption(
        "--skills-dir",
        action="store",
        default=str(DEFAULT_SKILLS_DIR),
        help="Directory containing Claude Code skills to validate.",
    )


@pytest.fixture
def skills_dir(request: pytest.FixtureRequest) -> Path:
    """Return the skills directory supplied via ``--skills-dir`` (defaults to ~/.claude/skills)."""
    return Path(request.config.getoption("--skills-dir"))
