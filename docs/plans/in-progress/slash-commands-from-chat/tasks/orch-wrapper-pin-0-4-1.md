---
title: orch wrapper pin 0.4.1
status: done
repo: agents-orchestrator
value: the orchestrator runs and tests against the wrapper that closes the whitespace bypass and denies the extended list
files: [pyproject.toml, uv.lock, e2e/agent-test.Dockerfile, README.md, tests/fakes/fake_wrapper.py, tests/test_fake_wrapper_contract.py]
verify: "uv run --frozen pytest tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && mise run lint"
depends_on: [wrapper-release-0-4-1, orch-command-outcome]
model: sonnet
review: ""
verified_head: 44416f0dff8b98df22bb7cd00cce2de3b1b723ea
points: 2
expected_minutes: 5
expected_tokens: 546295
points_actual: 2
actual_minutes: 5
actual_tokens: 477684
actual_roles: "impl 4, review 2"
actual_role_tokens: "impl 400151, review 77533"
---

# orch wrapper pin 0.4.1

## Requirement

User decision F1 (2026-10-29), verbatim: "F1 (security): both slash parsers adopt claude's JS whitespace set and skip invisible Cc/Cf characters as the architect specifies, including the ESC hole and the Session.probe guard; wrapper release v0.4.1 (tag approved by the user and mx-34 #432; the orchestrator session pushes it after merge) and an orchestrator pin to it; amend D2."

User decision (2026-10-29 15:26Z/15:29Z), verbatim: "User verbatim 2026-10-29 15:26Z/15:29Z: "Yes" / "all yes" to: (1) extend the wrapper's DEFAULT_COMMAND_DENY with heapdump, plugin, plugins, marketplace, install, import, daemon, schedule, routines, add-dir, export, install-github-app, install-slack-app, design-consent, design-revoke, desktop, remote-env, feedback, bug, extra-usage, usage-credits, terminal-setup, ide, memory (verify each name/alias against claude 2.1.304 at /usr/local/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe; a name that does not exist is reported, not invented); (2) a wrapper session-create override may only extend the deny list, never replace or empty it; (3) keep client ["*"] with the extended deny list. The orchestrator's fake wrapper COMMAND_DENY mirror and docs/examples follow."

Architect brief, verbatim: "3. `wrapper-release-0-4-1`: then `orch-wrapper-pin-0-4-1`, touching the same files as `orch-wrapper-pin-0-4-0`."

Design D14 (amended 2026-10-29), verbatim: "then orch-wrapper-pin-0-4-1 moves the orchestrator pin (same files as orch-wrapper-pin-0-4-0, plus the fake wrapper's deny mirror and the contract test)."

Needs a merged upstream: the claude-code-wrapper fix-round PR merged on `main` and tagged `v0.4.1` (task wrapper-release-0-4-1). The orchestrator amends this task with the merge sha.

Scope (agents-orchestrator):
- `pyproject.toml`: dev dependency `claude-code-wrapper @ git+https://github.com/szymonrychu/claude-code-wrapper@<merge sha>`; `uv lock`.
- `e2e/agent-test.Dockerfile`: `BASE_IMAGE` tag `<sha7>` and `WRAPPER_SHA` `<merge sha>`.
- README `## Images`: recommended agent image `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`.
- `e2e/agent-test.config.yaml` keeps `sessions.commands.client: ["*"]` (user decision 3); unchanged.
- `tests/fakes/fake_wrapper.py`: `COMMAND_DENY` mirrors the pinned wrapper's 51-name `DEFAULT_COMMAND_DENY` (50 plus `app`, the alias of `desktop`, leader-approved under the user's Q1) (comment names the source).
- `tests/test_fake_wrapper_contract.py`: `test_commands_any_name_and_denied` (both legs) also refuses the added names; a Docker-free check pins the mirror to the pinned wrapper's constant.

Merged upstream (2026-10-29): claude-code-wrapper PR #11 merged to `main` as `eed2c3c582827e297eb6d838cb00500db9a27333` (sha7 `eed2c3c`), tagged `v0.4.1`; `build.yaml` green on it (image `harbor.szymonrichert.pl/containers/claude-code-wrapper:eed2c3c`). `<merge sha>` above reads `eed2c3c582827e297eb6d838cb00500db9a27333` and `<sha7>` reads `eed2c3c`.

## Acceptance conditions

- ac1: pyproject, uv.lock, README Images and the agent-test Dockerfile name the same wrapper commit [evidence: test:tests/test_images.py::test_agent_test_dockerfile_matches_dev_dependency]
- ac2: the dev dependency matches the agent image sha [evidence: test:tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha]
- ac3: the pinned wrapper carries the F1 parser and the extended deny list [evidence: command:uv run --frozen python -c "from claude_code_wrapper.session import slash_command; from claude_code_wrapper.config import DEFAULT_COMMAND_DENY; assert slash_command('/exit x') == ('exit', 'x'); assert slash_command('/ex\x1bit') == ('exit', ''); assert {'plugin', 'marketplace', 'routines', 'memory', 'usage-credits'} <= set(DEFAULT_COMMAND_DENY)"]
- ac4: the fake wrapper's COMMAND_DENY equals the pinned wrapper's DEFAULT_COMMAND_DENY, lower-cased (new) [evidence: test:tests/test_fake_wrapper_contract.py::test_fake_deny_mirrors_wrapper_default]
- ac5: on the fake leg, and on the real leg on a Docker host, "plugin", "Marketplace", "routines", "memory" and "usage-credits" are refused 403 command_denied while "context" still queues (updated) [evidence: test:tests/test_fake_wrapper_contract.py::test_commands_any_name_and_denied]
- ac6: the agent-test config still allows every client command [evidence: command:grep -q 'client: \["\*"\]' e2e/agent-test.config.yaml]
- ac7: (Docker host) the real contract leg passes [evidence: command:mise run test:integration]
- ac8: images, render and contract suites and lint pass [evidence: command:uv run --frozen pytest tests/test_images.py tests/test_render.py tests/test_fake_wrapper_contract.py && mise run lint]

## Files

- `pyproject.toml`
- `uv.lock`
- `e2e/agent-test.Dockerfile`
- `README.md`
- `tests/fakes/fake_wrapper.py`
- `tests/test_fake_wrapper_contract.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

- Red: add `test_fake_deny_mirrors_wrapper_default` and the new names in `test_commands_any_name_and_denied`, move the pyproject pin to the merge sha and run `uv lock`; run `uv run --frozen pytest tests/test_images.py tests/test_fake_wrapper_contract.py`: the Dockerfile/README image checks and the mirror test fail.
- Green: update `e2e/agent-test.Dockerfile` (`BASE_IMAGE` sha7, `WRAPPER_SHA`), README `## Images` and `COMMAND_DENY` to the pinned wrapper's list; run the task's verify: passes. Quote the summary line. The real contract leg (ac7) runs in CI on the PR.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-29 amended: wrapper v0.4.1 merged and tagged: merge sha eed2c3c

- 2026-10-29 done
