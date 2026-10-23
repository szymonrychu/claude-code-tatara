---
title: session bootstrap
status: in-progress
repo: agent-orchestrator
value: "Every ready agent pod gets exactly one wrapper session, adopted after a restart instead of duplicated."
files: [src/agent_orchestrator/reconciler/sessions.py, src/agent_orchestrator/reconciler/loop.py, src/agent_orchestrator/db/agents.py, tests/test_session_bootstrap.py]
verify: "uv run pytest tests/test_session_bootstrap.py -q && mise run lint"
depends_on: [reconciler-loop, fake-wrapper-contract]
owns: []
uses: [agents-repo, wrapper-client, fake-wrapper, cluster-tokens, kube-api, k8s-render]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-orchestrator-session-bootstrap/agent-orchestrator
branch: agent-orchestrator-session-bootstrap
verified_head: ""
run: agent-orchestrator
provides: []
acs_for_audit: []
process_gaps: []
---

# session bootstrap

## Requirement

Session bootstrap and adoption, run by the reconciler after observing pods (D6).

- Every ready agent without a `session_id` first gets `GET /v1/sessions` with the cluster's derived auth token (D27).
  - Adopt only a session whose state is creating, ready or busy (newest first) with `set_session`.
  - A session that is stopped or failed and has a transcript is resumed with `resume_session` (`POST .../resume`) and then adopted; a resume refusal falls through to the next rule.
  - Otherwise (including stopped or failed without a transcript) call `POST /v1/sessions {name: spec.workdir, workdir: spec.workdir, model, effort}` and record it. The session workdir is the one rendered path of `render.workdir_path(spec)` = `/workdir/<spec.workdir>`, the directory check Jobs use too.
- An agent with a stored `session_id` that the wrapper no longer lists gets `clear_session`, then bootstraps again.
- A `rebootstrap` command (enqueued by the dispatcher when a turn submit answered 404) is claimed in the reconcile tick (`claim_command(['rebootstrap'])`, separate from the restart claim of reconciler-loop): the agent's session is cleared, then bootstrapped again in the same tick, and the command completes.
- 429, 503 and network errors leave the agent without a session, record a message in the cluster status, and retry on the next tick.
- Bootstraps of different agents run concurrently, bounded at 8.

## Acceptance conditions

- AC1: a ready pod without a session gets one created with the spec workdir name [evidence: test:tests/test_session_bootstrap.py::test_creates_session_for_ready_pod]
- AC2: an existing session is adopted instead of creating a second [evidence: test:tests/test_session_bootstrap.py::test_adopts_existing_session]
- AC3: unready pods are not bootstrapped [evidence: test:tests/test_session_bootstrap.py::test_unready_pod_skipped]
- AC4: a wrapper 503 leaves the agent for the next tick with a status message [evidence: test:tests/test_session_bootstrap.py::test_wrapper_unavailable_retries_next_tick]
- AC5: a stored session the wrapper no longer lists is cleared and re-bootstrapped [evidence: test:tests/test_session_bootstrap.py::test_lost_session_rebootstrapped]
- AC6: the cluster's derived auth token is used [evidence: test:tests/test_session_bootstrap.py::test_uses_cluster_auth_token]
- AC7: only creating, ready and busy sessions are adopted; stopped and failed ones are not [evidence: test:tests/test_session_bootstrap.py::test_adopts_only_live_sessions]
- AC8: a stopped session with a transcript is resumed through the resume endpoint and adopted [evidence: test:tests/test_session_bootstrap.py::test_resumes_stopped_session_with_transcript]
- AC9: a failed session without a transcript is not adopted and a new session is created [evidence: test:tests/test_session_bootstrap.py::test_failed_session_without_transcript_gets_new_session]
- AC10: a rebootstrap command clears the session and bootstraps again in the same tick [evidence: test:tests/test_session_bootstrap.py::test_rebootstrap_command_clears_and_bootstraps]
- AC11: the session is created with the workdir name whose path is the rendered workdir_path [evidence: test:tests/test_session_bootstrap.py::test_session_workdir_matches_rendered_workdir_path]

## Files

- `src/agent_orchestrator/reconciler/sessions.py`
- `src/agent_orchestrator/reconciler/loop.py`
- `src/agent_orchestrator/db/agents.py`
- `tests/test_session_bootstrap.py`

## Interfaces

- `agent_orchestrator.reconciler.sessions:bootstrap_sessions(pool, cluster, agents, wrapper_factory, tokens) -> list[str]` (status messages)

## Expected outcome

After reconcile, each ready agent row has the wrapper session id the ingester and dispatcher need.

## Steps

- Write tests/test_session_bootstrap.py with the eleven named tests against FakeWrapper and FakeKube; run it; expect failures.
- Implement sessions.py and call it from Reconciler.reconcile_once.
- Rerun `uv run pytest tests/test_session_bootstrap.py -q`; expect `11 passed`; run `mise run lint`.

## Notes

Session create is synchronous (returns when ready) and `max_sessions` is 1, so a duplicate create returns 429; adopt first. The reconciler, not the API, calls wrappers here (D1).

- 2026-10-23 run agent-orchestrator: dependency-failed on reconciler-loop
