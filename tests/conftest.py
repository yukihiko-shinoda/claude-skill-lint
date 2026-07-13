"""Configuration of pytest."""

from __future__ import annotations

import hashlib
import io
import shutil
import tarfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from csklint.installation import SkillValidatorInstaller

if TYPE_CHECKING:
    from typing import Self

    from pytest_mock import MockerFixture

collect_ignore = ["setup.py"]


@pytest.fixture
def csklint_command() -> str:
    """Return the absolute path of the ``csklint`` console script, failing the test when it is not on PATH."""
    path = shutil.which("csklint")
    if path is None:
        pytest.fail("csklint console script not found on PATH; run `uv sync` first.")
    return path


@pytest.fixture
def fixture_skills_dir() -> Path:
    """Return the checked-in skills directory used to exercise the bundled suite with the real tools."""
    return Path(__file__).parent / "fixtures" / "skills"


@pytest.fixture
def invalid_fixture_skills_dir() -> Path:
    """Return the checked-in skills directory whose only skill intentionally fails the bundled suite."""
    return Path(__file__).parent / "fixtures" / "invalid-skills"


class FakeResponse:
    """Minimal context-manager stand-in for the object returned by ``urllib.request.urlopen``."""

    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return self._payload


class FakeSkillValidatorRelease:
    """Fake GitHub release serving a skill-validator tarball and its checksums file."""

    def __init__(self, binary_content: bytes, digest: str | None = None) -> None:
        """Build the tarball for ``binary_content`` and record ``digest`` (or the real sha256) in the checksums."""
        self.binary_content = binary_content
        buffer = io.BytesIO()
        with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
            info = tarfile.TarInfo(name="skill-validator")
            info.size = len(binary_content)
            archive.addfile(info, io.BytesIO(binary_content))
        self.tarball_bytes = buffer.getvalue()
        self.tarball_name = SkillValidatorInstaller().tarball_name
        self.digest = digest if digest is not None else hashlib.sha256(self.tarball_bytes).hexdigest()
        self.checksums_text = f"{self.digest}  {self.tarball_name}\n"

    def urlopen(self, url: str) -> FakeResponse:
        """Serve the tarball for ``*.tar.gz`` URLs and the checksums file for any other URL."""
        payload = self.tarball_bytes if url.endswith(".tar.gz") else self.checksums_text.encode("utf-8")
        return FakeResponse(payload)


@pytest.fixture
def fake_release(mocker: MockerFixture) -> FakeSkillValidatorRelease:
    """Patch ``urlopen`` in the installation module to serve a fake release with a valid checksum."""
    release = FakeSkillValidatorRelease(b"fake-skill-validator-binary")
    mocker.patch("csklint.installation.urllib.request.urlopen", side_effect=release.urlopen)
    return release


@pytest.fixture
def fake_release_bad_checksum(mocker: MockerFixture) -> FakeSkillValidatorRelease:
    """Patch ``urlopen`` in the installation module to serve a fake release whose checksum never matches."""
    release = FakeSkillValidatorRelease(b"fake-skill-validator-binary", digest="0" * 64)
    mocker.patch("csklint.installation.urllib.request.urlopen", side_effect=release.urlopen)
    return release
