"""Console scripts for csklint."""

import sys
from importlib import resources
from pathlib import Path

import click
import pytest

from csklint.installation import Installer

DEFAULT_SKILLS_DIR = Path.home() / ".claude" / "skills"


@click.group()
def csklint() -> None:
    """Lint Claude Code skills and install the tools the linter depends on."""


@csklint.command()
@click.argument(
    "skills_dir",
    required=False,
    default=str(DEFAULT_SKILLS_DIR),
    type=click.Path(),
)
def run(skills_dir: str) -> int:
    """Run the bundled skills-validation tests against SKILLS_DIR (defaults to ~/.claude/skills)."""
    with resources.as_file(resources.files("csklint") / "_tests") as tests_dir:
        return int(pytest.main([str(tests_dir), f"--skills-dir={skills_dir}"]))


@csklint.command()
def install() -> None:
    """Install skill-validator (Go binary) and markdownlint-cli2 (npm)."""
    sys.exit(Installer().install())


if __name__ == "__main__":
    sys.exit(csklint())  # pragma: no cover
