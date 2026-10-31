# Lean development flow implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: Remove workflows

- Status: done
- Files: `plugins/workbench/workflows/`, `plugins/workbench/skills/heartbeat/`, `plugins/workbench/scripts/hook-evidence.py`, `plugins/workbench/scripts/tests/`, `scripts/harness/fallbacks/`, `scripts/harness/skills_emit.py`, `scripts/tests/`, `plugins/workbench/scripts/run-tests.sh`
- Verify: `pytest scripts/tests -m "not slow" -q && mise run lint && bash plugins/workbench/scripts/run-tests.sh`
- Verified head: 6f72ab793a614d3a938d3406eb1ac798f820049f

#### Requirement

Remove the Workflow runtime and everything that exists only to drive or watch it. Delete `plugins/workbench/workflows/` entirely (plan-execute.js, named-copy.mjs, hook-probe.js, validate-tasks.mjs, ac-lint.mjs, tests/ including harness.mjs), the `heartbeat` skill (`plugins/workbench/skills/heartbeat/`), `plugins/workbench/scripts/hook-evidence.py` and its tests, and the `plan-execute` harness fallback (`scripts/harness/fallbacks/plan-execute/`). In `scripts/harness/skills_emit.py` remove the `CLAUDE_ONLY` set and every rewrite rule that exists for Workflow, plan-execute, heartbeat or Monitor wording; the emitter keeps working for the remaining skills. Update the root tests that enumerate the removed paths (`scripts/tests/test_config_dir_literals.py`, `test_root_config.py`, `test_builtin_worktree_guard.py`, `scripts/tests/harness/`) and remove the workflows branch from `plugins/workbench/scripts/run-tests.sh`. Add a retirement test that pins the removal with `git ls-files`. Do not reword docs or skills and do not touch ticket.py: later tasks own those.

#### Acceptance conditions

- AC0: every `! grep` evidence command below passes when it exits 0, which means no match [evidence: command:true]
- AC1: `git ls-files plugins/workbench/workflows plugins/workbench/skills/heartbeat plugins/workbench/scripts/hook-evidence.py scripts/harness/fallbacks/plan-execute` prints nothing [evidence: command:git ls-files plugins/workbench/workflows plugins/workbench/skills/heartbeat plugins/workbench/scripts/hook-evidence.py scripts/harness/fallbacks/plan-execute]
- AC2: a retirement test asserts AC1 with git ls-files, never the filesystem [evidence: test:scripts/tests/test_retired_workflow.py::test_workflow_runtime_retired]
- AC3: `scripts/harness/skills_emit.py` has no CLAUDE_ONLY set and no rewrite rule mentioning Workflow, plan-execute, heartbeat or Monitor; `grep -n "plan-execute\|heartbeat\|CLAUDE_ONLY\|Workflow" scripts/harness/skills_emit.py` prints nothing [evidence: command:! grep -n "plan-execute\|heartbeat\|CLAUDE_ONLY\|Workflow" scripts/harness/skills_emit.py]
- AC4: `bash plugins/workbench/scripts/run-tests.sh` runs every remaining component and ends with `all green` [evidence: command:bash plugins/workbench/scripts/run-tests.sh]
- AC5: `pytest scripts/tests -m "not slow" -q` and `mise run lint` pass [evidence: command:pytest scripts/tests -m "not slow" -q]

#### Files

- `plugins/workbench/workflows/`
- `plugins/workbench/skills/heartbeat/`
- `plugins/workbench/scripts/hook-evidence.py`
- `plugins/workbench/scripts/tests/`
- `scripts/harness/fallbacks/`
- `scripts/harness/skills_emit.py`
- `scripts/tests/`
- `plugins/workbench/scripts/run-tests.sh`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

1. Read the files named under Files and the tests the ACs name; write the new or changed tests first and run them: they must fail for the expected reason.
2. Implement until the targeted verify command passes; keep every existing test green or update it where it pinned removed behaviour.
3. Run the verify command, paste its real tail in the report, commit on the epic branch, leave the tree clean.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S2: Retire verifier scripts

- Status: done
- Files: `plugins/workbench/scripts/verify-task.py`, `plugins/workbench/scripts/triage.py`, `plugins/workbench/scripts/lib/claude_json.py`, `plugins/workbench/scripts/tests/`, `plugins/workbench/agents/verifier.md`, `plugins/workbench/README.md`, `docs/enterprise.md`, `plugins/workbench/skills/start-development/tests/test_release.py`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only scripts && pytest plugins/workbench/skills/start-development/tests/test_release.py -q && mise run lint`
- Verified head: 94230655c7cc75b77caed68257323627e74a6954

#### Requirement

Retire the independent-verifier tooling that only the plan-execute run called. Delete `plugins/workbench/scripts/verify-task.py`, `plugins/workbench/scripts/triage.py`, `plugins/workbench/scripts/lib/claude_json.py` and their tests and fixtures (`test_verify_task.py`, `test_verify_bounded.py`, `test_triage.py`, `test_claude_json.py`, `fixtures/`), and `plugins/workbench/agents/verifier.md`. Remove the `claude_json` and `verify-task`/`triage` rows from the plugin README script table and from `docs/enterprise.md`, and fix `plugins/workbench/skills/start-development/tests/test_release.py` where it pins those names. The reviewer agent (rewritten in a later task) takes over running the verify command on HEAD and checking acceptance conditions; nothing here replaces the scripts with new code. Add a retirement test with `git ls-files`. Leave estimator.py alone: the ticket task removes it.

#### Acceptance conditions

- AC1: `git ls-files plugins/workbench/scripts/verify-task.py plugins/workbench/scripts/triage.py plugins/workbench/scripts/lib/claude_json.py plugins/workbench/agents/verifier.md plugins/workbench/scripts/tests/fixtures` prints nothing [evidence: command:git ls-files plugins/workbench/scripts/verify-task.py plugins/workbench/scripts/triage.py plugins/workbench/scripts/lib/claude_json.py plugins/workbench/agents/verifier.md plugins/workbench/scripts/tests/fixtures]
- AC2: a retirement test asserts AC1 with git ls-files [evidence: test:plugins/workbench/scripts/tests/test_retired_verifier.py::test_verifier_tooling_retired]
- AC3: `grep -rn "claude_json\|verify-task\|triage.py" plugins/workbench/README.md docs/enterprise.md` prints nothing [evidence: command:! grep -rn "claude_json\|verify-task\|triage.py" plugins/workbench/README.md docs/enterprise.md]
- AC4: `bash plugins/workbench/scripts/run-tests.sh --only scripts` and `pytest plugins/workbench/skills/start-development/tests/test_release.py -q` pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only scripts]

#### Files

- `plugins/workbench/scripts/verify-task.py`
- `plugins/workbench/scripts/triage.py`
- `plugins/workbench/scripts/lib/claude_json.py`
- `plugins/workbench/scripts/tests/`
- `plugins/workbench/agents/verifier.md`
- `plugins/workbench/README.md`
- `docs/enterprise.md`
- `plugins/workbench/skills/start-development/tests/test_release.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

1. Read the files named under Files and the tests the ACs name; write the new or changed tests first and run them: they must fail for the expected reason.
2. Implement until the targeted verify command passes; keep every existing test green or update it where it pinned removed behaviour.
3. Run the verify command, paste its real tail in the report, commit on the epic branch, leave the tree clean.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S3: Ticket drop run commands

- Status: done
- Files: `plugins/workbench/skills/start-development/scripts/ticket.py`, `plugins/workbench/skills/start-development/scripts/ticket_cmds/`, `plugins/workbench/skills/start-development/tests/`, `plugins/workbench/scripts/lib/estimator.py`, `plugins/workbench/scripts/lib/estimator.json`, `plugins/workbench/scripts/tests/test_estimator.py`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint`
- Verified head: 31559e5841b567af391c1516c94f2cd187bc0340

#### Requirement

Remove from `ticket.py` every subcommand that existed for the plan-execute run loop or the approval ledger: `apply-run`, `args`, `continue`, `rule`, `estimate`, `facts`, `decide`, `contract` and `graph`, with their modules under `ticket_cmds/`, their tests (`test_ticket_run.py`, `test_ticket_continue.py`, `test_ticket_continue_launch.py`, `test_ticket_args.py`, `test_ticket_apply_run_fixes.py`, `test_ticket_decide.py`, `test_ticket_estimate.py` and the contract, graph, facts and rule tests), and the estimator (`plugins/workbench/scripts/lib/estimator.py`, `estimator.json`, `scripts/tests/test_estimator.py`). `ticket.py --help` lists none of the removed nine and still lists: slug, new-epic, new-task, check, index, existing, tasks, worktrees, move, stage, review, rename, lint, reap, path, amend, close, questions, roadmap (a later task adds `task`, so the retirement test asserts the absence of the removed nine, never an exact count). Under `ticket_cmds/` the kept modules are `__init__.py`, `amend.py`, `close_cmd.py`, `questions.py` and `roadmap.py`. `new-task` loses `--estimate`; nothing writes `estimate`, `estimate_by`, `actual` or `actual_roles`. Dead helpers that only those commands used go too (the run-dir readers, rulings readers, approvals loaders used only by decide). Keep every other subcommand's behaviour and tests green. Add a retirement test that pins the removed subcommands and files.

#### Acceptance conditions

- AC1: `python3 plugins/workbench/skills/start-development/scripts/ticket.py --help` lists none of apply-run, args, continue, rule, estimate, facts, decide, contract, graph and still lists the 19 kept subcommands [evidence: command:python3 plugins/workbench/skills/start-development/scripts/ticket.py --help]
- AC2: `git ls-files plugins/workbench/skills/start-development/scripts/ticket_cmds plugins/workbench/scripts/lib/estimator.py plugins/workbench/scripts/lib/estimator.json` lists only `__init__.py`, `amend.py`, `close_cmd.py`, `questions.py` and `roadmap.py` under ticket_cmds and no estimator file [evidence: command:git ls-files plugins/workbench/skills/start-development/scripts/ticket_cmds plugins/workbench/scripts/lib/estimator.py plugins/workbench/scripts/lib/estimator.json]
- AC3: a retirement test pins AC1 and AC2 by absence (no exact subcommand count) [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retired_run_loop.py::test_run_loop_commands_retired]
- AC4: `grep -n "estimate\|actual_roles\|apply.run\|rulings" plugins/workbench/skills/start-development/scripts/ticket.py` prints nothing [evidence: command:! grep -n "estimate\|actual_roles\|apply.run\|rulings" plugins/workbench/skills/start-development/scripts/ticket.py]
- AC5: `bash plugins/workbench/scripts/run-tests.sh --only start-development` and `--only scripts` pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development]

#### Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/`
- `plugins/workbench/skills/start-development/tests/`
- `plugins/workbench/scripts/lib/estimator.py`
- `plugins/workbench/scripts/lib/estimator.json`
- `plugins/workbench/scripts/tests/test_estimator.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

1. Read the files named under Files and the tests the ACs name; write the new or changed tests first and run them: they must fail for the expected reason.
2. Implement until the targeted verify command passes; keep every existing test green or update it where it pinned removed behaviour.
3. Run the verify command, paste its real tail in the report, commit on the epic branch, leave the tree clean.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S4: Agents lean roles

- Status: done
- Files: `plugins/workbench/agents/implementer.md`, `plugins/workbench/agents/reviewer.md`, `plugins/workbench/agents/scope-auditor.md`, `plugins/workbench/agents/planner.md`, `plugins/workbench/agents/spec-reviewer.md`, `plugins/workbench/agents/quality-reviewer.md`, `plugins/workbench/skills/start-review/`, `plugins/workbench/skills/start-research/tests/`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only start-review && bash plugins/workbench/scripts/run-tests.sh --only start-research && mise run lint`
- Verified head: b79edfd

#### Requirement

Rewrite the four agents that carry the lean loop, and remove the two the merge makes redundant. Agent files are instructions: every rule kept must earn its place by preventing a failure the records show (silent scope narrowing, parking wording, unverified claims, test weakening, committing outside the tree).

- `implementer.md` (default model sonnet; the task's `model` field overrides per call): implements one task test-first inside the epic's integration worktree, where earlier tasks are already committed on branch `<epic>`. Drop everything about per-task trees, forking from the epic branch, `git merge` of the epic, shared parts (`owns`/`uses`/`provides`/`reimplemented`), approved items and the handoff `readSet`. Keep: work only in the given tree by absolute path, never touch the main checkout or another tree, commit only the task's files, no parking wording, `undelivered` (always a finding) and `discovered` (becomes a new task), red-green-refactor with `tests.red` evidence, run the targeted verify and paste the real tail, commit, leave the tree clean, 150-word summary. Fix mode: the same agent is continued with the review findings (not a fresh agent); judge each finding, reproduce real ones with a failing test first, never weaken or delete an existing test to get green. Context ceiling: commit WIP and return `handoff` with remaining ACs.
- `reviewer.md` (model set per call, sonnet by default): one pass per task that replaces verifier, spec-reviewer and quality-reviewer. Order: (1) `git status --porcelain` is empty and `git rev-parse HEAD` is recorded as `head`; (2) run the task's verify command on that HEAD and paste its tail; (3) check every acceptance condition against the files, a `test:<file>::<name>` ref means that test exists under that name and ran; (4) grep the diff for debt markers and parking wording (TODO, FIXME, "later", "follow-up", "out of scope", "phase 2"); (5) only then quality: the changed code, its callers, its tests, per `skills/start-review/references/review-checklist.md`. Output: `head`, `verifyPassed` with the tail, `unmetAcs` by id with evidence, `findings` (severity, file:line, what, why), `declined`, `cannotVerify`. Read-only. A re-review continues the same reviewer with what changed.
- `scope-auditor.md`: audits an epic at close against the README Goals and Non-goals and every task's acceptance conditions, reading the integrated diff `git diff <base>...<epic>` and the files, never the summaries; includes the cross-task duplicate sweep (the same helper built twice). Drop every mention of the approval ledger, worktrees per task, shared-parts maps and plan-execute return fields. Output: gaps as `{what, where, evidence, suggestedTask}`.
- `planner.md` (default model opus): plans one epic from `{epic, briefs[], userDecisions[]}`: design.md from the template, tasks via `ticket.py new-task` with a verbatim Requirement, ACs with `test:` or `command:` evidence, `files`, a targeted `verify`, `depends_on`, and `model` (opus when the task adds a module or touches more than five files, else sonnet). Sizing rule: one test file's worth of behaviour, at most eight files. Lint with `ticket.py lint <epic>` until ok. Drop approvals.json, contracts, `ticket.py graph`, `facts`, `estimate` and validate-tasks.mjs.
- Delete `spec-reviewer.md` and `quality-reviewer.md`. `review-checklist.md` names only the reviewer, panel-reviewer and start-review as its readers. Update the tests under `skills/start-review/` and `skills/start-research/tests/` that pin agent names, frontmatter or wording, and add a retirement test for the two deleted agents.

#### Acceptance conditions

- AC1: `git ls-files plugins/workbench/agents/spec-reviewer.md plugins/workbench/agents/quality-reviewer.md` prints nothing, pinned by a retirement test [evidence: test:plugins/workbench/skills/start-review/tests/test_agents_lean.py::test_split_reviewers_retired]
- AC2: implementer.md contains none of the backticked field names `owns`, `uses`, `provides`, `reimplemented`, nor the phrases "forks from", "git merge", "readSet", "approved item", and the file keeps the words `undelivered`, `discovered`, `tests.red`, `handoff` [evidence: test:plugins/workbench/skills/start-review/tests/test_agents_lean.py::test_implementer_is_lean]
- AC3: `reviewer.md` orders clean tree and head, verify on HEAD, every AC, debt markers, then quality, and names the output fields head, verifyPassed, unmetAcs, findings, declined, cannotVerify [evidence: test:plugins/workbench/skills/start-review/tests/test_agents_lean.py::test_reviewer_verifies_then_reviews]
- AC4: scope-auditor.md and planner.md contain none of ledger, approvals, plan-execute, validate-tasks, shared-parts; planner.md has `model: opus` and names `ticket.py lint` [evidence: command:! grep -n "ledger\|approvals\|plan-execute\|validate-tasks\|shared-parts" plugins/workbench/agents/scope-auditor.md plugins/workbench/agents/planner.md]
- AC5: `review-checklist.md` mentions none of spec-reviewer, quality-reviewer, plan-execute (its readers line names reviewer, panel-reviewer and start-review) [evidence: command:! grep -n "spec-reviewer\|quality-reviewer\|plan-execute" plugins/workbench/skills/start-review/references/review-checklist.md]
- AC6: `bash plugins/workbench/scripts/run-tests.sh --only start-review` and `--only start-research` pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-review]

#### Files

- `plugins/workbench/agents/implementer.md`
- `plugins/workbench/agents/reviewer.md`
- `plugins/workbench/agents/scope-auditor.md`
- `plugins/workbench/agents/planner.md`
- `plugins/workbench/agents/spec-reviewer.md`
- `plugins/workbench/agents/quality-reviewer.md`
- `plugins/workbench/skills/start-review/`
- `plugins/workbench/skills/start-research/tests/`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

1. Read the files named under Files and the tests the ACs name; write the new or changed tests first and run them: they must fail for the expected reason.
2. Implement until the targeted verify command passes; keep every existing test green or update it where it pinned removed behaviour.
3. Run the verify command, paste its real tail in the report, commit on the epic branch, leave the tree clean.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S5: Ticket lean tasks

- Status: done
- Files: `plugins/workbench/skills/start-development/scripts/ticket.py`, `plugins/workbench/skills/start-development/scripts/ticket_cmds/`, `plugins/workbench/skills/start-development/tests/`, `plugins/workbench/skills/start-development/templates/`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint`
- Verified head: 1b76c81caaba63a2b44315677d8a1fce28265f7e

#### Requirement

Slim the task model to one integration worktree per epic with tasks run sequentially inside it, and give the orchestrator the one status command the loop needs.

1. Legacy keys: the loader tolerates and preserves unknown frontmatter keys on read and write, so the done epics and this epic's own task files (written with the old keys) still load, and `lint` never rejects a legacy key; only what `new-task` writes changes. Task frontmatter written by `new-task` becomes exactly: `title`, `status`, `repo`, `value`, `files`, `verify`, `depends_on`, `model`, `review`, `verified_head`. Remove `owns`, `uses`, `provides`, `estimate`, `estimate_by`, `actual`, `actual_roles`, `worktree`, `branch`, `run` from the template, the loader, the writer and `new-task` (`--owns`, `--uses` go). `templates/task.md`, `templates/epic.md` (drop `## Time`) and `templates/design.md` (drop the Contracts table, the Research inputs ledger wording and every mention of approval ids) follow. `tasks <epic>` stops regenerating the README Time section and emits the tasks in dependency order (a dependency always precedes its dependents).
2. New subcommand `task <epic> <task> --status <todo|in-progress|done|escalated|blocked> [--verified-head <sha>] [--note <text>]`: sets the status (and `verified_head`, appends a dated note line under `## Notes`) and commits as `chore(ticket): <epic> task <task> <status>`. It is how the orchestrator records a task's outcome. Implement it as `ticket_cmds/task_cmd.py`.
3. `worktrees <epic>` creates or reuses only the integration tree (the test for AC4 asserts on the `--help` text and on the trees created) and branch `<epic>` (the per-task mode and `--integration` flag go; `move in-progress` keeps creating the integration tree; `--refresh` keeps fast-forwarding it). `reap --epic <epic>` reaps the integration trees of a done epic; `--task` goes.
4. `close <epic> --verify <cmd>` keeps rebase, verify on the rebased tip, fast-forward, verify on main and `close.json`; the "every done task contained in <epic>" gate and its MERGE lines go, since tasks commit directly on `<epic>`. `stage review` still refuses while a task is not `done`.
5. `lint` no longer reads approvals.json or checks owns/uses. It requires per task: a non-empty Requirement, at least one AC, `verify`, `files`, and `depends_on` entries that resolve to tasks of the epic with no cycle; when design.md exists its Decision coverage maps every `### D<n>` to existing task slugs. `check`, `index`, `existing`, `questions`, `amend`, `rename`, `roadmap`, `path`, `slug`, `stage`, `review`, `move` keep their behaviour; update their tests only where a removed field appears.
Every behaviour above is covered by a test seen red first; existing tests that assert the removed fields are updated, not deleted wholesale.

#### Acceptance conditions

- AC1: a task written by `new-task` has exactly the ten frontmatter keys, and a task file carrying legacy keys (owns, estimate, run) still loads and round-trips title, status, repo, value, files, verify, depends_on, model, review, verified_head [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_task_frontmatter_is_lean]
- AC2: `task <epic> <task> --status done --verified-head <sha>` writes status and verified_head, appends a dated note, and commits as `chore(ticket): <epic> task <task> done`; an unknown status exits 1 [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_task_status.py::test_task_status_sets_fields_and_commits]
- AC3: `tasks <epic>` emits every dependency before its dependents [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_files.py::test_tasks_are_in_dependency_order]
- AC4: `worktrees <epic>` creates only the integration tree; `--integration`, per-task trees and `reap --task` are gone from `--help` [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_worktrees_refresh.py::test_worktrees_creates_integration_tree_only]
- AC5: `close` has no MERGE-line gate: with every task done it rebases, verifies and fast-forwards; it still refuses (exit 4) on a failed verify [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_close_cmd.py::test_close_without_containment_gate]
- AC6: `lint` passes an epic with no approvals.json and fails one whose task lacks an AC, lacks `verify`, or has a dependency cycle, and one whose design.md Decision coverage names a missing task [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_lint.py::test_lint_lean_rules]
- AC7: `grep -n "owns\|uses\|provides\|approvals\|estimate\|## Time" plugins/workbench/skills/start-development/scripts/ticket.py plugins/workbench/skills/start-development/templates/*.md` prints nothing [evidence: command:! grep -n "owns\|uses\|provides\|approvals\|estimate\|## Time" plugins/workbench/skills/start-development/scripts/ticket.py plugins/workbench/skills/start-development/templates/task.md plugins/workbench/skills/start-development/templates/epic.md plugins/workbench/skills/start-development/templates/design.md]
- AC8: `bash plugins/workbench/scripts/run-tests.sh --only start-development` passes [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development]

#### Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/`
- `plugins/workbench/skills/start-development/tests/`
- `plugins/workbench/skills/start-development/templates/`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

1. Read the files named under Files and the tests the ACs name; write the new or changed tests first and run them: they must fail for the expected reason.
2. Implement until the targeted verify command passes; keep every existing test green or update it where it pinned removed behaviour.
3. Run the verify command, paste its real tail in the report, commit on the epic branch, leave the tree clean.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S6: Start-development rewrite

- Status: done
- Files: `plugins/workbench/skills/start-development/SKILL.md`, `plugins/workbench/skills/start-development/references/`, `plugins/workbench/skills/start-development/templates/record.md`, `plugins/workbench/skills/start-development/tests/`, `plugins/workbench/agents/record-writer.md`, `plugins/workbench/README.md`, `plugins/workbench/.claude-plugin/plugin.json`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint`
- Verified head: 06d6a93

#### Requirement

Rewrite `start-development` for the lean flow. `SKILL.md` is at most 150 lines and the references directory holds at most seven files; the phase list is: 0 size (lean or full), 1 discovery (optional lenses, each recorded as ran or skipped), 2 design doc, 3 tasks via the planner plus `ticket.py lint` and the builder check (one general-purpose agent on sonnet reads README, design.md and tasks and returns only the questions it still needs answered), THE GATE, 4 execute (invoke `epic-run`, see below; that skill is added by the next task and no test here checks the skill exists), 5 epic review (whole-diff `start-review`, one `scope-auditor`, the one full-suite run, security check when the diff touches that surface), 6 close or merge (`ticket.py close` in meta mode, the MR path in component mode), 7 record.

The gate message: epic README and design.md paths, the project brief, the task table (id, title, value, files, depends_on, model), the lenses that ran or were skipped, the builder check's remaining questions as one numbered batch with a recommended answer each, every irreversible operation, and "Approve, or tell me what to change". Approving the message approves the README goals and every task's acceptance conditions; there is no approval ledger. Everything after the gate runs unattended to merge.

Phase 4 text: the loop that `epic-run` runs, written once here and referenced from that skill: claim the epic (`ticket.py move <epic> in-progress`, which creates the integration tree), then for each task in `ticket.py tasks <epic>` order: dispatch one `workbench:implementer` (model from the task, in the background) with the task file verbatim and the tree path; on return dispatch one `workbench:reviewer`; while it reports unmet ACs or findings, continue the same implementer with SendMessage, then the same reviewer, at most two fix rounds; then `ticket.py task <epic> <task> --status done --verified-head <head>`, or `--status escalated` after the cap with the open findings as the note, and go on with tasks that do not depend on it. The orchestrator plans other epics while dispatches run; it never implements a task itself and never merges a tree itself. After the last task: phases 5 to 7. Rules: a task's `undelivered` entry is a finding, `discovered` becomes a new task in the same epic via `new-task`, `escalated` tasks are judged by the orchestrator (fix with a sharper requirement, or `interrogate` once), and the epic cannot close while a task is not `done`.

References: keep and update `tickets.md` (the lean layout, subcommands, frontmatter, state machines, writer rule; fold `task-fields.md` in), `worktrees.md` (one integration tree per epic), `non-negotiables.md` (half its length; drop plan-execute return fields), `hooks.md` (what the hooks enforce), `merge-hosts.md`, `user-run-steps.md`, `workbench-config.md`. Delete `phase-4-execute.md`, `phases-1-3.md`, `phases-5-7.md`, `run-handback.md`, `approvals.md`, `agents.md`, `builder-check.md`, `mode-flags.md`, `multi-epic.md`, `plan-inputs.md`, `task-fields.md`. `templates/record.md` becomes a short record (what was asked, what shipped, per task: status, verified head, review rounds, verification tail; rulings; what is not pushed) and `agents/record-writer.md` fills it from the task files, git log and the orchestrator's notes with no plan-execute return. Update the plugin `README.md` (flow, agents, scripts, verification sections) and `plugin.json` description. Update `tests/` here (including `test_skill_size.py`, which reads `references/phase-4-execute.md` today) so every doc test pins the lean wording and no test mentions a removed file, command or return field; add a test pinning the deleted references.

#### Acceptance conditions

- AC1: SKILL.md has at most 150 lines and `references/` at most seven files, with the eleven named references absent from `git ls-files` [evidence: test:plugins/workbench/skills/start-development/tests/test_lean_flow_docs.py::test_skill_is_lean]
- AC2: SKILL.md names the phases 0 to 7, the gate items, `epic-run`, `ticket.py task`, `SendMessage`, the two-round cap and the sequential dependency order, and contains no `plan-execute`, `Workflow(`, `heartbeat`, `approvals.json`, `verifier`, `forward-merge`, `land`, `rulings` or `apply-run` [evidence: test:plugins/workbench/skills/start-development/tests/test_lean_flow_docs.py::test_skill_describes_lean_loop]
- AC3: outside `tests/` directories (the retirement tests name the retired words on purpose), `grep -rn "plan-execute\|heartbeat\|approvals.json\|apply-run\|forwardMerged\|verify-task" plugins/workbench/skills/start-development plugins/workbench/agents/record-writer.md plugins/workbench/README.md plugins/workbench/.claude-plugin/plugin.json` prints nothing [evidence: command:! grep -rn --exclude-dir=tests "plan-execute\|heartbeat\|approvals.json\|apply-run\|forwardMerged\|verify-task" plugins/workbench/skills/start-development plugins/workbench/agents/record-writer.md plugins/workbench/README.md plugins/workbench/.claude-plugin/plugin.json]
- AC4: `templates/record.md` and record-writer.md mention no plan-execute return (`return value`, `forwardMerged`, `plan-execute`), and record-writer.md names task files and git log as its inputs [evidence: command:! grep -n "return value\|forwardMerged\|plan-execute" plugins/workbench/skills/start-development/templates/record.md plugins/workbench/agents/record-writer.md]
- AC5: `bash plugins/workbench/scripts/run-tests.sh --only start-development` passes [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development]

#### Files

- `plugins/workbench/skills/start-development/SKILL.md`
- `plugins/workbench/skills/start-development/references/`
- `plugins/workbench/skills/start-development/templates/record.md`
- `plugins/workbench/skills/start-development/tests/`
- `plugins/workbench/agents/record-writer.md`
- `plugins/workbench/README.md`
- `plugins/workbench/.claude-plugin/plugin.json`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

1. Read the files named under Files and the tests the ACs name; write the new or changed tests first and run them: they must fail for the expected reason.
2. Implement until the targeted verify command passes; keep every existing test green or update it where it pinned removed behaviour.
3. Run the verify command, paste its real tail in the report, commit on the epic branch, leave the tree clean.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S7: Epic-run skill

- Status: done
- Files: `plugins/workbench/skills/epic-run/`, `plugins/workbench/skills/start-research/tests/`
- Verify: `bash plugins/workbench/scripts/run-tests.sh --only epic-run && bash plugins/workbench/scripts/run-tests.sh --only start-research && mise run lint`
- Verified head: de33424

#### Requirement

Add the `epic-run` skill (`plugins/workbench/skills/epic-run/SKILL.md`): execute one already-planned epic from any session. Description for the skill index: "Execute one planned epic: claim it, run its tasks in dependency order through one implementer and one reviewer each with at most two fix rounds, audit scope, close. Use after the gate of start-development or to run an epic planned in another session." The body is short and refers to the phase 4 text of `start-development/SKILL.md` for the loop rather than restating it; it adds only the entry conditions (`ticket.py lint <epic>` ok, epic in todo or in-progress, a clean green main), the per-task dispatch prompt shapes (implementer: the task file verbatim plus the tree path and the `cd`; reviewer: the task file, the tree path, the task's commit range), the status command after each task, what to do with `escalated`, `discovered` and `undelivered`, and the exit (phases 5 to 7 of start-development, one closing message of three lines). Add a structure test like the other skills' tests (frontmatter name and description, the referenced files exist, the forbidden words plan-execute, heartbeat, Workflow(, approvals absent) and register the skill in `plugins/workbench/skills/start-research/tests/test_start_skills_structure.py`, which enumerates skills (it lists `skills/heartbeat/SKILL.md` today; remove-workflows handles that line).

#### Acceptance conditions

- AC1: `plugins/workbench/skills/epic-run/SKILL.md` exists with frontmatter `name: epic-run` and the description above, and names start-development phase 4, `ticket.py tasks`, `ticket.py task`, `workbench:implementer`, `workbench:reviewer` and `SendMessage` [evidence: test:plugins/workbench/skills/epic-run/tests/test_epic_run_structure.py::test_skill_structure]
- AC2: the file contains none of plan-execute, heartbeat, `Workflow(`, approvals [evidence: test:plugins/workbench/skills/epic-run/tests/test_epic_run_structure.py::test_no_retired_words]
- AC3: `bash plugins/workbench/scripts/run-tests.sh --only epic-run` and `--only start-research` pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only epic-run]

#### Files

- `plugins/workbench/skills/epic-run/`
- `plugins/workbench/skills/start-research/tests/`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

1. Read the files named under Files and the tests the ACs name; write the new or changed tests first and run them: they must fail for the expected reason.
2. Implement until the targeted verify command passes; keep every existing test green or update it where it pinned removed behaviour.
3. Run the verify command, paste its real tail in the report, commit on the epic branch, leave the tree clean.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S8: Skills wording

- Status: done
- Files: `plugins/workbench/skills/`, `plugins/workbench/hooks/`, `plugins/workbench/rules/concise-orchestrator.md`, `plugins/workbench/agents/`
- Verify: `bash plugins/workbench/scripts/run-tests.sh && mise run lint`
- Verified head: 606b059

#### Requirement

Remove every remaining reference to the retired machinery from the plugin outside start-development: in `plugins/workbench/skills/` (interrogate, start-review, start-discovery, worktree-create, worktree-merge, epic-create, epic-move, epic-task-create, epic-worktrees-remove, handoff, release, pullrequests-*, research-*, init, template-update and any other), `plugins/workbench/hooks/` (the bash-output-filter docstring) and `plugins/workbench/rules/concise-orchestrator.md` ("heartbeat reply"). The words that must be gone from every file outside a `tests/` directory (the retirement tests name them on purpose), as the proof: plan-execute, heartbeat, hook-probe, verify-task, approvals ledger, approvals.json, apply-run, `ticket.py continue`, `ticket.py rule`, forward-merge, per-task worktree, named copy, Workflow tool. Where a sentence described a plan-execute behaviour (interrogate "a task plan-execute escalated", start-review "a plan-execute run on the full path", worktree-create/merge per-task trees, epic-move and epic-worktrees-remove task trees), rewrite it for the lean loop (an escalated task of epic-run; the implementer in the epic's integration tree; one integration tree per epic). Each skill's own tests keep passing; where a test pinned the old wording, update it. Nothing else changes in those skills.

#### Acceptance conditions

- AC1: outside `tests/` directories, `grep -rniE --exclude-dir=tests "plan-execute|heartbeat|hook-probe|verify-task|approvals ledger|approvals\.json|apply-run|ticket\.py continue|ticket\.py rule|forward-merge|per-task worktree|named copy|Workflow tool" plugins/workbench/skills plugins/workbench/hooks plugins/workbench/rules plugins/workbench/agents` prints nothing [evidence: command:! grep -rniE --exclude-dir=tests "plan-execute|heartbeat|hook-probe|verify-task|approvals ledger|approvals\.json|apply-run|ticket\.py continue|ticket\.py rule|forward-merge|per-task worktree|named copy|Workflow tool" plugins/workbench/skills plugins/workbench/hooks plugins/workbench/rules plugins/workbench/agents]
- AC2: a test pins AC1 over those four directories, skipping `tests/` directories [evidence: test:plugins/workbench/hooks/tests/test_no_retired_words.py::test_plugin_has_no_retired_words]
- AC3: `bash plugins/workbench/scripts/run-tests.sh` ends with `all green` [evidence: command:bash plugins/workbench/scripts/run-tests.sh]

#### Files

- `plugins/workbench/skills/`
- `plugins/workbench/hooks/`
- `plugins/workbench/rules/concise-orchestrator.md`
- `plugins/workbench/agents/`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

1. Read the files named under Files and the tests the ACs name; write the new or changed tests first and run them: they must fail for the expected reason.
2. Implement until the targeted verify command passes; keep every existing test green or update it where it pinned removed behaviour.
3. Run the verify command, paste its real tail in the report, commit on the epic branch, leave the tree clean.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S9: Root docs and rules

- Status: done
- Files: `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/architecture.md`, `docs/harnesses.md`, `docs/enterprise.md`, `scripts/tests/`
- Verify: `pytest scripts/tests -m "not slow" -q && mise run lint`
- Verified head: 8990c8e

#### Requirement

Bring the root documents and their tests to the lean flow. `AGENTS.md`: ground rule 1 says implementation goes through `epic-run` (one implementer and one reviewer per task, two fix rounds, one scope audit per epic) and never hand-rolled beyond that; ground rule 4 drops the heartbeat sentence and keeps the 10-minute bound with the background Agent notification as the wake signal; the Claude-only block in `CLAUDE.md` drops the plan-execute and heartbeat lines and says `epic-run` dispatches agents in the background. Root `README.md`: "The autonomous run to merge" describes epic-run, "Parallel epics, background runs, heartbeats" becomes "Parallel epics and background runs" without the heartbeat skill, "Resume after an escalation" names `ticket.py task` and `epic-run`. `docs/architecture.md` and `docs/harnesses.md`: remove the Workflow row and the plan-execute fallback paragraphs; other harnesses run the same loop with their own subagent facility. `docs/enterprise.md` only if a reference remains after retire-verifier-scripts. Regenerate the rules block with `mise run harness-setup` after `concise-orchestrator.md` changed (skills-wording task) and commit the regenerated output. Update `scripts/tests/test_agents_md.py`, `scripts/tests/init_engine/test_project_files.py` and `scripts/tests/harness/fixtures/tree/AGENTS.md` so they pin the new wording; the init engine must still produce an AGENTS.md whose ground rules match this one. No other root file changes.

#### Acceptance conditions

- AC1: `grep -rniE "plan-execute|heartbeat|Workflow tool|Workflow scripts|approval ledger" AGENTS.md CLAUDE.md README.md docs/architecture.md docs/harnesses.md docs/enterprise.md` prints nothing [evidence: command:! grep -rniE "plan-execute|heartbeat|Workflow tool|Workflow scripts|approval ledger" AGENTS.md CLAUDE.md README.md docs/architecture.md docs/harnesses.md docs/enterprise.md]
- AC2: AGENTS.md ground rule 1 names `epic-run`, one implementer and one reviewer per task, two fix rounds and one scope audit per epic [evidence: test:scripts/tests/test_agents_md.py::test_ground_rule_one_names_epic_run]
- AC3: after the task's commit, `mise run harness-setup` leaves the tree unchanged (the generated block is committed) [evidence: command:mise run harness-setup && git status --porcelain]
- AC4: `pytest scripts/tests -m "not slow" -q` and `mise run lint` pass [evidence: command:pytest scripts/tests -m "not slow" -q]

#### Files

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/architecture.md`
- `docs/harnesses.md`
- `docs/enterprise.md`
- `scripts/tests/`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

1. Read the files named under Files and the tests the ACs name; write the new or changed tests first and run them: they must fail for the expected reason.
2. Implement until the targeted verify command passes; keep every existing test green or update it where it pinned removed behaviour.
3. Run the verify command, paste its real tail in the report, commit on the epic branch, leave the tree clean.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

## Files to delete

none recorded in the epic format

## Final verify

`mise run test && mise run lint`

## After merge

none
