---
title: common release 0.4.0
status: todo
repo: agents-common
value: "webhook, schedule and the Matrix connector can pin the agents-common release whose run tracker judges command outcomes"
files: [pyproject.toml, uv.lock, CHANGELOG.md, README.md, tests/test_release.py]
verify: "uv run pytest tests/test_release.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [common-command-outcome]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 629191
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# common release 0.4.0

## Requirement

User decision F2 (2026-10-29), verbatim: "[...] agents-common release v0.4.0 (tag pending mx-34 confirmation; write the task so the orchestrator session pushes the tag after confirmation), then pin bumps in agents-webhook and agents-schedule."

Architect brief, verbatim: "7. `common-release-0-4-0` (a minor release), then two pin tasks".

Design D14 (amended 2026-10-29), verbatim: "agents-common 0.4.0 (minor: `Message.command`, D20) is released by common-release-0-4-0; its tag waits for mx-34's confirmation and the orchestrator session pushes it after that."

Scope (agents-common, mirrors done task common-release-v0-3-0 of epic orchestrator-rename-sessions):
- `pyproject.toml` `version = "0.4.0"`; `uv.lock` refreshed.
- `CHANGELOG.md`: `## v0.4.0` on top: `orchestrator`: `Message.command` (`CommandOutcome`: `state`, `result`, `error`, `turn_id`, `at`; needs agents-orchestrator with `MessageView.command`); `runs.track` judges a command message by its outcome (reasons `command_<error>`, `command_cancelled`); `fake_orchestrator`: `complete_command`, `fail_command`. No breaking change.
- `README.md` install line `agents-common @ git+https://github.com/szymonrychu/agents-common@v0.4.0`; `tests/test_release.py` `INSTALL` and the expected version 0.4.0.
- Release step, run by the orchestrator session (never a subagent): the agents-common PR merges to `main` through the normal PR flow; the session sends version, epic, live and replaces to the leader and waits for mx-34's confirmation; only then it pushes tag `v0.4.0` on the merge commit (irreversible, listed in design.md), confirms `uv pip install "agents-common @ git+https://github.com/szymonrychu/agents-common@v0.4.0"` in a fresh venv, and the pin tasks webhook-common-pin-0-4-0, schedule-common-pin-0-4-0 and mxc-command-outcome start. ac3 is checked by the orchestrator session after the push; the implementer and the reviewer check ac1, ac2 and ac4.

## Acceptance conditions

- ac1: version, CHANGELOG, README install line and package metadata agree on 0.4.0 (updated) [evidence: test:tests/test_release.py::test_versions_agree]
- ac2: CHANGELOG's top section is v0.4.0 and names Message.command [evidence: command:grep -m1 '^## v' CHANGELOG.md | grep -q 'v0.4.0' && grep -q 'Message.command' CHANGELOG.md]
- ac3: (checked by the orchestrator session after mx-34 confirmed and it pushed the tag) tag v0.4.0 exists on origin at the main merge commit [evidence: command:test -n "$(git ls-remote --tags origin v0.4.0)"]
- ac4: the release test and lint pass [evidence: command:uv run pytest tests/test_release.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `pyproject.toml`
- `uv.lock`
- `CHANGELOG.md`
- `README.md`
- `tests/test_release.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
