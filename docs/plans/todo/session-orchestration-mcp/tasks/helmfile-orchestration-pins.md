---
title: helmfile orchestration pins
status: todo
repo: agents-helmfile
value: "agents-helmfile pins the orchestrator, schedule and web builds of this epic and wires the relay"
files: [values/agents-orchestrator/common.yaml, values/agents-schedule/common.yaml, values/agents-web/common.yaml, helmfile.yaml.gotmpl, tests/test_orchestrator_release.py, tests/test_schedule_release.py, tests/test_web_release.py]
verify: "uv run pytest tests/test_orchestrator_release.py tests/test_schedule_release.py tests/test_web_release.py && mise run lint"
depends_on: [helmfile-relay-secrets, orch-orchestration-tools-pin, sched-chart-relay-port, web-created-by, web-schedule-owner, plugins-release-orch-tools]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 936557
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile orchestration pins

## Requirement

README Goal G7, verbatim: "The plugin release, orchestrator pin, agents-helmfile values and live applies ship it, and a live smoke from a flagged throwaway session proves create, edit and delete of a preset, a session and a schedule, the refusals and the audit rows, leaving nothing behind."

Design D15, verbatim: "The orchestrator values set `schedule.url: http://agents-schedule-api-relay:8001`."

Design D17, verbatim: "agents-schedule is pinned by its main build: chart `0.1.0-main.<sha7>` (`scripts/chart-version.sh`) and image `<sha7>`, no schedule tag (my call; the 0.1.0 release pin is replaced). The orchestrator and agents-web are pinned by main sha7 as today; the agent image stays on its release tag (Harbor prunes wrapper sha7 tags)."

Standing user rule (2026-10-27), verbatim from the lead: "Deploy whenever possible: live applies need no approval, so include the agents-helmfile values, apply and live smoke tasks in this epic."

Scope (agents-helmfile): `values/agents-orchestrator/common.yaml` (image tag, `schedule.url`, `ORCH_ANY_MCP_PLUGINS_REF` the new tag), `values/agents-schedule/common.yaml` (image tag, relay on), `values/agents-web/common.yaml` (image tag), `helmfile.yaml.gotmpl` (chart versions), `tests/test_orchestrator_release.py`, `tests/test_schedule_release.py`, `tests/test_web_release.py`.

Tests no longer accurate (named): `tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image` (its `PIN`) and `::test_any_mcp_configured_for_new_sessions` (the plugins ref), `tests/test_schedule_release.py::test_release_declared` and `::test_schedule_pin_matches_release` (they pin chart `0.1.0` and image `6cfa955`), `tests/test_web_release.py::test_web_pin_matches_image` (its pin); each asserts the new pin.

## Acceptance conditions

- ac1: the orchestrator image tag and chart version name the same orchestrator main sha7 (updated) [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- ac2: the orchestrator values set schedule.url to http://agents-schedule-api-relay:8001 and no plaintext schedule token [evidence: test:tests/test_orchestrator_release.py::test_schedule_relay_wired]
- ac3: new sessions install the orchestrator plugin at the tag released by plugins-release-orch-tools (updated) [evidence: test:tests/test_orchestrator_release.py::test_any_mcp_configured_for_new_sessions]
- ac4: the schedule chart version is 0.1.0-main.<sha7> and the image tag the same sha7, and the release still needs its database and the orchestrator (updated) [evidence: test:tests/test_schedule_release.py::test_schedule_pin_matches_release]
- ac5: the schedule release is still declared with its chart, namespace, labels and the orchestrator service token file (updated) [evidence: test:tests/test_schedule_release.py::test_release_declared]
- ac6: the schedule values turn the relay listener on with its hash from relay-token.secrets.yaml and no plaintext hash [evidence: test:tests/test_schedule_release.py::test_relay_listener_enabled]
- ac7: the web image tag and chart version name the same agents-web main sha7 (updated) [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- ac8: the pinned orchestrator sha7 contains orch-orchestration-tools-pin and orch-chart-schedule-relay, the schedule sha7 contains sched-chart-relay-port, the web sha7 contains web-created-by and web-schedule-owner, each on its repo's main with green CI [evidence: judgement:reviewer checks git merge-base --is-ancestor of each task's verified_head against the pinned sha and the CI run of that sha]
- ac9: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_orchestrator_release.py tests/test_schedule_release.py tests/test_web_release.py && mise run lint]

## Files

- `values/agents-orchestrator/common.yaml`
- `values/agents-schedule/common.yaml`
- `values/agents-web/common.yaml`
- `helmfile.yaml.gotmpl`
- `tests/test_orchestrator_release.py`
- `tests/test_schedule_release.py`
- `tests/test_web_release.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
