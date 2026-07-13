"""Requirement checks for the external command-line tools the bundled tests depend on."""

from __future__ import annotations

import shutil

import pytest


def assert_tool_on_path(tool: str) -> None:
    """Fail the calling test when ``tool`` is not found on PATH.

    Args:
        tool: Name of the required command-line tool (e.g. ``skill-validator``).
    """
    if shutil.which(tool) is None:
        pytest.fail(f"{tool} not found on PATH; run `csklint install` to install it")
