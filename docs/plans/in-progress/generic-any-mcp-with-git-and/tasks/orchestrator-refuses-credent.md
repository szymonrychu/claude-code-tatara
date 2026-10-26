---
title: Orchestrator refuses credentials in plugin source URLs
status: todo
repo: agents-orchestrator
value: Tokens pasted into a plugin source never reach pod logs or caches
files: [src/agents_orchestrator/spec.py, tests/test_spec_any_mcp_sources.py, README.md]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest -q -o addopts=\"\" tests/test_spec_any_mcp_sources.py && mise run lint"
depends_on: [orch-render-plugin-sources]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 656478
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# Orchestrator refuses credentials in plugin source URLs

## Requirement

Security review finding (LOW, accepted as a fix 2026-10-27): a remote source with credentials in the URL, such as `git::https://user:token@github.com/o/r.git`, passes validation, and any-mcp then writes the raw source into install error messages (onStart hook output) and into its plaintext manifest.json. The orchestrator must refuse any remote any_mcp_sources entry (and any source in any_mcp_config) whose URL carries userinfo (a `@` before the host, user or user:password), with the message form `plugin source '<text>': credentials in the URL are not allowed`, never echoing the secret part in the error (redact everything before `@` in the echoed text). The reserved plugin source rendered from settings is unaffected.

## Acceptance conditions

- ac1: any_mcp_sources entries with `user@`, `user:pass@` or `:token@` before the host are refused 422 with the credentials message, and the response does not contain the secret part [evidence: test:tests/test_spec_any_mcp_sources.py::test_source_with_credentials_refused]
- ac2: spec, readme and nomenclature tests and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q -o addopts="" tests/test_spec_any_mcp_sources.py tests/test_readme_api.py tests/test_nomenclature.py && mise run lint]

## Files

- `src/agents_orchestrator/spec.py`
- `tests/test_spec_any_mcp_sources.py`
- `README.md`

## Interfaces

- Same message form as the existing source checks; parity between orchestrator (spec.py remote_source_problem) and web (pluginSource.ts).

## Expected outcome

A source with credentials in its URL is refused with a redacted message.

## Steps

- Red: add the test; run the task's verify; expect failure.
- Green: add the check; run the task's verify on the committed HEAD.

## Notes

- From the phase-5 security review (sonnet), LOW finding accepted as a fix. any-mcp v0.5.0 itself still accepts userinfo for local use; a later any-mcp release may align (noted, not in scope).
- Keep the word cluster out of new text.
