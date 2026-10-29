---
title: orchestration smoke script
status: todo
repo: agents-helmfile
value: one command proves the orchestration tools live end to end and leaves nothing behind
files: [scripts/orchestration-smoke.sh, scripts/lib/smoke-common.sh, mise.toml, README.md, tests/test_orchestration_smoke_script.py, tests/test_mise_tasks.py]
verify: "uv run pytest tests/test_orchestration_smoke_script.py tests/test_mise_tasks.py && mise run lint"
depends_on: [orch-schedule-relay, sched-relay-routes, helmfile-relay-secrets]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 8
expected_tokens: 1828146
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orchestration smoke script

## Requirement

README Goal G7, verbatim: "The plugin release, orchestrator pin, agents-helmfile values and live applies ship it, and a live smoke from a flagged throwaway session proves create, edit and delete of a preset, a session and a schedule, the refusals and the audit rows, leaving nothing behind."

Design D18, verbatim: "`scripts/orchestration-smoke.sh` (mise task `orchestration-smoke`), separate from `scripts/smoke.sh`. It creates a throwaway alone session with `session_orchestration` true through the public API, posts it a user message (main port, origin `user`) that keeps the turn open (the agent runs a bounded `sleep`), waits until that turn is current, and from the session's pod (its own `ORCH_AGENT_*` env, never printed) calls the orchestration routes: `me`, presets list, preset create and update, a refused `privilege_escalation` preset, session create from the own preset, overview, session delete, schedule create (disabled, `0 3 * * *`), update, runs and delete, preset delete, and the actions list; after the turn ends it checks one write is refused `not_user_turn`. Each wait has its own deadline; a trap deletes everything the script created through the public API on success, failure and interrupt."

Retro proposals, verbatim: "for smoke-script tasks the reviewer checks every timeout or deadline against the AC and the MEMORY claim" and "any task that shells out to an external tool must have its AC cite a captured real output sample, and the reviewer checks fakes against it."

Scope (agents-helmfile): new `scripts/orchestration-smoke.sh` (env `RELEASE`, `NAMESPACE`, `ORCH_SMOKE_PRESET` or the default preset as the base spec, `ORCH_SMOKE_TIMEOUT_S` per wait, `ORCH_SMOKE_HOLD_S` for the held turn, `SMOKE_LOCAL_PORT`), new mise task `orchestration-smoke`, README (names the task and what it creates and deletes), `tests/test_orchestration_smoke_script.py` with kubectl and curl fakes, `tests/test_mise_tasks.py`.

## Acceptance conditions

- ac1: against fakes the script creates the flagged throwaway session, holds a user turn, runs every D18 step in order from the session's pod, prints each step's status and the ids, and exits 0 [evidence: test:tests/test_orchestration_smoke_script.py::test_happy_path]
- ac2: the privilege_escalation preset and the write after the held turn ends must be refused with those codes, and any other answer exits 1 naming the step [evidence: test:tests/test_orchestration_smoke_script.py::test_refusals_required]
- ac3: the actions list must show an ok row for every write step and the privilege_escalation row, else exit 1 [evidence: test:tests/test_orchestration_smoke_script.py::test_actions_checked]
- ac4: every wait (pod Ready, turn current, turn ended, each delete) has its own ORCH_SMOKE_TIMEOUT_S deadline, and a timeout exits 1 naming the step [evidence: test:tests/test_orchestration_smoke_script.py::test_each_wait_has_its_own_deadline]
- ac5: the trap deletes every session, preset and schedule the script created, and only those, through the public API on success, failure and interrupt, kills its port-forwards, and a stale port-forward on its port is killed first [evidence: test:tests/test_orchestration_smoke_script.py::test_cleanup_only_own_objects]
- ac6: no token or ORCH_AGENT_* value is printed [evidence: test:tests/test_orchestration_smoke_script.py::test_no_secrets_printed]
- ac7: the fakes replay bodies with the shapes of the orchestrator README Orchestration section and the committed agents-schedule openapi-relay.json [evidence: judgement:reviewer compares the fake bodies with the agents-orchestrator README and agents-schedule openapi-relay.json on their main]
- ac8: the mise task orchestration-smoke runs the script and README names it [evidence: test:tests/test_mise_tasks.py::test_readme_names_every_task]
- ac9: the targeted tests and lint (ruff, shellcheck, gitleaks) pass [evidence: command:uv run pytest tests/test_orchestration_smoke_script.py tests/test_mise_tasks.py && mise run lint]

## Files

- `scripts/orchestration-smoke.sh`
- `scripts/lib/smoke-common.sh`
- `mise.toml`
- `README.md`
- `tests/test_orchestration_smoke_script.py`
- `tests/test_mise_tasks.py`

## Interfaces

- `mise run orchestration-smoke` (env above); output one `orchestration-smoke: <step> <status> <id>` line per step, ending `orchestration-smoke: OK`.
- Throwaway names: `orch-smoke-<ts>` (session and caller preset base), `orch-smoke-<ts>-p` (owned preset), `orch-smoke-<ts>-s` (owned session), `orch-smoke-<ts>` (schedule, disabled).

## Expected outcome

One command proves the orchestration tools live end to end and leaves nothing behind but audit rows.

## Steps

- Red: write `tests/test_orchestration_smoke_script.py` (fakebin kubectl and curl, as `tests/test_smoke_script.py` does); run it: fails.
- Green: the script, mise task, README; run the task's verify. Quote the summary line.

## Notes

- Source `scripts/lib/smoke-common.sh` like `scripts/smoke.sh` and `scripts/chat-smoke.sh` do (`SMOKE_LOG_PREFIX`, `log`, `fail`, `now`, `agent_call` for the pod exec with the pod's own `ORCH_AGENT_*` env, `stale_pids`, `kill_stale_port_forward`); extend the lib only for a helper both other scripts could use, and keep `tests/test_smoke_script.py` and `tests/test_chat_smoke_script.py` green.
- `tests/test_smoke_script.py` and `tests/test_chat_smoke_script.py` are the fakebin patterns for the new test.
- The held turn: the user message asks the agent to run `sleep $ORCH_SMOKE_HOLD_S` and then reply ok; the script waits until the message's turn is the agent's current turn before the first write, and until it ends before the not_user_turn check.
- The owned session is created from the owned preset (alone, 1 replica) and deleted before the owned preset.
- Never print `ORCH_AGENT_TOKEN`; read it inside the pod exec only.
