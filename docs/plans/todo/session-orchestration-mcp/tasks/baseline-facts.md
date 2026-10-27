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

Design Constraints, verbatim: "Every version and migration number that depends on those epics follows a rule, never a guessed number: orchestrator migration: the next free number in `src/agents_orchestrator/db/migrations/` at build time [...]; plugins release: the next minor after the plugins version hive-decoupling leaves pinned in the orchestrator (`ORCH_ANY_MCP_PLUGINS_REF`) at build time; agents-schedule migration: the next free number at build time."

Scope: this task changes no behaviour. It runs only after hive-decoupling, matrix-connector-agent-initi and slash-commands-from-chat have all merged to main. It reads, on the main branch of each repo (never from memory or an old design):

- agents-orchestrator: the highest file in `src/agents_orchestrator/db/migrations/` and so the next free number; every call site of `enqueue_message` and every other insert into `messages` (the main-port post, the service-port post, the session-message path, the command-kind messages slash-commands added, the orchestrator-internal enqueues) with its file; `ORCH_ANY_MCP_PLUGINS_REF` in `settings.py`.
- any-mcp-tatara-plugins: the tool count asserted in `orchestration/orchestrator/tests/test_orchestrator_plugin.py` (the `test_lists_<n>_tools` name) and the version in `orchestration/orchestrator/pyproject.toml`, and the latest tag on origin.
- agents-schedule: the highest file in `src/agents_schedule/migrations/` and so the next free number.

It records them in one dated agents-orchestrator `MEMORY.md` entry headed "Baseline for session-orchestration-mcp". The orchestrator session then amends the dependent tasks (orch-message-origin, sched-schedule-owner, plugin-orchestration-tools, plugins-release-orch-tools, orch-orchestration-tools-pin) with `ticket.py amend`, replacing every `NNNN`, "next free number", "next minor" and "the tools hive-decoupling left" with the real value, and adds the enqueue call-site files to orch-message-origin.

## Acceptance conditions

- ac1: hive-decoupling, matrix-connector-agent-initi and slash-commands-from-chat are all merged to the main branch of the repos they touch before anything else in this epic is dispatched [evidence: judgement:reviewer lists the merged pull requests of the three epics with gh pr list --state merged in agents-orchestrator, any-mcp-tatara-plugins and agents-helmfile and confirms each is on main]
- ac2: MEMORY.md has a dated entry "Baseline for session-orchestration-mcp" naming the next free agents-orchestrator migration number, the next free agents-schedule migration number, the plugins version and latest origin tag, the plugin tool count test name and its count, the ORCH_ANY_MCP_PLUGINS_REF value, and every enqueue call site of messages with its file [evidence: command:grep -q "Baseline for session-orchestration-mcp" MEMORY.md]
- ac3: each recorded number matches main: the migration numbers are one above the highest migration file in the directory, the version is the one in pyproject.toml [evidence: judgement:reviewer re-derives each value from the repos' main branches with ls, grep and git ls-remote --tags and compares it with the entry]
- ac4: orch-message-origin, sched-schedule-owner, plugin-orchestration-tools, plugins-release-orch-tools and orch-orchestration-tools-pin carry no NNNN, no assumed migration number, no assumed version and no assumed tool count after the orchestrator session amended them from the entry [evidence: judgement:reviewer opens the five task files through ticket.py path and finds the real values and no placeholder]

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
