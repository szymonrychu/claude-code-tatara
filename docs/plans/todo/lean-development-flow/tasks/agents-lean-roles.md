---
title: Agents lean roles
status: todo
repo: workbench
value: "Model quality and instructions replace orchestration machinery; these four files are where scope protection now lives"
files: [plugins/workbench/agents/implementer.md, plugins/workbench/agents/reviewer.md, plugins/workbench/agents/scope-auditor.md, plugins/workbench/agents/planner.md, plugins/workbench/agents/spec-reviewer.md, plugins/workbench/agents/quality-reviewer.md, plugins/workbench/skills/start-review/, plugins/workbench/skills/start-research/tests/]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-review && bash plugins/workbench/scripts/run-tests.sh --only start-research && mise run lint"
depends_on: [retire-verifier-scripts]
owns: []
uses: []
model: opus
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

# Agents lean roles

## Requirement

Rewrite the four agents that carry the lean loop, and remove the two the merge makes redundant. Agent files are instructions: every rule kept must earn its place by preventing a failure the records show (silent scope narrowing, parking wording, unverified claims, test weakening, committing outside the tree).

- `implementer.md` (default model sonnet; the task's `model` field overrides per call): implements one task test-first inside the epic's integration worktree, where earlier tasks are already committed on branch `<epic>`. Drop everything about per-task trees, forking from the epic branch, `git merge` of the epic, shared parts (`owns`/`uses`/`provides`/`reimplemented`), approved items and the handoff `readSet`. Keep: work only in the given tree by absolute path, never touch the main checkout or another tree, commit only the task's files, no parking wording, `undelivered` (always a finding) and `discovered` (becomes a new task), red-green-refactor with `tests.red` evidence, run the targeted verify and paste the real tail, commit, leave the tree clean, 150-word summary. Fix mode: the same agent is continued with the review findings (not a fresh agent); judge each finding, reproduce real ones with a failing test first, never weaken or delete an existing test to get green. Context ceiling: commit WIP and return `handoff` with remaining ACs.
- `reviewer.md` (model set per call, sonnet by default): one pass per task that replaces verifier, spec-reviewer and quality-reviewer. Order: (1) `git status --porcelain` is empty and `git rev-parse HEAD` is recorded as `head`; (2) run the task's verify command on that HEAD and paste its tail; (3) check every acceptance condition against the files, a `test:<file>::<name>` ref means that test exists under that name and ran; (4) grep the diff for debt markers and parking wording (TODO, FIXME, "later", "follow-up", "out of scope", "phase 2"); (5) only then quality: the changed code, its callers, its tests, per `skills/start-review/references/review-checklist.md`. Output: `head`, `verifyPassed` with the tail, `unmetAcs` by id with evidence, `findings` (severity, file:line, what, why), `declined`, `cannotVerify`. Read-only. A re-review continues the same reviewer with what changed.
- `scope-auditor.md`: audits an epic at close against the README Goals and Non-goals and every task's acceptance conditions, reading the integrated diff `git diff <base>...<epic>` and the files, never the summaries; includes the cross-task duplicate sweep (the same helper built twice). Drop every mention of the approval ledger, worktrees per task, shared-parts maps and plan-execute return fields. Output: gaps as `{what, where, evidence, suggestedTask}`.
- `planner.md` (default model opus): plans one epic from `{epic, briefs[], userDecisions[]}`: design.md from the template, tasks via `ticket.py new-task` with a verbatim Requirement, ACs with `test:` or `command:` evidence, `files`, a targeted `verify`, `depends_on`, and `model` (opus when the task adds a module or touches more than five files, else sonnet). Sizing rule: one test file's worth of behaviour, at most eight files. Lint with `ticket.py lint <epic>` until ok. Drop approvals.json, contracts, `ticket.py graph`, `facts`, `estimate` and validate-tasks.mjs.
- Delete `spec-reviewer.md` and `quality-reviewer.md`. `review-checklist.md` names only the reviewer, panel-reviewer and start-review as its readers. Update the tests under `skills/start-review/` and `skills/start-research/tests/` that pin agent names, frontmatter or wording, and add a retirement test for the two deleted agents.

## Acceptance conditions

- AC1: `git ls-files plugins/workbench/agents/spec-reviewer.md plugins/workbench/agents/quality-reviewer.md` prints nothing, pinned by a retirement test [evidence: test:plugins/workbench/skills/start-review/tests/test_agents_lean.py::test_split_reviewers_retired]
- AC2: `grep -n "owns\|uses\|provides\|reimplemented\|forks from\|git merge\|readSet\|approved item" plugins/workbench/agents/implementer.md` prints nothing, and the file keeps the words `undelivered`, `discovered`, `tests.red`, `handoff` [evidence: test:plugins/workbench/skills/start-review/tests/test_agents_lean.py::test_implementer_is_lean]
- AC3: `reviewer.md` orders clean tree and head, verify on HEAD, every AC, debt markers, then quality, and names the output fields head, verifyPassed, unmetAcs, findings, declined, cannotVerify [evidence: test:plugins/workbench/skills/start-review/tests/test_agents_lean.py::test_reviewer_verifies_then_reviews]
- AC4: `grep -n "ledger\|approvals\|plan-execute\|worktrees\b.*task\|shared-parts" plugins/workbench/agents/scope-auditor.md plugins/workbench/agents/planner.md` prints nothing; planner.md has `model: opus` and names `ticket.py lint` [evidence: command:grep -c "ledger\|approvals\|plan-execute\|validate-tasks\|shared-parts" plugins/workbench/agents/scope-auditor.md plugins/workbench/agents/planner.md]
- AC5: `review-checklist.md` lists only reviewer, panel-reviewer and start-review as readers [evidence: command:grep -n "spec-reviewer\|quality-reviewer\|plan-execute" plugins/workbench/skills/start-review/references/review-checklist.md]
- AC6: `bash plugins/workbench/scripts/run-tests.sh --only start-review` and `--only start-research` pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-review]

## Files

- `plugins/workbench/agents/implementer.md`
- `plugins/workbench/agents/reviewer.md`
- `plugins/workbench/agents/scope-auditor.md`
- `plugins/workbench/agents/planner.md`
- `plugins/workbench/agents/spec-reviewer.md`
- `plugins/workbench/agents/quality-reviewer.md`
- `plugins/workbench/skills/start-review/`
- `plugins/workbench/skills/start-research/tests/`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
