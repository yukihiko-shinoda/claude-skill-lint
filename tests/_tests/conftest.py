"""Configuration of pytest for the claudeskilllint._tests unit tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def path_without_tools(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Point PATH at an empty directory so that no command-line tool can be found."""
    monkeypatch.setenv("PATH", str(tmp_path))


@pytest.fixture
def path_with_fake_tool(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Point PATH at a directory containing only an executable ``fake-tool.bat``.

    The ``.bat`` suffix keeps the fixture portable: ``shutil.which`` on Windows resolves commands via ``PATHEXT``
    (which includes ``.BAT`` by default), while on POSIX the explicit suffix plus the executable bit suffices.
    """
    fake_tool = tmp_path / "fake-tool.bat"
    fake_tool.write_text("", encoding="utf-8")
    fake_tool.chmod(0o755)
    monkeypatch.setenv("PATH", str(tmp_path))
