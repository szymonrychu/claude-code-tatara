---
title: baseline facts
status: todo
repo: agents-orchestrator
value: "the migration numbers, plugins version and tool counts the epic builds on are read from main, not assumed"
files: [MEMORY.md]
verify: "grep -q 'Baseline for session-orchestration-mcp' MEMORY.md"
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 544297
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# baseline facts

## Requirement

User settlement B6 (2026-10-27), verbatim: "the build starts only after all three blockers have merged. The first task reads the real migration number, plugins version and tool counts from main and amends the dependent tasks. No assumed numbers in ACs."

Negotiated numbers (mx-34 #469/#470, 2026-10-29), as recorded in design.md Constraints: orchestrator migration 0013 (slash-commands-from-chat ships 0010 and 0012; main ends at 0011), any-mcp-tatara-plugins release v0.6.0 (latest tag v0.5.1), agents-schedule migration 0002 and agents-schedule release v0.2.0 (negotiated, user answer pending).

Build order (accepted queue, 2026-10-29): this epic runs right after slash-commands-from-chat, its only README blocker; hive-decoupling and matrix-connector-agent-initi are done.

Scope: this task changes no behaviour. It runs only after slash-commands-from-chat has merged to main. It reads, on the main branch of each repo (never from memory or an old design):

- agents-orchestrator: the highest file in `src/agents_orchestrator/db/migrations/` (0012 expected, so 0013 free); every call site of `queue.enqueue_message` and every other `INSERT INTO messages` with its file and line (expected: `api/messages.py:post_message` and `api/agent.py:session_send`, the only `INSERT INTO messages` in `db/queue.py:enqueue_message`); the `any_mcp_plugins_ref` default in `settings.py` (v0.5.1 expected).
- any-mcp-tatara-plugins: `len(ALL_TOOLS)` in `orchestration/orchestrator/tests/test_orchestrator_plugin.py` (16 expected, asserted by `test_lists_all_tools`), the version in `orchestration/orchestrator/pyproject.toml` (0.5.1 expected) and the latest tag on origin (v0.5.1 expected).
- agents-schedule: the highest file in `src/agents_schedule/migrations/` (0001 expected, so 0002 free), the version in `chart/agents-schedule/Chart.yaml` and the latest tag on origin (0.1.0 and v0.1.0 expected).

It records them in one dated agents-orchestrator `MEMORY.md` entry headed "Baseline for session-orchestration-mcp". When every value matches the negotiated numbers, the dependent tasks stand as written. When one differs, the orchestrator session stops, proposes the new number on mx-34 and waits for its confirmation (standing rule: numbers and tags are negotiated, never taken silently), then amends the dependent tasks (orch-message-origin, sched-schedule-owner, plugin-orchestration-tools, plugins-release-orch-tools, orch-orchestration-tools-pin, sched-release-0-2-0, helmfile-orchestration-pins) with `ticket.py amend`.

## Acceptance conditions

- ac1: slash-commands-from-chat is merged to the main branch of every repo it touches (its README repos: claude-code-wrapper, agents-orchestrator, agents-web, any-mcp-tatara-plugins, agents-common, agents-webhook, agents-schedule, agents-matrix-connector) before anything else in this epic is dispatched [evidence: judgement:reviewer lists the merged slash-commands-from-chat pull requests with gh pr list --state merged in each repo and confirms each merge commit is on main]
- ac2: MEMORY.md has a dated entry "Baseline for session-orchestration-mcp" naming the highest and next free agents-orchestrator migration, the highest and next free agents-schedule migration, the plugins version and latest origin tag, len(ALL_TOOLS) of the plugin test, the any_mcp_plugins_ref default, the agents-schedule chart version and latest tag, and every enqueue_message call site and INSERT INTO messages with its file [evidence: command:grep -q "Baseline for session-orchestration-mcp" MEMORY.md]
- ac3: each recorded value matches main: the next free migrations are one above the highest file in each directory, the versions are the ones in pyproject.toml and Chart.yaml, the tags the latest on origin [evidence: judgement:reviewer re-derives each value from the repos' main branches with git ls-tree, git grep and git ls-remote --tags and compares it with the entry]
- ac4: the entry states whether every value matches the negotiated numbers (orchestrator migration 0013, schedule migration 0002, plugins v0.6.0 from v0.5.1, schedule v0.2.0 from v0.1.0, 16 plugin tools); on a mismatch the dependent tasks carry the number confirmed on mx-34 and no other [evidence: judgement:reviewer compares the entry with the negotiated numbers in design.md Constraints and, on a mismatch, with the amended task files and the mx-34 confirmation quoted in their Notes]

## Files

- `MEMORY.md`

## Interfaces

- agents-orchestrator `MEMORY.md`: one dated entry "Baseline for session-orchestration-mcp" (values, each with the file or command it came from, and a matches-negotiated yes or no per value).
- No code, test or schema changes.

## Expected outcome

The numbers the epic builds on (orchestrator migration 0013, schedule migration 0002, plugins v0.6.0 from v0.5.1, schedule v0.2.0 from v0.1.0, 16 plugin tools, the two enqueue call sites) are confirmed on main and recorded, or a mismatch is renegotiated on mx-34 before any dependent task is dispatched.

## Steps

No behaviour change, so no red-green cycle (doc-only exception).

- Confirm slash-commands-from-chat merged: `gh pr list --state merged --search slash-commands-from-chat` in each repo of its README; stop and report if any is open.
- In agents-orchestrator: `git fetch origin && git ls-tree --name-only origin/main src/agents_orchestrator/db/migrations/` (expect 0012 highest), `git grep -n "enqueue_message(\|INSERT INTO messages" origin/main -- src` (expect `api/messages.py`, `api/agent.py`, `db/queue.py`), `git grep -n "any_mcp_plugins_ref: str" origin/main -- src` (expect `v0.5.1`).
- In any-mcp-tatara-plugins: count `ALL_TOOLS` in `orchestration/orchestrator/tests/test_orchestrator_plugin.py` (expect 16), read the pyproject version (expect 0.5.1), `git ls-remote --tags origin` (expect v0.5.1 latest).
- In agents-schedule: `git ls-tree --name-only origin/main src/agents_schedule/migrations/` (expect 0001 highest), Chart.yaml version (expect 0.1.0), latest tag (expect v0.1.0).
- Write the MEMORY.md entry; run `grep -q 'Baseline for session-orchestration-mcp' MEMORY.md` (exit 0).

## Notes

- Read from origin/main after `git fetch`, never from a local branch or the slash worktrees.
- A mismatch is not fixed by this task: report it; the orchestrator session renegotiates on mx-34 (standing rule) and amends the dependents.
- immediate-message-delivery-w builds on this epic's 0013 and v0.6.0 (it takes 0014 and v0.7.0); a renegotiated number here moves its numbers too, so the mx-34 proposal names both epics.

- 2026-10-29 amended: staleness refresh: negotiated numbers (mx-34 #469/#470) confirmed, not derived; slash-commands-from-chat the only blocker; ALL_TOOLS count, not a test name; Interfaces, Expected outcome, Steps and Notes filled
