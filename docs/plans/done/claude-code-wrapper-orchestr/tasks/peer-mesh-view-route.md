---
title: Peer mesh view route
status: done
repo: claude-code-wrapper
value: Orchestrator can read the peer mesh without holding peers.token
files: [src/claude_code_wrapper/api/peers.py, src/claude_code_wrapper/peer_membership.py, README.md, tests/test_api_peers_view.py]
verify: "uv run pytest tests/test_api_peers_view.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: ""
review: ""
verified_head: 892610075f08ff303a9f9b8481777d143a0c53e7
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: 3
actual_tokens: 463866
actual_roles: "impl 2, review 1"
actual_role_tokens: "impl 303856, review 160010"
---

# Peer mesh view route

## Requirement

`GET /v1/peers` (bearer auth) returns the peer mesh view: `{enabled: false}` when `peers` is not enabled, otherwise `{enabled: true, self: {instance, url}, members: [{instance, url, sessions, last_seen_at, missed}]}`. It is mounted unconditionally: api/app.py:79-85 mounts the HMAC `peers.router` only when `cfg.peers.enabled`, so the new bearer route lives in a separate router included in the `v1` router (api/app.py:73-78) regardless, and answers `{enabled: false}` itself when `manager.peers is None` (manager.py:302). Fields come from peers.py: `self` from `PeerService.instance` and `.url` (peer_service.py:78-79); each member from `Member` (peers.py:60-66) fields `instance`, `url`, `sessions` (tuple of `PeerSession` {session_id, name, cwd}, peers.py:53), `missed` and `last_seen` (a monotonic float, converted to ISO `last_seen_at`, null when None); `reachable` is not exposed. It never exposes peers.token and is not HMAC-signed (the existing POST /v1/peers/* routes stay HMAC-only). Implemented in api/peers.py (a bearer router separate from the signed one) with a read accessor on the MemberTable. README.md documents the route and the response (test_readme_api enforces it).

## Acceptance conditions

- AC1: peers disabled returns {enabled: false} [evidence: test:tests/test_api_peers_view.py::test_disabled_returns_enabled_false]
- AC2: enabled returns self and members with sessions, last_seen_at and missed [evidence: test:tests/test_api_peers_view.py::test_enabled_lists_members]
- AC3: requires the bearer token and never leaks peers.token [evidence: test:tests/test_api_peers_view.py::test_requires_bearer_and_hides_token]
- AC4: README documents GET /v1/peers [evidence: test:tests/test_readme_api.py::test_every_public_route_documented]

## Files

- `src/claude_code_wrapper/api/peers.py`
- `src/claude_code_wrapper/peer_membership.py`
- `README.md`
- `tests/test_api_peers_view.py`

## Interfaces

api/peers.py bearer route GET /v1/peers; peer_membership.py snapshot accessor. Contract wrapper-peers-view.

## Expected outcome

GET /v1/peers with the bearer returns the mesh view; peers off returns {enabled: false}.

## Steps

- Write tests/test_api_peers_view.py; run it and see it fail (404).
- Add a bearer router in api/peers.py and a read accessor on PeerMembership; update README.md.
- Run `uv run pytest tests/test_api_peers_view.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check .`.

## Notes

The signed POST /v1/peers/* routes are mounted only with peers.enabled (api/app.py:79-85); the GET must be mounted always. Reuse the bearer dependency in api/auth.py (require_auth, applied to `v1`). Monotonic `last_seen` must be converted to wall-clock using the table clock offset at read time.
