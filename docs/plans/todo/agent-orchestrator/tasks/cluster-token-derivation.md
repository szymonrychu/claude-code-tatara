---
title: cluster token derivation
status: todo
repo: agent-orchestrator
value: "Per-cluster wrapper and peer tokens that every process derives identically, so no token is stored or read back from Kubernetes."
files: [src/agent_orchestrator/tokens.py, tests/test_tokens.py]
verify: "uv run pytest tests/test_tokens.py -q && mise run lint"
depends_on: [settings-model]
owns: [cluster-tokens]
uses: [settings]
model: ""
estimate: 5
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

# cluster token derivation

## Requirement

Token derivation (D7).

- `derive_tokens(master_key: bytes, cluster_id: UUID) -> ClusterTokens`
  - `auth` = hex HMAC-SHA256(master, "auth:" + str(cluster_id))
  - `peer` = hex HMAC-SHA256(master, "peer:" + str(cluster_id))
- Both tokens are 64 characters long, deterministic, and always differ from each other.
- `ClusterTokens` is a frozen dataclass whose `repr` and `str` mask both values (`***`), so a logged object never leaks a token.
- `tokens_for(settings, cluster_id)` reads the key with `settings.require_master_key()`.

## Acceptance conditions

- AC1: the same inputs give the same tokens [evidence: test:tests/test_tokens.py::test_deterministic]
- AC2: auth and peer tokens differ [evidence: test:tests/test_tokens.py::test_auth_and_peer_differ]
- AC3: a different cluster or master key gives different tokens [evidence: test:tests/test_tokens.py::test_depends_on_cluster_and_master]
- AC4: tokens are at least 16 characters (the wrapper's peer minimum) [evidence: test:tests/test_tokens.py::test_length_at_least_16]
- AC5: repr and str mask the values [evidence: test:tests/test_tokens.py::test_repr_masks]

## Files

- `src/agent_orchestrator/tokens.py`
- `tests/test_tokens.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
