---
title: smoke matrix check
status: in-progress
repo: agents-helmfile
value: "every apply proves the connector is logged in, syncing and serving its API, without touching any chat"
files: [scripts/smoke.sh, tests/test_smoke_script.py, README.md]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_smoke_script.py && shellcheck --severity=error scripts/smoke.sh && uv run ruff check . && uv run ruff format --check ."
depends_on: [helmfile-matrix-releases]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 7
expected_tokens: 538938
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# smoke matrix check

## Requirement

Extend the live smoke with connector checks that never send a Matrix message (design D13). Paths are in code/agents-helmfile.

- `scripts/smoke.sh`, new steps after the webhook steps (release name `MATRIX_RELEASE`, default `agents-matrix-connector`): the `-api` and `-bot` Deployments are Available; through a port-forward to the api Deployment (bypassing its SSO sidecar, as the webhook steps do): `GET /matrix/api/v1/meta` answers `user_id` `@hermes:szymonrichert.pl` and `sync.healthy` true (proves the token, the homeserver path and the sync loop); `POST /rules` a deny rule `{list: deny, kind: user, value: "@smoke-<random>:invalid.example"}`, `GET /rules` lists it, `DELETE /rules/{id}` removes it (the trap deletes it on failure, as the webhook endpoint cleanup does); `GET /rooms` answers 200. The UI `config.json` lists the `matrix` backend.
- The header comment documents the new steps and env.
- `tests/test_smoke_script.py`: the script contains the meta, rules round-trip and rooms checks, cleans the rule up in its trap, and never calls a Matrix send or the homeserver directly.
- `README.md` (helmfile) smoke section mentions the connector checks.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: the smoke checks meta identity and sync health, a rule round trip with cleanup, the rooms list and the UI backend [evidence: test:tests/test_smoke_script.py::test_matrix_connector_checks]
- AC2: the smoke never sends a Matrix message nor calls the homeserver [evidence: test:tests/test_smoke_script.py::test_matrix_smoke_sends_nothing]
- AC3: shellcheck and lint pass [evidence: command:shellcheck --severity=error scripts/smoke.sh && uv run ruff check . && uv run ruff format --check .]

## Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
- `README.md`

## Interfaces

- `scripts/smoke.sh` (run by `mise run smoke`), consumed by apply-smoke-matrix.

## Expected outcome

`mise run smoke` after the apply proves the connector is logged in, syncing and its API works, without touching any chat.

## Steps

- Red: add the two tests to `tests/test_smoke_script.py`. Fails: no matrix steps.
- Green: extend the script and README. Run the verify.

## Notes

- Follow the webhook steps' port-forward and trap pattern in the same script.

- 2026-10-25 amended: revision R1 (user 2026-10-25): the connector takes over Hermes' Matrix user and Facebook account, Hermes scaled to 0; only the Hermes home-channel owner DM is allowed
