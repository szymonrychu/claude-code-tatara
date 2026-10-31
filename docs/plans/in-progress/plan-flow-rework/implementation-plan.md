# Plan flow replaces epics and tasks implementation plan

## Agreed rung

Rung 3 (complete) of plan.md, items 1.1 to 3.5, with the gate modifications listed under plan.md
Agreed scope. Nothing outside those items is built; anything found on the way goes to the
implementer's `discovered` list and into retro.md Recommendations.

## Approach

Meta mode: one tree for the superrepo, branch `plan-flow-rework`, base `main`.

Bootstrap, because this plan runs before its own tooling exists:

- The orchestrator commits this plan dir on main (`docs(plan): plan-flow-rework plan`), then
  creates the tree from the main checkout with
  `python3 plugins/workbench/skills/worktree-create/scripts/create.py --integration --name plan-flow-rework`.
  `<tree>` below is the path it prints (`<configdir>/worktrees/plan-flow-rework`).
- Chunks 1 to 4 run sequentially in `<tree>`, each one `workbench:implementer` with the model
  named on the chunk, prompted with this file's path and its chunk number, first line
  `[wb plan-flow-rework/impl]`.
- The review runs once after chunk 4: a general-purpose agent (sonnet) told to follow
  `<tree>/plugins/workbench/agents/reviewer.md` (the new one, from chunk 3), at most two fix rounds
  by continuing the same agents. On pass it writes
  `docs/plans/in-progress/plan-flow-rework/retro.md` in the main checkout.
- The merge: `workbench:worktree-merger` (sonnet) runs
  `python3 plugins/workbench/skills/worktree-merge/scripts/merge.py --name plan-flow-rework --base main --keep --verify 'mise run test && mise run lint'`
  (the prompt overrides its "no merge script against main" rule for this one bootstrap merge).
- Then the After merge steps, by one general-purpose agent (sonnet) in the main checkouts.

Rules for every chunk:

- Commit per step: `<type>(<scope>): S<n> <title>`. Test first; a deletion-only step names the
  "deletion pinned by a retirement test" exception and its pin.
- Verify commands run from `<tree>/plugins/workbench` unless they start with `cd`. Quote the
  summary line.
- Each chunk ends with `cd <tree> && mise run test && mise run lint` green. A test that pins old
  behaviour or old doc text the chunk removed is updated or deleted in that chunk (say which and
  why); nothing else from a later chunk is pulled forward.
- No personal paths or the ros2 project name in any file under `plugins/` (`mise run lint`
  personal check). Plain ASCII, no em dashes, no arrows.

## Chunk 1: ticket.py core for plans (model: opus)

### S1: Plan, implementation-plan and retro templates

- Files: `plugins/workbench/skills/start-development/templates/plan.md` (new),
  `templates/implementation-plan.md` (new), `templates/retro.md` (rewrite),
  `skills/start-development/tests/test_templates.py` (rewrite).
- Covers: 1.2, 3.2.
- Test first: test_templates.py pins, per template, the H1 and the H2 headings in order exactly as
  plan.md Design lists them; plan.md frontmatter keys exactly `title, repos, created, owner, rung`;
  the step field names of implementation-plan.md (`Files`, `Covers`, `Test first`, `Change`,
  `Verify`); retro.md has no `retro:generated` markers and its Recommendations names the three
  lists. Drop the old design/record/builder-check/record-writer assertions (retired in S5 and
  chunk 3). Run it red.
- Change: write the three templates; each section carries a one-line instruction in place of
  content, like the current templates. This plan's own plan.md and implementation-plan.md are the
  worked example of the shape.
- Verify: `pytest skills/start-development/tests/test_templates.py`

### S2: Plan core commands: slug, new, check, path, rename, old-format refusal

- Files: `skills/start-development/scripts/ticket.py`, `tests/test_ticket_files.py` (rewrite),
  `tests/test_ticket_check.py` (rewrite), `tests/test_ticket_naming.py` (rewrite),
  `tests/ticket_repo_helpers.py`, `tests/conftest.py`.
- Covers: 3.1.
- Test first: `new --title T [--repos a,b] [--force]` writes `todo/<slug>/plan.md` from the
  template with title, repos, created set and commits exactly it as `chore(ticket): <plan> new`;
  a near duplicate (similarity >= 0.6 over title plus What and why) in todo or in-progress exits 3
  and writes nothing, `--force` overrides, one in done is a note only; `check --title` lists near
  duplicates with exit 0; `path <plan> plan|implementation|retro|close` prints the absolute path in
  the current phase; `rename` works in todo only (slug freeze); a slug whose branch or worktree
  name is taken is refused, naming the holder; a plan dir holding README.md and no plan.md makes
  every command that reads plans exit 1 with `old epic format under <dir>; run ticket.py migrate
  --all`; frontmatter round-trip `dump(load(x)) == x`; `require_main_checkout` and
  `commit_ticket_change` behave as today. Run red.
- Change: rework ticket.py's core around plan dirs (`find_plan`, `resolve_plan`, `scan` of plans
  only). Keep the restricted frontmatter parser, slugify, the git guard and the commit helper.
- Verify: `pytest skills/start-development/tests/test_ticket_files.py skills/start-development/tests/test_ticket_check.py skills/start-development/tests/test_ticket_naming.py`

### S3: Claim and worktrees

- Files: `scripts/ticket.py`, `tests/test_ticket_move.py` (rewrite, claim part),
  `tests/test_ticket_integration.py`, `tests/test_ticket_worktrees_refresh.py`.
- Covers: 3.1.
- Test first: `move <plan> in-progress [--owner]` refuses a plan outside todo, a plan whose
  frontmatter `rung` is empty, and a plan without implementation-plan.md (each refusal names the
  reason, nothing moves); on success it creates or reuses the tree(s) through worktree-create's
  integration function (meta: one superrepo tree; component: one per `repos` entry that is a
  `code/` submodule, forked from its tracked branch; meta mixed with component refused), git-mvs
  the dir to in-progress, sets `owner`, commits `chore(ticket): <plan> move in-progress`; a
  repeat claim reuses the tree; `worktrees <plan> [--refresh] [--base]` behaves as today for plans.
  Run red.
- Change: claim and worktree code read `repos` from plan.md frontmatter instead of task files.
- Verify: `pytest skills/start-development/tests/test_ticket_move.py skills/start-development/tests/test_ticket_integration.py skills/start-development/tests/test_ticket_worktrees_refresh.py`

### S4: Done, close and reap

- Files: `scripts/ticket.py`, `scripts/ticket_cmds/close_cmd.py`, `tests/test_ticket_move.py`
  (done part), `tests/test_ticket_close.py`, `tests/test_ticket_close_cmd.py`.
- Covers: 3.1.
- Test first: `close <plan> --verify <cmd> [--base main]` refuses unless the plan is in-progress
  and retro.md exists; meta mode rebases `<plan>` onto main in the tree, verifies there,
  fast-forwards main only on pass, verifies main, writes close.json (`plan`, `base`, `baseBefore`,
  `baseAfter`, `planTip`, `integrationVerify`, `mainVerify`, `at`), then moves the dir to done and
  commits close.json, retro.md and the move as `chore(ticket): <plan> close`, then sweeps the tree
  and branch; a failed verify is exit 4 and nothing moves; a rerun after success is a no-op that
  prints close.json; component mode prints that it closes through the MR and moves nothing.
  `move <plan> done [--base]` refuses without retro.md or when a plan branch is not contained in
  its trunk (ancestor, else patch equivalent), else moves, commits with retro.md and sweeps.
  `reap --plan <plan> [--dry-run] [--base]` as today for done plans. Run red.
- Change: replace the review-verdict gate with the retro.md gate; fold the move to done into
  close; rename epic to plan in output keys and messages.
- Verify: `pytest skills/start-development/tests/test_ticket_move.py skills/start-development/tests/test_ticket_close.py skills/start-development/tests/test_ticket_close_cmd.py`

### S5: Retire the task machinery

- Files: `scripts/ticket.py`, `scripts/ticket_cmds/__init__.py`,
  `tests/test_ticket_retired_run_loop.py` renamed to `tests/test_ticket_retired_subcommands.py`,
  `tests/test_ticket_cmd_modules.py`, plus every file listed under Files to delete for chunk 1.
- Covers: 2.2, 3.1.
- Test first: test_ticket_retired_subcommands.py pins that `new-epic`, `new-task`, `tasks`,
  `task`, `amend`, `questions`, `lint`, `stage`, `review`, `actuals`, `deltas`, `retro`,
  `roadmap`, `index` and `existing` are not ticket.py subcommands (argparse exit 2), keeps the old
  run-loop pins, and asserts `git ls-files` is empty for every chunk 1 deletion. Run red.
- Change: delete the subcommands, their modules, helpers (task parsing, dependency order, AC
  parsing, points and calibration, overlap counting, index) and the `calibration` and
  `agent_usage` imports; delete the four old templates and the five thin epic-* wrapper skills
  that call the removed subcommands. Old `migrate` goes too (rewritten in chunk 2). Exception
  named: deletion pinned by a retirement test.
- Verify: `pytest skills/start-development/tests/test_ticket_retired_subcommands.py skills/start-development/tests/test_ticket_cmd_modules.py`

### S6: Chunk 1 green

- Files: only tests the chunk's removals broke.
- Covers: 3.1.
- Test first: none (verification step).
- Change: fix each failing assertion that pins removed behaviour (for example epic-* dirs in
  `start-research/tests/test_start_skills_structure.py` LOCAL_SKILL_DIRS); leave doc rewrites to
  chunks 3 and 4.
- Verify: `cd <tree> && mise run test && mise run lint`

## Chunk 2: migrate and usage records (model: opus)

### S7: ticket.py migrate, old epics to plans

- Files: `scripts/ticket_cmds/migrate.py` (new content),
  `tests/test_ticket_migrate_plans.py` (new), `tests/ticket_repo_helpers.py`.
- Covers: 3.3.
- Test first, fixtures written in the test (no real project data): (a) the current scheme: README
  with Project brief, Description, Goals, Non-goals, Review; design.md with every template
  section; tasks with the eighteen keys; RETRO.md with the generated block, Retro table and
  Improvements; record.md; close.json. (b) the older scheme: approvals.json, rulings.json, tasks
  with `owns`, `uses`, `estimate`, `actual`, `worktree`, `branch`, `run`, `provides`,
  `acs_for_audit`, `process_gaps`, extra task sections `## Ruling` and `## Resolution`, README
  `## Time`, design.md extra sections (`## Contracts`). (c) a todo epic with README only.
  (d) an in-progress epic with done and todo tasks and a dependency chain. Assertions:
  - `migrate <epic> | --all [--dry-run]`; `--all` covers todo, in-progress and done and keeps
    each plan in its phase; plan dirs already holding plan.md are untouched.
  - plan.md and implementation-plan.md follow the S1 templates and the mapping in plan.md D10:
    one rung `Rung 1: agreed scope (migrated)` from the README goals; in-progress and done get
    `rung: "1"` and an Agreed scope stating the migration, todo gets `rung: ""` and "not agreed
    yet", so `move <plan> in-progress` refuses a migrated todo plan until a gate sets the rung;
    a todo epic with no tasks gets no implementation-plan.md; steps in dependency order in one
    chunk whose model is opus when any
    task was opus else sonnet, each step `### S<n>: <task title>` with `Status`, `Files`,
    `Verify`, `Verified head` and every task body section verbatim one level deeper; rulings.json
    as `## Rulings (migrated)`; approvals.json and every unmapped README or design.md section
    under `## Migrated notes`; README `## Time` dropped.
  - retro.md written when RETRO.md or record.md existed: Retro table columns split into What went
    well and What went wrong or could improve, Improvements under Recommendations, the generated
    block dropped, record.md verbatim under `## Delivery record (migrated)`; no retro.md otherwise.
  - Nothing lost: every line of every mapped source section appears in the output.
  - README.md, design.md, tasks/, RETRO.md, record.md, approvals.json and rulings.json are removed
    with `git rm`; close.json stays; one commit per plan, `chore(ticket): <plan> migrate`, holding
    exactly that plan's paths; per plan one line `<plan>: migrated (<n> steps[, retro.md])`.
  - Validation first: any unparseable file in any epic exits 1, lists every problem and writes
    nothing anywhere.
  - `--dry-run` writes nothing, makes no commit, runs in any checkout and prints per plan the
    files it would write and remove; a second run prints `migrate: nothing to change`.
  Run red.
- Change: write the module; it reads old files with the existing frontmatter loader.
- Verify: `pytest skills/start-development/tests/test_ticket_migrate_plans.py`

### S8: Usage records keyed by plan; calibration gone

- Files: `plugins/workbench/scripts/lib/agent_usage.py`, `plugins/workbench/scripts/lib/calibration.py`
  (delete), `scripts/tests/test_agent_usage.py`, `scripts/tests/test_calibration.py` (delete),
  `hooks/agent-usage-recorder.py`, `hooks/tests/test_agent_usage_recorder.py`,
  `hooks/tests/test_py39_safe.py`, `hooks/tests/test_fail_closed.py` (only if they name the
  removed parts).
- Covers: 2.2 (D9).
- Test first: the marker `[wb <plan>/<role>]` with role one of plan, impl, review, merge parses;
  the old three-part marker does not; a record carries `plan` and `role` and no `epic` or `task`;
  calibration.py and test_calibration.py absent from `git ls-files`; agent_usage keeps only what
  the recorder uses (summarize, parse_marker, role_for, write_record and their helpers). Run red.
- Change: trim agent_usage.py, update the recorder, delete calibration.
- Verify: `pytest scripts/tests/test_agent_usage.py hooks/tests/test_agent_usage_recorder.py hooks/tests/test_py39_safe.py hooks/tests/test_fail_closed.py`

### S9: Dry run on real data, outside every checkout

- Files: none committed.
- Covers: 3.3.
- Test first: none (verification step).
- Change: copy (read-only access, the one exception to the tree rule for this step) `docs/plans`
  of this repo's main checkout and of `../ros2-lerobot-sverve-platform` (sibling of the
  workbench) into two fresh git repos under
  `$(mktemp -d)`, commit, and run `python3 <tree>/plugins/workbench/skills/start-development/scripts/ticket.py migrate --all --root <copy>/docs/plans`
  first with `--dry-run`, then for real. Expect 27 plans migrated in the ros2 copy and 10 in this
  repo's copy (plan-flow-rework untouched), no refusal, a second run `nothing to change`. Any
  refusal is fixed in S7's code with a new failing fixture first. Report the counts.
- Verify: the two migrate runs' last lines, quoted.

### S10: Chunk 2 green

- Files: only tests the chunk's changes broke.
- Covers: 3.3.
- Test first: none (verification step).
- Change: as S6.
- Verify: `cd <tree> && mise run test && mise run lint`

## Chunk 3: flow skills and agents (model: sonnet)

### S11: start-development and its references

- Files: `skills/start-development/SKILL.md`, `references/tickets.md`, `references/worktrees.md`,
  `references/non-negotiables.md`, `references/hooks.md`, `references/workbench-config.md`,
  `references/merge-hosts.md` (trim epic-only text), `references/retro.md` (delete);
  tests `test_skill_size.py`, `test_lean_flow_docs.py` replaced by `test_plan_flow_docs.py`,
  `test_ticket_flow_docs.py`, `test_flow_references_remarks.py`, `test_review_flow_docs.py`,
  `test_start_development_remarks.py`, `test_start_development_generic.py`,
  `test_docs_paths_handback.py`.
- Covers: 1.1, 3.4.
- Test first: SKILL.md at most 150 lines, every named reference exists, retro.md not in KEPT;
  test_plan_flow_docs.py pins, in SKILL.md plus references: discovery subagents, plan-writer,
  scope ladder from MVP to complete, open questions with a recommended answer, one gate that may
  batch plans (a section and a worktree each), implementation plan for the agreed rung only and
  no second gate, `plan-run`, one implementer per plan with sequential chunks in one tree, one
  reviewer on the whole diff, under- and over-delivery, at most two fix rounds by SendMessage,
  worktree-merger merges, retro.md by the reviewer, recommendations relayed in the closing
  message; and the absence of epic, task file, points, builder check, scope-auditor,
  record-writer, retro-writer, record.md. test_ticket_flow_docs.py: every `ticket.py <sub>` the
  docs name is a real subcommand (parse `--help`). Run red.
- Change: rewrite SKILL.md per plan.md Design (Modes; Phase 1 Discovery with the Plan inputs four
  lists, `fix-as-ac` now placed as a step's Verify or Test first; Phase 2 Plan; The gate; Phase 3
  Implementation plan; Phase 4 Run via plan-run; Non-negotiables). tickets.md documents the
  layout, frontmatter, kept subcommands and migrate. non-negotiables: the agreed rung is the
  scope; discovered work is recommended, never built; over-delivery is a finding. hooks.md: the
  new marker. workbench-config.md: overlapIgnore read by worktree-merge only; refRunners read by
  the plan-writer.
- Verify: `pytest skills/start-development/tests`

### S12: plan-run skill; epic-run gone

- Files: `skills/plan-run/SKILL.md` (new), `skills/plan-run/tests/test_plan_run_structure.py`
  (new), `skills/epic-run/` (delete).
- Covers: 2.1.
- Test first: plan-run SKILL.md at most 100 lines; names entry conditions (rung set,
  implementation-plan.md present, main clean), `ticket.py move <plan> in-progress`, one
  `workbench:implementer` per chunk with the chunk's model and marker `[wb <plan>/impl]`, paths
  passed instead of file contents, `workbench:reviewer` (sonnet) with `<base>...HEAD`, at most two
  fix rounds by SendMessage, the reviewer writing retro.md on pass, `workbench:worktree-merger`
  (sonnet; opus when `merge.py --assess` predicts a conflict), security-researcher for a diff
  touching secrets, RBAC, ingress, privilege, CI vars, image pins or hooks, every agent call in
  the background, capped reports (implementer 200 words, reviewer 250, merger 150), the closing
  message with the retro.md path and its recommendations one line each; `skills/epic-run` absent
  from `git ls-files`. Run red.
- Change: write plan-run; delete epic-run.
- Verify: `pytest skills/plan-run/tests`

### S13: Agents

- Files: `agents/plan-writer.md` (new), `agents/implementer.md`, `agents/reviewer.md`,
  `agents/worktree-merger.md`, deleted `agents/planner.md`, `agents/record-writer.md`,
  `agents/retro-writer.md`, `agents/scope-auditor.md`; tests `test_planner_agent.py` replaced by
  `test_plan_writer_agent.py`, `skills/start-review/tests/test_agents_lean.py`,
  `skills/start-research/tests/test_start_skills_structure.py`.
- Covers: 1.2, 2.1, 2.2, 3.2.
- Test first:
  - plan-writer (model opus; tools Read, Write, Edit, Grep, Glob, Bash, LSP, ToolSearch): two
    modes, plan (input `{plan, briefs[]}`: fills plan.md, ladder from MVP to complete, every open
    question with a recommended answer, `(my call)` on unstated defaults, commits
    `docs(plan): <plan> plan`) and implementation (input: the user's gate answer verbatim:
    records Agreed scope and answers, sets `rung`, writes implementation-plan.md for that rung
    only with chunks, Covers and verify commands, commits `docs(plan): <plan> implementation
    plan`); writes only under its plan dir; report at most 200 words.
  - implementer: works the chunk of implementation-plan.md it is given in the plan tree, commits
    per step, resumes from the git log, builds nothing outside the plan's steps, reports
    `discovered` without building it; keeps the tree rules, TDD, verify, context ceiling.
  - reviewer: tools add Write; inputs plan.md, implementation-plan.md, tree, base; order: clean
    tree and HEAD, every step's Verify and the Final verify on HEAD, under-delivery (every agreed
    item and step), over-delivery (every changed hunk maps to a step and an agreed item), debt
    markers, quality; output `undelivered`, `overDelivered`, `findings`; on a clean pass writes
    retro.md from the template and nothing else; no `pointsActual`.
  - worktree-merger: section `## Plan close`: meta runs `ticket.py close <plan> --verify`,
    resolving a rebase conflict in the plan tree then rerunning close; component pushes, opens the
    MR, watches, merges when green and mergeable, then `ticket.py move <plan> done`.
  - planner, record-writer, retro-writer, scope-auditor absent from `git ls-files`.
  Run red.
- Change: write and rewrite the agents as pinned; README agent tables are chunk 4.
- Verify: `pytest skills/start-development/tests skills/start-review/tests skills/start-research/tests`

### S14: Chunk 3 green

- Files: only tests the chunk's changes broke.
- Covers: 3.4.
- Test first: none (verification step).
- Change: as S6.
- Verify: `cd <tree> && mise run test && mise run lint`

## Chunk 4: every other reference, metadata, pins (model: sonnet)

### S15: Kept skills

- Files: `skills/start-discovery/SKILL.md`, `skills/start-research/SKILL.md`,
  `skills/research-code-internal/SKILL.md`, `skills/research-code-external/SKILL.md`,
  `skills/research-docs/SKILL.md`, `skills/research-papers/SKILL.md`,
  `skills/start-review/SKILL.md`, `skills/interrogate/SKILL.md`, `skills/start-debugging/SKILL.md`,
  `skills/pullrequests-review-loop/SKILL.md`, `skills/worktree-create/SKILL.md`,
  `skills/worktree-create/scripts/create.py` (help text only), `skills/worktree-merge/SKILL.md`,
  `skills/worktree-merge/scripts/merge.py` (the not-checked-out message only), and their tests:
  `start-discovery/tests/test_discovery_structure.py`,
  `research-code-internal/tests/test_research_skills_structure.py`,
  `start-review/tests/test_start_review_structure.py`,
  `interrogate/tests/test_interrogate_structure.py`,
  `start-debugging/tests/test_start_debugging_structure.py`,
  `pullrequests-review-loop/tests/test_review_loop_structure.py`,
  `worktree-merge/tests/test_close_entry_docs.py`, `worktree-merge/tests/test_merge_target.py`.
- Covers: 3.4.
- Test first: each structure test pins the new wording: discovery feeds the plan-writer and phase 2
  is the plan; research-code-internal runs before phase 2 (no "lean path"); start-review is the
  standalone review and the reviewer in plan-run follows the same checklist; interrogate runs when
  plan-run's two fix rounds leave findings open or for a high-risk plan before the gate;
  start-debugging phase 7 goes through start-development with the regression test and fix as the
  MVP rung; worktree-create and worktree-merge speak of the plan tree and `ticket.py move <plan>
  in-progress`; none of them says epic. Run red.
- Change: edit the wording only.
- Verify: `pytest skills/start-discovery/tests skills/research-code-internal/tests skills/start-review/tests skills/interrogate/tests skills/start-debugging/tests skills/pullrequests-review-loop/tests skills/worktree-create/tests skills/worktree-merge/tests`

### S16: Rules, AGENTS.md, CLAUDE.md, READMEs, harness doc, plugin metadata

- Files: `plugins/workbench/rules/housekeeping.md`, `AGENTS.md` (ground rule 1, Template
  maintenance; rules block regenerated by `mise run harness-setup`), `CLAUDE.md`, `README.md`,
  `plugins/workbench/README.md` (agents, dispatch table, skills list, Documents layout, the loop,
  verification, tests), `docs/harnesses.md`, `plugins/workbench/.claude-plugin/plugin.json` and
  `.claude-plugin/marketplace.json` (descriptions only, not versions), `.gitignore` (drop
  `docs/plans/index.json`); tests `scripts/tests/test_agents_md.py`,
  `scripts/tests/init_engine/test_project_files.py`,
  `skills/start-development/tests/test_release.py`,
  `skills/start-development/tests/test_plugin_readme_rules.py`.
- Covers: 3.4.
- Test first: ground rule 1 names `plan-run`, the scope ladder, one gate, one implementer, one
  reviewer on the whole diff and two fix rounds, and not epic-run or scope audit; the init-built
  AGENTS.md contains `plan-run`; plugin.json description words: one approval gate, scope ladder,
  plan-run, review, debugging, verification hooks, and no epic. Run red.
- Change: housekeeping rule 1: supervisor duties are ticket.py, the test and lint commands, and
  dispatching; plan.md and implementation-plan.md are written by the plan-writer, retro.md by the
  reviewer; then `mise run harness-setup` and commit the regenerated block. Rewrite the other
  texts to the new flow.
- Verify: `cd <tree> && pytest scripts/tests/test_agents_md.py scripts/tests/init_engine/test_project_files.py && cd plugins/workbench && pytest skills/start-development/tests/test_release.py skills/start-development/tests/test_plugin_readme_rules.py`

### S17: Retirement pins for the whole flow

- Files: `plugins/workbench/scripts/tests/test_retired_epic_flow.py` (new),
  `scripts/tests/test_no_epic_flow_refs.py` (new).
- Covers: 2.2, 3.4.
- Test first, both asserting on tracked files only: every path under Files to delete is absent
  from `git ls-files`; no tracked file under `plugins/workbench/` except `CHANGELOG.md`,
  `skills/start-development/scripts/ticket_cmds/migrate.py`, `references/tickets.md` and test
  files contains `epic-run`, `epic-create`, `epic-move`, `epic-task-create`,
  `epic-worktrees-remove`, `epic-migrate`, `scope-auditor`, `record-writer`, `retro-writer`,
  `workbench:planner`, `new-task`, `points_actual`, `builder check`, and no `*.md` under
  `skills/`, `agents/`, `rules/` (same exceptions) contains the word epic; the root AGENTS.md,
  CLAUDE.md, README.md and docs/harnesses.md contain none of those terms. Terms are split in the
  test source so it does not match itself. These pass if S11 to S16 were complete; a failure means
  a missed reference, fixed in the file it names.
- Change: fix any reference the pins find.
- Verify: `pytest scripts/tests/test_retired_epic_flow.py && cd <tree> && pytest scripts/tests/test_no_epic_flow_refs.py`

### S18: MEMORY.md and chunk 4 green

- Files: `MEMORY.md`.
- Covers: 3.4.
- Test first: none (doc edit exception).
- Change: one dated entry (2026-10-31): the plan flow replaced epics and tasks, why (tokens, speed,
  over-delivery), what was kept (ticket.py scaffolding, worktrees, one gate, retro by the
  reviewer), the old-format refusal and `ticket.py migrate --all`.
- Verify: `cd <tree> && mise run test && mise run lint`

## Files to delete

All under `plugins/workbench/` unless rooted otherwise.

Chunk 1:
- `skills/epic-create/`, `skills/epic-migrate/`, `skills/epic-move/`, `skills/epic-task-create/`,
  `skills/epic-worktrees-remove/` (whole dirs)
- `skills/start-development/templates/design.md`, `templates/epic.md`, `templates/record.md`,
  `templates/task.md`
- `skills/start-development/scripts/ticket_cmds/actuals.py`, `amend.py`, `deltas.py`,
  `questions.py`, `retro.py`, `roadmap.py`, `task_cmd.py`, `migrate.py` (old content; chunk 2
  adds the new file under the same name)
- `skills/start-development/tests/test_ticket_amend.py`, `test_ticket_deltas.py`,
  `test_ticket_lint.py`, `test_ticket_questions.py`, `test_ticket_reap_task.py`,
  `test_ticket_retro.py`, `test_ticket_roadmap.py`, `test_ticket_task_status.py`,
  `test_ticket_names.py`, `test_ticket_overlap_ignore.py`, `test_ticket_migrate_map.py`,
  `test_ticket_migrate.py`, `test_epic_skills_structure.py`, `test_ticket_retired_run_loop.py`
  (renamed to `test_ticket_retired_subcommands.py`)

Chunk 2:
- `scripts/lib/calibration.py`, `scripts/tests/test_calibration.py`

Chunk 3:
- `skills/epic-run/` (with `tests/test_epic_run_structure.py`)
- `skills/start-development/references/retro.md`
- `skills/start-development/tests/test_lean_flow_docs.py` (replaced by `test_plan_flow_docs.py`),
  `skills/start-development/tests/test_planner_agent.py` (replaced by `test_plan_writer_agent.py`)
- `agents/planner.md`, `agents/record-writer.md`, `agents/retro-writer.md`,
  `agents/scope-auditor.md`

## Final verify

`cd <tree> && mise run test && mise run lint`

## After merge

One general-purpose agent (sonnet), in the main checkouts, in this order; each step reports its
real output's summary line. Stop and report on any refusal; never work around one.

- A1: In this repo's main checkout, with the merged ticket.py:
  `python3 plugins/workbench/skills/start-development/scripts/ticket.py move plan-flow-rework done`
  (commits retro.md and the move, removes the tree and branch).
- A2: Migrate this repo's own old epics: `ticket.py migrate --all --dry-run`, then
  `ticket.py migrate --all`; expect 10 plans, then `nothing to change` on a rerun.
- A3: Release: `python3 plugins/workbench/skills/release/scripts/release.py --dry-run`; expect
  level major and version 3.0.0 (rerun with `--level major` if judged lower); then run it for
  real. It bumps plugin.json and marketplace.json, writes the CHANGELOG section, commits
  `chore(release): v3.0.0` and tags `v3.0.0`. Push nothing.
- A4: Refresh the installed plugin: `claude plugin marketplace update workbench-template`, then
  `claude plugin update workbench@workbench-template --scope user`. Verify
  `~/.claude/plugins/installed_plugins.json` lists `workbench@workbench-template` at 3.0.0 and
  `~/.claude/plugins/cache/workbench-template/workbench/3.0.0/skills/plan-run/SKILL.md` exists.
  The user then runs `/reload-plugins` (or restarts Claude Code); say so in the report.
- A5: Rewrite `~/.claude/rules/workbench-flow.md`: the table maps the old superpowers names to
  `workbench:start-development` and adds a row mapping `epic-run`, `epic-create` and the other
  epic-* names to `workbench:start-development` / `workbench:plan-run`; the closing paragraph
  describes the new flow (discovery subagents, plan.md with a scope ladder, one human gate,
  implementation-plan.md for the agreed rung, plan-run: one worktree, one implementer or
  sequential chunks, one whole-diff reviewer checking under- and over-delivery, at most two fix
  rounds by continuing the same agents, worktree-merger merges, retro.md by the reviewer). Plain
  ASCII.
- A6: ros2-lerobot-sverve-platform (sibling of this repo), from its main checkout:
  - Preflight: `git status --porcelain` empty on main; the tree
    `.claude/worktrees/realsense-d435-head-switchov` clean and with no commit in the last 30
    minutes (`git -C <tree> log -1 --format=%cr`); otherwise stop and ask the user (plan.md Q6).
  - `python3 ~/.claude/plugins/cache/workbench-template/workbench/3.0.0/skills/start-development/scripts/ticket.py migrate --all --dry-run`,
    then without `--dry-run`. Expect 27 plans (5 todo, 3 in-progress, 19 done), one
    `chore(ticket): <plan> migrate` commit each, and a rerun printing `nothing to change`.
  - Check: every dir under docs/plans/{todo,in-progress,done} holds plan.md (and
    implementation-plan.md unless it is a todo plan that had no tasks), none holds README.md,
    design.md or tasks/; the 5 todo plans have an empty `rung`.
  - MEMORY.md line pointing at `docs/plans/in-progress/rtab-map-rgb-d-3d-mapping-on/design.md`:
    point it at `docs/plans/done/rtab-map-rgb-d-3d-mapping-on/plan.md`, commit
    `docs(memory): point the RTAB-Map design at its migrated plan`.
  - Test per that repo's CLAUDE.md: `uv run pytest tests/test_jetson_retired.py tests/test_head_live_refs.py tests/test_head_camera_live_refs.py tests/test_servo_bus_live_refs.py && uv run poe lint`.
  - Push ros2 main (`git push origin main`), per plan.md D12. No deploy: docs only.
- A7: Report: this repo's main is ahead of origin by the merge, A1, A2 and the release commit plus
  tag; pushing it is the user's call.
