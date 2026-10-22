---
title: discard hook and export
status: todo
repo: agent-orchestrator
value: Discarding a cluster deletes everything while an optional hook still receives the full chat history first
files: [src/agent_orchestrator/db/export.py, src/agent_orchestrator/reconciler/discard_hook.py, src/agent_orchestrator/reconciler/loop.py, tests/test_discard_hook.py, README.md]
verify: "uv run pytest tests/test_discard_hook.py -q && mise run lint"
depends_on: [check-jobs]
owns: []
uses: [schema-v1, pg-fixture, settings, cluster-spec, kube-api]
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

# discard hook and export

## Requirement

The pre-discard hook and the history export (D15). Discard deletes everything. When a hook is configured, the cluster's full history is exported to it first.

`db/export.py`: `export_cluster_history(conn, cluster_id) -> AsyncIterator[str]` yields JSONL lines, each one JSON object with a `kind` field:
- one `cluster` record (id, slug, spec, created_at)
- then the `agent`, `message`, `turn`, `command`, `check` and `event` records, each kind in id order (turns in started_at order)

It streams with a server-side cursor, never loading the history into memory. Timestamps are ISO 8601 UTC.

`reconciler/discard_hook.py`: `run_discard_hook(hook, cluster, lines, timeout) -> HookResult(ok, reason)`. The hook to use is `cluster.spec.discard_hook_url`, else `settings.discard_hook()`.
- Command (settings only): run through `sh -c` with the JSONL on stdin and `ORCH_CLUSTER_ID` and `ORCH_CLUSTER_SLUG` in its environment. Exit 0 is success. A non-zero exit or a timeout is a failure whose reason carries the exit code and a bounded stderr tail. On timeout the process group is killed.
- Webhook: an httpx streaming `POST` of the JSONL with `Content-Type: application/x-ndjson`, `X-Orch-Cluster-Id` and `X-Orch-Cluster-Slug`. A 2xx is success; any other status or a connection error is a failure.
- Both are bounded by `settings.discard_hook_timeout_seconds`.

`reconciler/loop.py`: `Reconciler.pre_discard(cluster)` (the hook point from reconciler-loop) becomes:
- No hook configured, or the cluster status already records `discard_hook_delivered`: return True.
- Otherwise run the hook over `export_cluster_history`.
  - On success, write `status.discard_hook_delivered = <db now()>` and return True.
  - On failure, write `status.discard_hook_failed = <reason>` and `status.discard_hook_next_at`, then return False, so nothing is deleted. The hook is retried on later reconciles with `settings.retry_delay_seconds(n)` backoff on the database clock, where n is the failure count kept in the status.
- An error in one cluster's hook never stops other clusters reconciling.

README.md gains `## Discard`. It covers:
- what a discard deletes
- the hook sources and their precedence
- the JSONL record kinds
- the command and webhook contracts
- at-least-once delivery
- that a failing hook holds the discard

## Acceptance conditions

- AC1: the export streams one cluster record then agents, messages, turns, commands, checks and events in id order as valid JSONL [evidence: test:tests/test_discard_hook.py::test_export_jsonl_kinds_and_order]
- AC2: a command hook receives the JSONL on stdin with ORCH_CLUSTER_ID and ORCH_CLUSTER_SLUG, and the discard proceeds on exit 0 [evidence: test:tests/test_discard_hook.py::test_command_hook_gets_export_then_discard_proceeds]
- AC3: a webhook hook receives an application/x-ndjson POST with the cluster headers, and the spec URL wins over the settings hook [evidence: test:tests/test_discard_hook.py::test_webhook_hook_and_spec_precedence]
- AC4: a failing or timed-out hook deletes nothing, records discard_hook_failed and is retried with backoff [evidence: test:tests/test_discard_hook.py::test_failed_hook_blocks_deletion_and_retries]
- AC5: once delivered, a reconciler restart does not send the export again and the discard completes, deleting the row and its history [evidence: test:tests/test_discard_hook.py::test_delivered_hook_not_resent_and_history_deleted]
- AC6: with no hook configured the discard deletes everything without exporting [evidence: test:tests/test_discard_hook.py::test_no_hook_discards_directly]
- AC7: README documents the discard [evidence: doc-section:README.md#Discard]

## Files

- `src/agent_orchestrator/db/export.py`
- `src/agent_orchestrator/reconciler/discard_hook.py`
- `src/agent_orchestrator/reconciler/loop.py`
- `tests/test_discard_hook.py`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
