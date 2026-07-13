"""Installation of the external tools the skill linter depends on."""

from __future__ import annotations

import hashlib
import platform
import shutil
import subprocess  # nosec B404 - subprocess is used intentionally to invoke npm tooling
import tarfile
import tempfile
import urllib.request
from pathlib import Path

import click

NPM_TOOLS = ("markdownlint-cli2",)
_SUPPORTED_LINUX_IDS = frozenset({"debian", "ubuntu"})
_DEFAULT_OS_RELEASE_PATH = Path("/etc/os-release")

SKILL_VALIDATOR_VERSION = "1.5.6"
_SKILL_VALIDATOR_REPO_URL = "https://github.com/agent-ecosystem/skill-validator/releases/download"
_SKILL_VALIDATOR_INSTALL_PATH = Path("/usr/local/bin/skill-validator")
ARCH_MAP = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64"}
_CHECKSUMS_LINE_FIELDS = 2


class SkillValidatorInstaller:
    """Downloads, verifies, extracts, and installs the skill-validator Go binary onto PATH."""

    def __init__(self, version: str = SKILL_VALIDATOR_VERSION, install_path: Path | None = None) -> None:
        """Compute the GoReleaser release coordinates for the current platform.

        Args:
            version: The skill-validator release version to install.
            install_path: Destination for the binary (defaults to /usr/local/bin/skill-validator).

        Raises:
            click.ClickException: If the machine architecture is not supported.
        """
        self.version = version
        self.install_path = _SKILL_VALIDATOR_INSTALL_PATH if install_path is None else install_path
        self.os_token = "darwin" if platform.system() == "Darwin" else "linux"
        self.arch_token = self._release_arch()
        self.tarball_name = f"skill-validator_{version}_{self.os_token}_{self.arch_token}.tar.gz"
        self.checksums_name = f"skill-validator_{version}_checksums.txt"
        self.base_url = f"{_SKILL_VALIDATOR_REPO_URL}/v{version}"

    @staticmethod
    def _release_arch() -> str:
        """Return the GoReleaser arch token (``amd64`` or ``arm64``) for the current machine.

        Raises:
            click.ClickException: If the machine architecture is not supported.
        """
        machine = platform.machine().lower()
        arch = ARCH_MAP.get(machine)
        if arch is None:
            message = f"Unsupported CPU architecture '{machine}'; skill-validator provides amd64 and arm64 only."
            raise click.ClickException(message)
        return arch

    def install(self) -> None:
        """Download, verify, extract, and install the skill-validator Go binary onto PATH."""
        click.echo(f"Installing skill-validator {self.version} ({self.os_token}/{self.arch_token})...")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            tarball_path = tmp_dir / self.tarball_name
            checksums_path = tmp_dir / self.checksums_name
            self._download(f"{self.base_url}/{self.tarball_name}", tarball_path)
            self._download(f"{self.base_url}/{self.checksums_name}", checksums_path)
            expected = self._expected_checksum(checksums_path.read_text(encoding="utf-8"))
            self._verify_checksum(tarball_path, expected)
            self._install_binary(self._extract_binary(tarball_path, tmp_dir))
        click.echo(f"skill-validator installed to {self.install_path}.")

    @staticmethod
    def _download(url: str, destination: Path) -> None:
        """Download ``url`` to ``destination`` using the standard library."""
        with urllib.request.urlopen(url) as response:  # noqa: S310  # nosec B310
            destination.write_bytes(response.read())

    def _expected_checksum(self, checksums_text: str) -> str:
        """Return the sha256 hex digest recorded for the tarball in ``checksums_text``.

        Args:
            checksums_text: Contents of the ``*_checksums.txt`` file (``<hex>  <name>`` per line).

        Raises:
            click.ClickException: If the tarball is not present in the checksums file.
        """
        for line in checksums_text.splitlines():
            parts = line.split()
            if len(parts) == _CHECKSUMS_LINE_FIELDS and parts[1] == self.tarball_name:
                return parts[0]
        message = f"Checksum for '{self.tarball_name}' not found in the skill-validator checksums file."
        raise click.ClickException(message)

    @staticmethod
    def _verify_checksum(tarball_path: Path, expected_hex: str) -> None:
        """Raise if the sha256 of ``tarball_path`` does not equal ``expected_hex``.

        Raises:
            click.ClickException: On checksum mismatch.
        """
        actual_hex = hashlib.sha256(tarball_path.read_bytes()).hexdigest()
        if actual_hex != expected_hex:
            message = f"skill-validator checksum verification failed: expected {expected_hex}, got {actual_hex}."
            raise click.ClickException(message)

    @staticmethod
    def _extract_binary(tarball_path: Path, destination_dir: Path) -> Path:
        """Extract the ``skill-validator`` member from ``tarball_path`` into ``destination_dir``.

        Only the single named member is extracted (not ``extractall``) to avoid path traversal.

        Raises:
            click.ClickException: If the archive has no ``skill-validator`` member.
        """
        with tarfile.open(tarball_path, "r:gz") as archive:
            try:
                member = archive.getmember("skill-validator")
            except KeyError as error:
                message = "The skill-validator archive does not contain a 'skill-validator' binary."
                raise click.ClickException(message) from error
            archive.extract(member, path=destination_dir)
        return destination_dir / "skill-validator"

    def _install_binary(self, source: Path) -> None:
        """Copy ``source`` to the install path with mode 0o755.

        Raises:
            click.ClickException: If the destination is not writable (guides the user to use sudo).
        """
        try:
            shutil.copy2(source, self.install_path)
            self.install_path.chmod(0o755)
        except PermissionError as error:
            message = (
                f"Permission denied writing to {self.install_path}. "
                "Re-run `csklint install` with sudo, or install into a writable directory on PATH."
            )
            raise click.ClickException(message) from error


class NodeInstaller:
    """Installs Node.js via the OS package manager when npm is not on PATH."""

    def ensure_npm(self) -> None:
        """Install Node.js (which brings npm) via the OS package manager when npm is not on PATH."""
        if shutil.which("npm") is not None:
            return
        if platform.system() == "Darwin":
            self._install_macos()
        else:
            self._install_debian()

    @staticmethod
    def _install_macos() -> None:
        """Install Node.js on macOS via Homebrew.

        Raises:
            click.ClickException: If Homebrew is not on PATH, or if `brew install node` fails.
        """
        if shutil.which("brew") is None:
            message = (
                "npm not found and Homebrew is not installed. "
                "Install Homebrew from https://brew.sh, then re-run `csklint install`."
            )
            raise click.ClickException(message)
        click.echo("npm not found; installing Node.js via `brew install node`...")
        completed = subprocess.run(  # nosec B603, B607
            ["brew", "install", "node"],  # noqa: S607
            check=False,
        )
        if completed.returncode != 0:
            message = "`brew install node` failed; install Node.js manually, then re-run `csklint install`."
            raise click.ClickException(message)

    @staticmethod
    def _install_debian() -> None:
        """Install Node.js and npm on Debian/Ubuntu via apt-get.

        Run `apt-get update` first so a stale or never-populated package index does not break the install.
        Assumes the process runs as root (typical in the devcontainer); no sudo is prepended.

        Raises:
            click.ClickException: If `apt-get install` fails.
        """
        click.echo("npm not found; installing Node.js via `apt-get update` and `apt-get install -y nodejs npm`...")
        updated = subprocess.run(  # nosec B603, B607
            ["apt-get", "update"],  # noqa: S607
            check=False,
        )
        if updated.returncode != 0:
            click.echo("warning: `apt-get update` failed; attempting `apt-get install` anyway...")
        completed = subprocess.run(  # nosec B603, B607
            ["apt-get", "install", "-y", "nodejs", "npm"],  # noqa: S607
            check=False,
        )
        if completed.returncode != 0:
            message = (
                "`apt-get install -y nodejs npm` failed; ensure you have root privileges, "
                "then re-run `csklint install`."
            )
            raise click.ClickException(message)


class Installer:
    """Installs skill-validator (Go binary) and markdownlint-cli2 (npm)."""

    def __init__(self, os_release_path: Path = _DEFAULT_OS_RELEASE_PATH) -> None:
        self.os_release_path = os_release_path

    def check_os_supported(self) -> bool:
        """Return True if the current OS is macOS, Debian, or Ubuntu."""
        if platform.system() == "Darwin":
            return True
        if not self.os_release_path.exists():
            return False
        for line in self.os_release_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("ID="):
                return line.split("=", 1)[1].strip().strip('"').lower() in _SUPPORTED_LINUX_IDS
        return False

    def install(self) -> int:
        """Install all tools the linter depends on and return the npm exit code.

        Raises:
            click.ClickException: If the OS is unsupported, or if Node.js installation fails.
        """
        self._check_os()
        NodeInstaller().ensure_npm()
        SkillValidatorInstaller().install()
        return self._install_npm_tools()

    def _check_os(self) -> None:
        """Raise click.ClickException unless the OS is macOS, Debian, or Ubuntu."""
        if not self.check_os_supported():
            message = "Unsupported OS. `csklint install` supports Debian, Ubuntu, and macOS only."
            raise click.ClickException(message)

    @staticmethod
    def _install_npm_tools() -> int:
        """Install the npm tools globally and return the npm exit code."""
        click.echo(f"Installing npm tools: {', '.join(NPM_TOOLS)}")
        completed = subprocess.run(  # noqa: S603  # nosec B603, B607
            ["npm", "install", "-g", *NPM_TOOLS],  # noqa: S607
            check=False,
        )
        return completed.returncode
