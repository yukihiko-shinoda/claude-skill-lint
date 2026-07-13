# Claude Skill Lint

[![Test](https://github.com/yukihiko-shinoda/claude-skill-lint/workflows/Test/badge.svg)](https://github.com/yukihiko-shinoda/claude-skill-lint/actions?query=workflow%3ATest)
[![CodeQL](https://github.com/yukihiko-shinoda/claude-skill-lint/workflows/CodeQL/badge.svg)](https://github.com/yukihiko-shinoda/claude-skill-lint/actions?query=workflow%3ACodeQL)
[![Code Coverage](https://qlty.sh/gh/yukihiko-shinoda/projects/claude-skill-lint/coverage.svg)](https://qlty.sh/gh/yukihiko-shinoda/projects/claude-skill-lint)
[![Maintainability](https://qlty.sh/gh/yukihiko-shinoda/projects/claude-skill-lint/maintainability.svg)](https://qlty.sh/gh/yukihiko-shinoda/projects/claude-skill-lint)
[![Dependabot](https://flat.badgen.net/github/dependabot/yukihiko-shinoda/claude-skill-lint?icon=dependabot)](https://github.com/yukihiko-shinoda/claude-skill-lint/security/dependabot)
[![Python versions](https://img.shields.io/pypi/pyversions/csklint)](https://pypi.org/project/csklint/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/csklint)](https://pypi.org/project/csklint/)
[![X URL](https://img.shields.io/twitter/url?style=social&url=https%3A%2F%2Fgithub.com%2Fyukihiko-shinoda%2Fclaude-skill-lint)](https://x.com/intent/post?text=Claude%20Skill%20Lint&url=https%3A%2F%2Fpypi.org%2Fproject%2Fcsklint%2F&hashtags=python)

The linter for Claude Code skill.

## Advantage

* Wraps two purpose-built validators — [skill-validator] for `SKILL.md` structure and frontmatter, and
  `markdownlint-cli2` for Markdown hygiene — behind a single command, so you don't need to discover,
  install, and orchestrate them yourself.
* `csklint install` fetches and installs both tools (a Go binary and an npm package) for you, verifying
  the binary's SHA-256 checksum before installing it, on macOS, Debian, and Ubuntu.
* `csklint run` executes as a pytest suite, so failures show up as familiar pytest output and slot
  straight into CI pipelines or pre-commit hooks without extra tooling.

## Quickstart

Install the CLI:

```console
pip install csklint
```

Install the tools it depends on (skill-validator and markdownlint-cli2):

```console
csklint install
```

Lint your skills (defaults to `~/.claude/skills`):

```console
csklint run
```

A passing run prints a pytest summary ending in `... passed`; a failing skill reports the offending
file and the validator's error output.

<!-- markdownlint-disable no-trailing-punctuation -->
## How do I...
<!-- markdownlint-enable no-trailing-punctuation -->

### How do I lint skills in a different directory?

Pass the directory as an argument:

```console
csklint run path/to/skills
```

### How do I use this in CI?

Run `csklint install` once per CI run, then `csklint run <skills_dir>`; both exit non-zero on failure
so the step fails the build.

```yaml
- run: csklint install
- run: csklint run skills/
```

### How do I install without root privileges?

`csklint install` writes `skill-validator` to `/usr/local/bin`, which typically requires root. Re-run
the command with `sudo` if it reports a permission error.

[skill-validator]: https://github.com/agent-ecosystem/skill-validator

## Credits

This package was created with [Cookiecutter] and the [yukihiko-shinoda/cookiecutter-pypackage] project template.

[Cookiecutter]: https://github.com/audreyr/cookiecutter
[yukihiko-shinoda/cookiecutter-pypackage]: https://github.com/audreyr/cookiecutter-pypackage
