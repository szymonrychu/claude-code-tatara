---
title: session bootstrap
status: todo
repo: agent-orchestrator
value: "Every ready agent pod gets exactly one wrapper session, adopted after a restart instead of duplicated."
files: [src/agent_orchestrator/reconciler/sessions.py, src/agent_orchestrator/reconciler/loop.py, src/agent_orchestrator/db/agents.py, tests/test_session_bootstrap.py]
verify: "uv run pytest tests/test_session_bootstrap.py -q && mise run lint"
depends_on: [reconciler-loop, fake-wrapper-contract]
owns: []
uses: [agents-repo, wrapper-client, fake-wrapper, cluster-tokens, kube-api]
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

# session bootstrap

## Requirement

Session bootstrap and adoption, run by the reconciler after observing pods (D6).

- Every ready agent without a `session_id` first gets `GET /v1/sessions` with the cluster's derived auth token.
  - When a non-dead session exists, adopt the newest one with `set_session`. This covers `resume_on_start` after a pod restart.
  - Otherwise call `POST /v1/sessions {name: pod_name, workdir: spec.workdir, model, effort}` and record it.
- An agent with a stored `session_id` that the wrapper no longer lists gets `clear_session`, then bootstraps again.
- 429, 503 and network errors leave the agent without a session, record a message in the cluster status, and retry on the next tick.
- Bootstraps of different agents run concurrently, bounded at 8.

## Acceptance conditions

- AC1: a ready pod without a session gets one created with its pod name and workdir [evidence: test:tests/test_session_bootstrap.py::test_creates_session_for_ready_pod]
- AC2: an existing session is adopted instead of creating a second [evidence: test:tests/test_session_bootstrap.py::test_adopts_existing_session]
- AC3: unready pods are not bootstrapped [evidence: test:tests/test_session_bootstrap.py::test_unready_pod_skipped]
- AC4: a wrapper 503 leaves the agent for the next tick with a status message [evidence: test:tests/test_session_bootstrap.py::test_wrapper_unavailable_retries_next_tick]
- AC5: a stored session the wrapper no longer lists is cleared and re-bootstrapped [evidence: test:tests/test_session_bootstrap.py::test_lost_session_rebootstrapped]
- AC6: the cluster's derived auth token is used [evidence: test:tests/test_session_bootstrap.py::test_uses_cluster_auth_token]

## Files

- `src/agent_orchestrator/reconciler/sessions.py`
- `src/agent_orchestrator/reconciler/loop.py`
- `src/agent_orchestrator/db/agents.py`
- `tests/test_session_bootstrap.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
