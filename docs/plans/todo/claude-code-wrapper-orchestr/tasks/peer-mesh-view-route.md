---
title: Peer mesh view route
status: todo
repo: claude-code-wrapper
value: Orchestrator can read the peer mesh without holding peers.token
files: [src/claude_code_wrapper/api/peers.py, src/claude_code_wrapper/peer_membership.py, README.md, tests/test_api_peers_view.py]
verify: "uv run pytest tests/test_api_peers_view.py tests/test_readme_api.py -q && mise run lint"
depends_on: []
owns: [wrapper-peers-view]
uses: []
model: ""
estimate: 39
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
