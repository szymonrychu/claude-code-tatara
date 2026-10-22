---
title: Peer mesh view route
status: todo
repo: claude-code-wrapper
value: Orchestrator can read the peer mesh without holding peers.token
files: [src/claude_code_wrapper/api/peers.py, src/claude_code_wrapper/peer_membership.py, README.md, tests/test_api_peers_view.py]
verify: "uv run pytest tests/test_api_peers_view.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: []
owns: [wrapper-peers-view]
uses: []
model: ""
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

# Peer mesh view route

## Requirement

`GET /v1/peers` (bearer auth, mounted with the other /v1 routes even when peers are disabled) returns the peer mesh view: `{enabled: false}` when `peers` is not configured, otherwise `{enabled: true, self: {instance, url}, members: [{instance, url, sessions, last_seen_at, missed}]}` from the PeerMembership state (peer_membership.py). It never exposes peers.token and is not HMAC-signed (the existing POST /v1/peers/* routes stay HMAC-only). Implemented in api/peers.py (a bearer router separate from the signed one) with a read accessor on PeerMembership. README.md documents the route and the response (test_readme_api enforces it).

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

The signed POST /v1/peers/* routes are mounted only with peers.enabled; the GET must be mounted always. Reuse the bearer dependency in api/auth.py.
