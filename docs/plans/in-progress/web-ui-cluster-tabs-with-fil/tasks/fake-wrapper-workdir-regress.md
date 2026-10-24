---
title: fake wrapper workdir regression
status: todo
repo: agent-orchestrator
value: the orchestrator suite is green again on the epic branch
files: [tests/fakes/fake_wrapper.py, tests/test_api_files.py, tests/test_api_terminals.py, tests/test_terminal_relay.py, tests/test_workspace_proxy.py, tests/test_fake_wrapper_contract.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_session_bootstrap.py tests/test_api_files.py tests/test_api_terminals.py tests/test_terminal_relay.py tests/test_workspace_proxy.py tests/test_fake_wrapper_contract.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [terminal-ws-relay]
owns: []
uses: []
model: sonnet
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# fake wrapper workdir regression

## Requirement

Regression from file-proxy-routes: tests/fakes/fake_wrapper.py now reports each session's workdir as a temp directory (`/tmp/fake-wrapper-*/ses_*`) instead of the workdir the caller requested (`/workdir/<workdir or name or sid>`, as before this epic), so tests/test_session_bootstrap.py::test_session_workdir_matches_rendered_workdir_path fails on the epic branch and passes on main.

Keep the reported session workdir exactly as before this epic (the logical path the real wrapper would report), and back the fake's file and terminal routes with a separate real temp directory per session (for example a `backing_dir` field on the fake session, exposed by the existing `FakeWrapper.workdir()` helper), mapping the logical root onto it. The file listing response's absolute `root` stays the reported (logical) workdir, as the real wrapper reports it. Every test that writes files through `FakeWrapper.workdir()` keeps working. Do not change production code under src/.

## Acceptance conditions

- AC1: a session created through the fake reports the requested logical workdir [evidence: test:tests/test_session_bootstrap.py::test_session_workdir_matches_rendered_workdir_path]
- AC2: the file proxy tests list and read files written into the fake's backing directory, and the listing root equals the reported workdir [evidence: test:tests/test_api_files.py]
- AC3: the fake wrapper contract suite stays green [evidence: test:tests/test_fake_wrapper_contract.py]

## Files

- `tests/fakes/fake_wrapper.py`
- `tests/test_api_files.py`
- `tests/test_api_terminals.py`
- `tests/test_terminal_relay.py`
- `tests/test_workspace_proxy.py`
- `tests/test_fake_wrapper_contract.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
