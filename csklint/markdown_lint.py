"""Locate the shared markdownlint-cli2 configuration file for a Claude Code skills directory."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

_CONFIG_FILENAMES: tuple[str, ...] = (
    ".markdownlint-cli2.jsonc",
    ".markdownlint-cli2.yaml",
    ".markdownlint-cli2.yml",
    ".markdownlint-cli2.json",
    ".markdownlint-cli2.cjs",
    ".markdownlint-cli2.mjs",
)


class MarkdownlintConfigResolver:
    """Locate the shared markdownlint-cli2 config file for a Claude Code skills directory tree.

    skill-validator supports exactly two invocation shapes for its target directory: a single skill directory, or
    a parent directory containing multiple skill subdirectories. markdownlint-cli2's own config search never looks
    above the process's cwd, so when csklint sets cwd to a single skill directory, a shared config placed in that
    skill's parent (the top-level skills directory) would otherwise be invisible. This resolver checks exactly the
    two directories a shared config could occupy, given those two supported invocation shapes -- it is not a
    general upward-walking search.
    """

    def __init__(self, skills_dir: Path) -> None:
        self.skills_dir = skills_dir

    def resolve(self) -> Path | None:
        """Return the first matching config file in ``skills_dir``, else in its parent, else None."""
        for directory in self._search_directories():
            found = self._find_in(directory)
            if found is not None:
                return found
        return None

    def _search_directories(self) -> list[Path]:
        """Return candidate directories in precedence order: skills_dir, then its parent (deduplicated)."""
        parent = self.skills_dir.parent
        if parent == self.skills_dir:
            return [self.skills_dir]
        return [self.skills_dir, parent]

    @staticmethod
    def _find_in(directory: Path) -> Path | None:
        """Return the first existing config filename (in ``_CONFIG_FILENAMES`` order) in directory, or None."""
        for filename in _CONFIG_FILENAMES:
            candidate = directory / filename
            if candidate.is_file():
                return candidate
        return None
