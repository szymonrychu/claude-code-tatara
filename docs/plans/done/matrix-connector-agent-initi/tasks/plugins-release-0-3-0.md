---
title: plugins release 0.2.0
status: done
repo: any-mcp-tatara-plugins
value: the chat tools ship as plugins release v0.2.0 that the orchestrator can pin
files: [orchestration/orchestrator/pyproject.toml, uv.lock, orchestration/orchestrator/README.md, tests/test_source_install.py]
verify: "uv run pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint"
depends_on: [plugin-chat-tools]
model: sonnet
review: ""
verified_head: 073328ede436c782f832988ab8d0723e1b4378f8
points: 2
expected_minutes: 5
expected_tokens: 545296
points_actual: 1
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# plugins release 0.2.0

## Requirement

README Goal, verbatim: "An agent (session leader) can send a message to the user's Matrix chat at any time, including a chat it never received a message from (initiate), through MCP tools, not only as the final answer of a chat-started turn."

Design D13, verbatim: "any-mcp-tatara-plugins releases v0.2.0 (the orchestrator session pushes the tag after merge)."

Release number swap (design B2 and Irreversible operations, user decision 2026-10-27): this epic releases any-mcp-tatara-plugins v0.1.0 on top of v0.1.0, and slash-commands-from-chat releases v0.2.0 after it.

Repo README `## Releases`, verbatim: "Releases are `vX.Y.Z` tags on `main`; pin `?ref=` to a release tag. Nothing is published beyond the tag."

Scope (any-mcp-tatara-plugins):
- `orchestration/orchestrator/pyproject.toml`: version `0.2.0`; `uv lock` updates `uv.lock`.
- `orchestration/orchestrator/README.md`: the example source pins `?ref=v0.2.0`.
- `tests/test_source_install.py::test_orchestrator_distribution_metadata` is no longer accurate (named): on main it pins `0.1.0`; it asserts `0.2.0`.
- Release step, run by the orchestrator session (never a subagent) once this repo's PR is merged to `main` with green CI: `git tag v0.2.0 <merge sha> && git push origin v0.2.0` (irreversible, listed in design.md). ac3 is checked by the orchestrator after that push, not by the implementer or reviewer.

## Acceptance conditions

- ac1: the plugin's pyproject and installed metadata say 0.2.0 (updated) [evidence: test:tests/test_source_install.py::test_orchestrator_distribution_metadata]
- ac2: the plugin README example pins the new release and no older one [evidence: command:grep -q "ref=v0.2.0" orchestration/orchestrator/README.md && ! grep -q "ref=v0.1.0" orchestration/orchestrator/README.md]
- ac3: (checked by the orchestrator session after it pushed the tag) tag v0.2.0 exists on origin at the merge commit [evidence: command:test -n "$(git ls-remote --tags origin v0.2.0)"]
- ac4: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint]

## Files

- `orchestration/orchestrator/pyproject.toml`
- `uv.lock`
- `orchestration/orchestrator/README.md`
- `tests/test_source_install.py`

## Interfaces

- Distribution `any-mcp-tatara-orchestrator` version `0.2.0`; git tag `v0.2.0` on the `main` merge commit.

## Expected outcome

The orchestrator plugin with the chat tools is released as tag v0.2.0, so the orchestrator can pin it.

## Steps

- Confirm the plugins' newest tag on origin is `v0.1.0` and `v0.2.0` does not exist yet (`git ls-remote --tags origin`); stop and report if not.
- Red: change `test_orchestrator_distribution_metadata` to 0.2.0; run `uv run pytest tests/test_source_install.py::test_orchestrator_distribution_metadata`: fails.
- Green: bump the plugin pyproject, `uv lock`, the plugin README example; run the task's verify: passes. Quote the summary line.
- After the merge (orchestrator session): wait for CI green on the merge commit, `git tag v0.2.0 <merge sha> && git push origin v0.2.0`, then check ac3.

## Notes

- Dependency-bump TDD exception for the version values; the metadata test is the guard.
- `tests/test_source_install.py::test_orchestrator_plugin_installs_from_sources` fails in this pod with git 2.39 (`--end-of-options`); it is environmental (discovery sec 5) and CI is the gate for it.

- 2026-10-28 amended: plugins release number swap (design B2): this epic releases v0.2.0 on top of v0.1.0; slash-commands releases v0.3.0

- 2026-10-28 done: PR #2 merged 4506e70, main CI 40736029763 green, tag v0.2.0 pushed (ac3 ok)

- 2026-10-28 actuals: no agent records
