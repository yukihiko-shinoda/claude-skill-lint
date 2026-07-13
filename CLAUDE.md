# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

`csklint` (CLI name `csklint`) is a linter for Claude Code skills. Rather than reimplementing skill
validation, it bundles a pytest suite combining two external tools — `skill-validator` (a Go binary) and
`markdownlint-cli2` (an npm package) — with a pure-Python frontmatter schema check built on Pydantic, and provides
a `csklint install` subcommand to fetch and install the external tools.

## Commands

```bash
# Setup
uv sync

# Run this project's own test suite (unit + integration tests, mirrors src layout under tests/)
uv run invoke test              # fast tests only (excludes @pytest.mark.slow)
uv run invoke test.all          # all tests, including slow end-to-end tests
uv run pytest tests/test_installation.py::TestInstaller::test_check_os_supported_macos  # single test

# Lint / format (see /workspace/CLAUDE.local.md for the full tool list and flags)
uv run invoke lint
uv run invoke style --check

# Install the external tools the bundled linter suite depends on (Go binary + npm package)
uv run csklint install

# Run the bundled skill-validation suite against a real skills directory
uv run csklint run [SKILLS_DIR]   # defaults to ~/.claude/skills
```

A `PostToolUse` hook in [.claude/settings.json](.claude/settings.json) runs `uv run invoke lint` automatically after
every `Write`/`Edit`, so linting does not need to be triggered manually after making changes.

## Architecture

### Two CLI entry points, one real

[pyproject.toml](pyproject.toml) registers two console scripts:
- `csklint` → [csklint/cli.py](csklint/cli.py) `main()` — leftover cookiecutter scaffold
  placeholder, not the real interface.
- `csklint` → [csklint/cli.py](csklint/cli.py) `csklint` Click group — the actual CLI, with two
  subcommands: `run` (invoke the bundled skill-validation suite against a target directory) and `install` (fetch the
  external tools that suite depends on).

### Two distinct test suites — do not confuse them

This repo has two `pytest` suites that look similar but serve different purposes:

- **`tests/`** — the project's own test suite for this package's Python code (`installation.py`, `cli.py`, etc.). It
  mirrors `csklint/` 1:1 (e.g. `csklint/installation.py` → `tests/test_installation.py`) and is what
  `uv run invoke test` / bare `pytest` runs (`testpaths = ["tests"]` in [pyproject.toml](pyproject.toml)). Network
  calls in `SkillValidatorInstaller` are mocked via the `fake_release` fixtures in
  [tests/conftest.py](tests/conftest.py); everything else uses real objects/filesystem (`tmp_path`).
- **`csklint/_tests/`** — the linter's actual product: a pytest suite *shipped inside the wheel* (see its
  docstring) that end users run via `csklint run <skills_dir>` to validate their own Claude Code skills. Its tests
  hard-fail (not skip) via `assert_tool_on_path()` in
  [csklint/_tests/tool_requirement.py](csklint/_tests/tool_requirement.py) when `skill-validator` or
  `markdownlint-cli2` aren't on PATH, so it is intentionally excluded from `testpaths` and not collected by bare
  `pytest`. It gets exercised end-to-end only through
  [tests/test_cli.py](tests/test_cli.py)`::TestRun` (marked `@pytest.mark.slow`), which shells out to the real
  `csklint run` against [tests/fixtures/skills/](tests/fixtures/skills/) using the real installed binaries — no
  mocks. `tests/_tests/` mirrors `csklint/_tests/` the same way `tests/` mirrors `csklint/`
  (e.g. `tests/_tests/test_tool_requirement.py` tests `csklint/_tests/tool_requirement.py`).

### Frontmatter schema check ([csklint/frontmatter.py](csklint/frontmatter.py))

Unlike the two shelled-out checks, [csklint/_tests/test_frontmatter_lint.py](csklint/_tests/test_frontmatter_lint.py)
runs in-process: it validates each `SKILL.md`'s YAML frontmatter against `SkillFrontmatter`, a Pydantic model of the
documented frontmatter reference (field types, fixed enums like `effort`/`shell`, string-or-list shapes).
`extra="allow"` mirrors skill-validator's `--allow-extra-frontmatter`. Files without a frontmatter block are skipped
(presence is skill-validator's job); frontmatter that is invalid YAML, unclosed, or not a mapping is a failure.
Cross-referencing checks (is `model` a live alias? does `agent` exist on disk?) are intentionally out of scope. The
model's field annotations use `Optional`/`Union` (not PEP 604) because Pydantic evaluates them at runtime on
Python 3.9; Ruff's `keep-runtime-typing = true` preserves that. Reusable logic lives in
[csklint/frontmatter.py](csklint/frontmatter.py) (mirrored by `tests/test_frontmatter.py`); the shipped test file is
a thin wrapper like the other two checks.

### External tool installation ([csklint/installation.py](csklint/installation.py))

`Installer.install()` orchestrates three steps, in order:
1. `NodeInstaller.ensure_npm()` — installs Node.js via Homebrew (macOS) or `apt-get` (Debian/Ubuntu only; other
   Linux distros are rejected by `Installer.check_os_supported()`) if `npm` isn't already on PATH.
2. `SkillValidatorInstaller.install()` — downloads the GoReleaser tarball for the current OS/arch matching
   `SKILL_VALIDATOR_VERSION`, downloads the matching `*_checksums.txt`, verifies the tarball's SHA-256 before
   extracting, and extracts only the named `skill-validator` member (not `extractall`) to avoid path traversal, then
   installs it to `/usr/local/bin/skill-validator` with mode `0o755`.
3. `npm install -g markdownlint-cli2`.

When bumping `SKILL_VALIDATOR_VERSION`, both the download URL and the checksum file are re-derived from it
automatically — no other file needs updating.

### CI

Workflows in [.github/workflows/](.github/workflows/) all delegate to reusable workflows in the
`yukihiko-shinoda/reusable-workflow-invoke-lint-*` repos (test, lint, qlty, deploy) pinned by commit SHA, plus a
standard CodeQL workflow. The test workflow's `post-sync-command-linux` runs
`sudo env "PATH=$PATH" uv run --no-sync csklint install` before tests execute — this is what puts `skill-validator`
and `markdownlint-cli2` on PATH in CI so the `@pytest.mark.slow` end-to-end test can run; the devcontainer image
installs the same tools at build time (see [Dockerfile](Dockerfile)) for local development.
