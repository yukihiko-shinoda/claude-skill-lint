"""Tests for csklint._tests.tool_requirement."""

from __future__ import annotations

import pytest

from csklint._tests.tool_requirement import assert_tool_on_path


class TestAssertToolOnPath:
    """Tests for assert_tool_on_path()."""

    @pytest.mark.usefixtures("path_without_tools")
    def test_missing_tool(self) -> None:
        """Fail (not skip) with a `csklint install` hint when the tool is absent from PATH."""
        expected = r"skill-validator not found on PATH; run `csklint install` to install it"
        with pytest.raises(pytest.fail.Exception, match=expected):
            assert_tool_on_path("skill-validator")

    @pytest.mark.usefixtures("path_with_fake_tool")
    def test_existing_tool(self) -> None:
        """Return without failing when the tool is present on PATH."""
        assert_tool_on_path("fake-tool.bat")
