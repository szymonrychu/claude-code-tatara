---
title: origin allowlist
status: todo
repo: agent-orchestrator
value: no web page from another origin can open a shell through a LAN browser
files: [src/agent_orchestrator/settings.py, src/agent_orchestrator/api/origin.py, src/agent_orchestrator/api/app.py, README.md, e2e/values-kind.yaml, tests/test_origin.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_origin.py tests/test_settings.py && mise run lint"
depends_on: []
owns: [origin-allowlist]
uses: []
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# origin allowlist

## Requirement

Add the mandatory Origin allowlist to the orchestrator api (design D5, user Q7), test-first.

- `Settings.allowed_origins` (`ORCH_ALLOWED_ORIGINS`), a comma-separated `CsvList` of origins (`scheme://host[:port]`, lower-cased, no path, no trailing slash; an invalid entry fails settings validation with the field name), default empty.
- New `src/agent_orchestrator/api/origin.py`:
  - a pure ASGI middleware added in `api/app.py` that, for every `websocket` scope, reads the `Origin` header: absent passes; `null` or not in `allowed_origins` is refused with `websocket.close` code 1008 before accept. An empty list refuses every Origin-bearing upgrade. It runs together with the existing `SourceAllowlist`, which is unchanged.
  - a FastAPI dependency `require_allowed_origin` that applies the same rule to an HTTP request and raises `ApiError` 403 `forbidden_origin`; the terminal routes (task terminal-proxy-routes) attach it to their POST and DELETE.
- `e2e/values-kind.yaml` sets `ORCH_ALLOWED_ORIGINS` to `http://127.0.0.1:18080,http://localhost:18080` (the e2e port-forward).
- README (`code/agent-orchestrator/README.md`): a `## Configuration` row for `ORCH_ALLOWED_ORIGINS` (default empty, read by api); in `## Security` the Origin rule (why: browsers apply no CORS to WebSocket upgrades), including that deployments serving the UI must list the UI origin; in `### Ingress` that WebSocket routes need `nginx.ingress.kubernetes.io/proxy-read-timeout` and `proxy-send-timeout` raised (3600, as agents-helmfile already sets) through `ingress.annotations`, and that the UI pings every 20 s; `forbidden_origin` (403) added to the API error code list.

## Acceptance conditions

- AC1: ORCH_ALLOWED_ORIGINS parses a CSV of origins, normalises case and rejects a value with a path [evidence: test:tests/test_origin.py::test_settings_parse_and_validate]
- AC2: a WebSocket upgrade with an unlisted or null Origin is closed with 1008 before accept, a listed Origin and a missing Origin pass [evidence: test:tests/test_origin.py::test_websocket_origin_rule]
- AC3: an empty allowlist refuses every Origin-bearing upgrade [evidence: test:tests/test_origin.py::test_empty_list_fails_closed]
- AC4: require_allowed_origin answers 403 forbidden_origin for an unlisted Origin on HTTP and passes a missing one [evidence: test:tests/test_origin.py::test_http_dependency]
- AC5: the setting is documented in the README Configuration table [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_settings.py]
- AC6: README Security and Ingress describe the Origin rule and the WebSocket timeouts [evidence: doc-section:README.md#Ingress]
- AC7: targeted suites and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_origin.py tests/test_settings.py && mise run lint]

## Files

- `src/agent_orchestrator/settings.py`
- `src/agent_orchestrator/api/origin.py`
- `src/agent_orchestrator/api/app.py`
- `README.md`
- `e2e/values-kind.yaml`
- `tests/test_origin.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
