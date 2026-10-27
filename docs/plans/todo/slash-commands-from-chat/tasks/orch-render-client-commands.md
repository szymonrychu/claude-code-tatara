---
title: orch render client commands
status: todo
repo: agents-orchestrator
value: "every agent's wrapper accepts the orchestrator's commands, the compact button included"
files: [src/agents_orchestrator/k8s/render.py, src/agents_orchestrator/spec.py, README.md, openapi.json, tests/test_render.py, tests/golden/session_single.yaml, tests/golden/session_two_peers.yaml, tests/test_spec_config.py]
verify: "uv run --frozen pytest tests/test_render.py tests/test_spec_config.py tests/test_readme_api.py tests/test_api_config.py && mise run lint"
depends_on: [orch-wrapper-pin-0-4-0]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 963314
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch render client commands

## Requirement

Goal G1 (README), verbatim: "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards."

Design D11, verbatim: "`k8s/render.py` always renders `sessions.commands.client = ["*"]` (the orchestrator is the wrapper's only client; this also repairs the compact button, refused 403 today because the client allowlist was never rendered) and `sessions.commands.agent = spec.wrapper.agent_commands` when set. `spec.wrapper.agent_commands` becomes `list[str]` of names (D2 pattern) or `"*"`, validated by the wrapper's config model through the existing render validation. Needs the 0.4.0 wrapper pin (the 0.3.0 config model rejects `"*"`)."

D2 name pattern (design D2, interrogate item 2, verbatim): "unknown-command regex `^[a-zA-Z0-9_][a-zA-Z0-9:_-]*$`, no length cap".

Discovery fix-as-ac (agents-orchestrator.md), verbatim: "orchestrator never renders wrapper `sessions.commands.client`, so client-origin commands (existing `/agents/{id}/compact`) are refused by the real wrapper (k8s/render.py:133-134; ccw:commands.py:170-176)".

Scope (agents-orchestrator): `k8s/render.py`, `spec.py` (`agent_commands: list[str] | None`, each a D2-pattern name or `"*"`), `README.md` (the `agent_commands` row: names or `*`; the rendered client allowlist), `openapi.json` regenerated (the spec schema changes). The kind e2e case is task orch-e2e-slash-command, which builds on this task (interrogate item 12, design D14).

Tests no longer accurate (named): `tests/golden/session_single.yaml` and `tests/golden/session_two_peers.yaml` pin the rendered wrapper config, which now carries `sessions.commands.client: ["*"]`; they are regenerated. `tests/test_spec_config.py::test_wrapper_value_rules_refused` case `{"agent_commands": ["compact", "rm"]}` asserts `rm` is refused; `rm` is now a valid name, so the case becomes `["compact", "rm -rf"]` (outside the pattern), with `notes.txt` as a second refused case.

## Acceptance conditions

- ac1: every rendered session config has sessions.commands.client ["*"], and agent equal to spec agent_commands when set (new) [evidence: test:tests/test_render.py::test_commands_client_wildcard_rendered]
- ac2: the goldens carry the client allowlist (updated) [evidence: test:tests/test_render.py::test_golden_single_without_peers]
- ac3: the two-peer golden carries it too (updated) [evidence: test:tests/test_render.py::test_golden_two_replicas_with_peers]
- ac4: the rendered config, with agent_commands ["*"] or a free name such as "_x", validates against the pinned wrapper (updated) [evidence: test:tests/test_render.py::test_rendered_ccw_config_validates]
- ac5: agent_commands accepts free names and "*" and refuses "rm -rf" and "notes.txt" (outside the D2 pattern) at wrapper.agent_commands (updated) [evidence: test:tests/test_spec_config.py::test_wrapper_value_rules_refused]
- ac6: openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- ac7: targeted suites and lint pass [evidence: command:uv run --frozen pytest tests/test_render.py tests/test_spec_config.py tests/test_readme_api.py tests/test_api_config.py && mise run lint]

## Files

- `src/agents_orchestrator/k8s/render.py`
- `src/agents_orchestrator/spec.py`
- `README.md`
- `openapi.json`
- `tests/test_render.py`
- `tests/golden/session_single.yaml`
- `tests/golden/session_two_peers.yaml`
- `tests/test_spec_config.py`

## Interfaces

- Rendered wrapper config: `sessions.commands = {"client": ["*"]}` plus `"agent": [...]` when the spec sets `agent_commands`.
- `SessionSpec.wrapper.agent_commands: list[str] | None`.

## Expected outcome

Every agent pod's wrapper accepts client commands from the orchestrator, so chat and superleader commands (and the existing compact button) are no longer refused 403.

## Steps

- Red: add ac1, update the spec case and ac4; run `uv run --frozen pytest tests/test_render.py tests/test_spec_config.py`: they fail.
- Green: render, spec, regenerate the goldens and openapi.json, README; run the task's verify: passes. Quote the summary line.

## Notes

- Changing the rendered config changes the config hash and rolls agent pods on deploy (README `## Images` note); deploy is decided at the gate.
- `tests/test_api_config.py` uses `agent_commands: ["compact", "context"]` and must stay green.
- Depends on orch-wrapper-pin-0-4-0 (the pinned wrapper must accept `"*"`).

- 2026-10-27 amended: interrogate item 2 (agent_commands names follow claude's name regex) and item 12 (the kind e2e case builds on this task, as task orch-e2e-slash-command)
