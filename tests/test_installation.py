"""Tests for `claudeskilllint.installation` module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click
import pytest

from claudeskilllint.installation import Installer
from claudeskilllint.installation import NodeInstaller
from claudeskilllint.installation import SkillValidatorInstaller

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_mock import MockerFixture

    from tests.conftest import FakeSkillValidatorRelease


class TestInstaller:
    """Tests for the Installer class."""

    def test_check_os_supported_macos(self, mocker: MockerFixture) -> None:
        mocker.patch("claudeskilllint.installation.platform.system", return_value="Darwin")
        assert Installer().check_os_supported() is True

    def test_check_os_supported_debian(self, tmp_path: Path) -> None:
        os_release = tmp_path / "os-release"
        os_release.write_text('ID=debian\nVERSION_ID="12"\n')
        assert Installer(os_release).check_os_supported() is True

    def test_check_os_supported_ubuntu(self, tmp_path: Path) -> None:
        os_release = tmp_path / "os-release"
        os_release.write_text('ID=ubuntu\nVERSION_ID="24.04"\n')
        assert Installer(os_release).check_os_supported() is True

    def test_check_os_supported_unsupported_linux(self, tmp_path: Path) -> None:
        os_release = tmp_path / "os-release"
        os_release.write_text("ID=arch\n")
        assert Installer(os_release).check_os_supported() is False

    def test_check_os_supported_missing_os_release(self, tmp_path: Path) -> None:
        assert Installer(tmp_path / "nonexistent").check_os_supported() is False

    def test_check_os_supported_unsupported_system(self, mocker: MockerFixture, tmp_path: Path) -> None:
        mocker.patch("claudeskilllint.installation.platform.system", return_value="Windows")
        assert Installer(tmp_path / "nonexistent").check_os_supported() is False


class TestNodeInstaller:
    """Tests for the NodeInstaller class."""

    def test_ensure_npm_present_does_nothing(self, mocker: MockerFixture) -> None:
        """Do not attempt any install when npm is already on PATH."""
        mocker.patch("claudeskilllint.installation.shutil.which", return_value="/usr/bin/npm")
        run_mock = mocker.patch("claudeskilllint.installation.subprocess.run")
        NodeInstaller().ensure_npm()
        run_mock.assert_not_called()

    def test_ensure_npm_installs_nodejs_on_debian(self, mocker: MockerFixture) -> None:
        """Run `apt-get update` then `apt-get install -y nodejs npm` when npm is missing on a non-Darwin OS."""
        mocker.patch("claudeskilllint.installation.shutil.which", return_value=None)
        mocker.patch("claudeskilllint.installation.platform.system", return_value="Linux")
        run_mock = mocker.patch(
            "claudeskilllint.installation.subprocess.run",
            return_value=mocker.Mock(returncode=0),
        )
        NodeInstaller().ensure_npm()
        assert run_mock.call_args_list == [
            mocker.call(["apt-get", "update"], check=False),
            mocker.call(["apt-get", "install", "-y", "nodejs", "npm"], check=False),
        ]

    def test_ensure_npm_installs_nodejs_on_macos(self, mocker: MockerFixture) -> None:
        """Run `brew install node` when npm is missing and brew is on PATH on macOS."""
        mocker.patch(
            "claudeskilllint.installation.shutil.which",
            side_effect=lambda name: None if name == "npm" else "/opt/homebrew/bin/brew",
        )
        mocker.patch("claudeskilllint.installation.platform.system", return_value="Darwin")
        run_mock = mocker.patch(
            "claudeskilllint.installation.subprocess.run",
            return_value=mocker.Mock(returncode=0),
        )
        NodeInstaller().ensure_npm()
        run_mock.assert_called_once_with(["brew", "install", "node"], check=False)

    def test_ensure_npm_macos_without_brew_raises(self, mocker: MockerFixture) -> None:
        """Raise ClickException guiding the user to install Homebrew when brew is absent on macOS."""
        mocker.patch("claudeskilllint.installation.shutil.which", return_value=None)
        mocker.patch("claudeskilllint.installation.platform.system", return_value="Darwin")
        with pytest.raises(click.ClickException, match="Homebrew"):
            NodeInstaller().ensure_npm()

    def test_ensure_npm_debian_install_failure_raises(self, mocker: MockerFixture) -> None:
        """Raise ClickException when `apt-get install` returns a non-zero exit code after a successful update."""
        mocker.patch("claudeskilllint.installation.shutil.which", return_value=None)
        mocker.patch("claudeskilllint.installation.platform.system", return_value="Linux")
        mocker.patch(
            "claudeskilllint.installation.subprocess.run",
            side_effect=[mocker.Mock(returncode=0), mocker.Mock(returncode=1)],
        )
        with pytest.raises(click.ClickException, match="apt-get install"):
            NodeInstaller().ensure_npm()

    def test_ensure_npm_debian_update_failure_still_installs(
        self,
        mocker: MockerFixture,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Warn but still run `apt-get install` when `apt-get update` returns a non-zero exit code."""
        mocker.patch("claudeskilllint.installation.shutil.which", return_value=None)
        mocker.patch("claudeskilllint.installation.platform.system", return_value="Linux")
        run_mock = mocker.patch(
            "claudeskilllint.installation.subprocess.run",
            side_effect=[mocker.Mock(returncode=1), mocker.Mock(returncode=0)],
        )
        NodeInstaller().ensure_npm()
        assert run_mock.call_args_list == [
            mocker.call(["apt-get", "update"], check=False),
            mocker.call(["apt-get", "install", "-y", "nodejs", "npm"], check=False),
        ]
        assert "warning: `apt-get update` failed" in capsys.readouterr().out

    def test_ensure_npm_macos_install_failure_raises(self, mocker: MockerFixture) -> None:
        """Raise ClickException when `brew install node` returns a non-zero exit code."""
        mocker.patch(
            "claudeskilllint.installation.shutil.which",
            side_effect=lambda name: None if name == "npm" else "/opt/homebrew/bin/brew",
        )
        mocker.patch("claudeskilllint.installation.platform.system", return_value="Darwin")
        mocker.patch(
            "claudeskilllint.installation.subprocess.run",
            return_value=mocker.Mock(returncode=1),
        )
        with pytest.raises(click.ClickException, match="brew install node"):
            NodeInstaller().ensure_npm()


class TestSkillValidatorInstaller:
    """Tests for the SkillValidatorInstaller class (network mocked)."""

    def test_install(self, fake_release: FakeSkillValidatorRelease, tmp_path: Path) -> None:
        """Verify binary content and 0o755 permissions after a successful install."""
        install_path = tmp_path / "skill-validator"
        expected_mode = 0o755
        SkillValidatorInstaller(install_path=install_path).install()
        assert install_path.read_bytes() == fake_release.binary_content
        assert (install_path.stat().st_mode & 0o777) == expected_mode

    @pytest.mark.usefixtures("fake_release_bad_checksum")
    def test_install_checksum_mismatch(self, tmp_path: Path) -> None:
        """Raise ClickException when the downloaded tarball does not match the expected checksum."""
        with pytest.raises(click.ClickException, match="checksum verification failed"):
            SkillValidatorInstaller(install_path=tmp_path / "skill-validator").install()

    @pytest.mark.usefixtures("fake_release")
    def test_install_permission_error(self, mocker: MockerFixture, tmp_path: Path) -> None:
        """Raise ClickException with 'Permission denied' when the install path is not writable."""
        mocker.patch("claudeskilllint.installation.shutil.copy2", side_effect=PermissionError)
        with pytest.raises(click.ClickException, match="Permission denied"):
            SkillValidatorInstaller(install_path=tmp_path / "skill-validator").install()
