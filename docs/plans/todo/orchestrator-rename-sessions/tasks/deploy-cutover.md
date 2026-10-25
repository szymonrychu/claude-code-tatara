---
title: deploy cutover
status: todo
repo: agents-helmfile
value: "the live namespace runs agents-orchestrator with the presets carried over, proven by the smoke"
files: [MEMORY.md]
verify: "mise run diff && mise run smoke"
depends_on: [helmfile-smoke-sessions]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# deploy cutover

## Requirement

Move the live namespace to the renamed releases and prove it (design D5, D7, D8, D9; gate Q2, Q4; the irreversible operations are listed in design.md). Paths are in code/agents-helmfile. Applies are run by the orchestrator in the main session, never by a subagent; the implementer runs the read-only probes, `mise run diff` and `mise run smoke`.

- Precondition probes (implementer, read-only; any failure ends the task `blocked` with the output, before any apply): (1) `kubectl -n agents exec agent-orchestrator-db-cluster-1 -c postgres -- psql -U postgres -d agent_orchestrator -Atc "select count(*) from clusters where desired = 'active'"` prints 0, and the preset count is recorded; (2) `kubectl -n agents get secret agents-orchestrator-proxy` exists (user step U1 done; whoCanClear "user: apply the Keycloak client agents-orchestrator, design D9"); (3) the pinned charts exist (`helm show chart` for agents-orchestrator, agents-webhook, agents-web); (4) `mise run diff` shows only the expected changes: old app release removed, the two new releases, agents-webhook and agents-web values and versions; anything else stops the task. End the round with "ready for step 2".
- Step 2 (orchestrator): `mise run apply -- --selector name=agent-orchestrator` (uninstalls the old app).
- Step 3 (orchestrator): `mise run apply -- --selector name=agents-orchestrator-db`; implementer waits until `kubectl -n agents get cluster.postgresql.cnpg.io agents-orchestrator-db-cluster` is healthy and `select count(*) from presets` in `agents_orchestrator` equals the recorded count; a mismatch stops the task (rollback: re-declare the old release, D7).
- Step 4 (orchestrator): `mise run apply`. Implementer: the new app's migrate applied 0004 and 0005 (`select version from schema_migrations` lists 0001-0005, tables `sessions` and `session_leaders` exist), the presets are listed by `GET /api/v1/presets`, `mise run diff` shows no drift, `mise run smoke` exits 0.
- Step 5 (orchestrator): once `kubectl -n agents get certificate agents-orchestrator-tls` is Ready, `kubectl -n agents delete secret agent-orchestrator-tls`.
- `MEMORY.md`: a dated line: cut over to agents-orchestrator `0.1.0-main.<sha7>` with database `agents-orchestrator-db` imported from `agent-orchestrator-db` (preset count), agents-webhook and agents-web pins, the old TLS Secret removed, smoke green (quote its last line). No other file changes.

## Acceptance conditions

- AC1: the preconditions held before any apply [evidence: judgement:the task notes quote the four precondition probe outputs]
- AC2: the imported database keeps the presets and carries the session schema [evidence: judgement:the task notes quote the preset counts of both databases and schema_migrations 0001-0005]
- AC3: the live namespace has no drift from the helmfile after the cutover [evidence: command:mise run diff]
- AC4: the smoke passes on the renamed releases [evidence: command:mise run smoke]
- AC5: MEMORY.md records the cutover [evidence: command:grep -q 'agents-orchestrator-db' MEMORY.md && grep -q 'smoke' MEMORY.md]

## Files

- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
