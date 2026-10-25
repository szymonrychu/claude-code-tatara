---
title: smoke session mcp check
status: done
repo: agents-helmfile
value: the smoke proves any-mcp is connected in a real agent session
files: [scripts/smoke.sh, tests/test_smoke_script.py]
verify: "uv run pytest tests/test_smoke_script.py -q -p no:cacheprovider && mise run lint"
depends_on: [db-secret-name-from-cnpg, smoke-script]
model: ""
review: ""
verified_head: c45fd6ee57ddfd48145a62a9651b5c3743f26fde
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: 6
actual_tokens: 235329
actual_roles: "impl 3, review 3"
actual_role_tokens: "impl 127584, review 107745"
---

# smoke session mcp check

## Requirement

Live smoke failed on a false check: scripts/smoke.sh runs a bare 'claude mcp list' via kubectl exec, which reads the container's default config and reports no servers. claude-code-wrapper writes MCP servers into each session's own config dir (/sessions/<session_id>/config). Verified live: CLAUDE_CONFIG_DIR=/sessions/<sid>/config claude mcp list shows 'any-mcp: /opt/any-mcp/bin/any-mcp --config /opt/any-mcp/etc/any-mcp.yaml - Connected'. Fix the smoke: find the session config dir in the agent pod (the session id from the orchestrator API agents endpoint for the cluster, or the single /sessions/*/config), run claude mcp list with CLAUDE_CONFIG_DIR set, and require the any-mcp line to say Connected; also assert /opt/any-mcp/bin/any-mcp --version reports 0.1.0. Ignore the ccw entry (its URL env exists only inside the session process).

## Acceptance conditions

- AC1: the smoke checks any-mcp in the session's config dir and requires Connected [evidence: test:tests/test_smoke_script.py::test_smoke_checks_session_config_dir]
- AC2: mise run smoke passes against the live deployment [evidence: command:mise run smoke]

## Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

mise run smoke passes on the live deployment.

What is true and observable when the task is done.

## Steps

- Red: live smoke FAIL any-mcp missing; write the test, see it fail.
- Check the session config dir; run green and the live smoke.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
