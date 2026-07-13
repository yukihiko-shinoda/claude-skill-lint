---
name: kitchen-sink
description: Exercise every statically-checkable frontmatter field. Use when verifying that the csklint frontmatter schema accepts a fully-populated valid skill.
when_to_use: Only during csklint end-to-end testing.
argument-hint: "[filename] [format]"
arguments: filename format
disable-model-invocation: true
user-invocable: true
allowed-tools:
  - Read
  - Grep
disallowed-tools: Bash
model: inherit
effort: high
context: fork
agent: general-purpose
paths: docs/, src/
shell: bash
---

# Kitchen Sink

Exercise every statically-checkable frontmatter field.
