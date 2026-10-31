# Superpowers-based plan flow replaces the workbench flow implementation plan

## Agreed rung

Rung 3 (complete) of plan.md: items 1.1-1.10, 2.1-2.3, 3.1-3.4, no gate modifications; decisions D1-D9 bind how.
Nothing outside them is built. The Q3 edit of `~/.claude/rules/workbench-flow.md` is outside the repo and runs in
After merge.

## Approach

- Meta mode: the workbench superrepo itself, no submodule. One tree on branch `superpowers-plan-flow`, created by
  `ticket.py move superpowers-plan-flow in-progress` from the main checkout (the old path,
  `plugins/workbench/skills/start-development/scripts/ticket.py`, which is how this plan itself is claimed and
  closed: close runs from main before the fast-forward lands the move).
- Chunks run in order in that one tree: 1 plugin skeleton and plan lifecycle, 2 the vendored flow skills, 3 the
  rung-2 skills, 4 the switch, the reference rewrite and the retirement, 5 harness parity, template sync, upstream
  diff and docs. Every step is test-first, red then green, and ends in one commit with a semantic message.
- Upstream source for every vendored file: `~/.claude/plugins/cache/claude-plugins-official/superpowers/7.0.0/`
  (`$UP` below). Vendored text keeps upstream wording except where a step names the adaptation; every em dash
  (U+2014) becomes ` - `; LICENSE is the one verbatim file (D5, D8).
- `superpowers:<skill>` cross references inside vendored skills must resolve to a vendored skill: references to
  executing-plans, writing-skills, diagnosing-superpowers and the visual companion are removed or rewritten.
- Plugin tests live in `plugins/superpowers/tests/` and run as `pytest plugins/superpowers/tests -q` from the repo
  root (pyproject sets `--import-mode=importlib`); workbench plugin tests run from `plugins/workbench`.
- Another session works the `semver-image-tags-at-the-end` plan in this repo and edits `AGENTS.md` and
  `scripts/tests/test_agents_md.py`; a conflict there surfaces at `ticket.py close` and is resolved in this plan's
  tree, never by editing that plan's files.
- Never use the phrase built as `"builder " + "check"` in `AGENTS.md`, `CLAUDE.md`, `README.md` or
  `docs/harnesses.md` (`scripts/tests/test_no_epic_flow_refs.py`) nor anywhere under `plugins/workbench`
  (`test_retired_epic_flow.py`); inside `plugins/superpowers` it is allowed.

## Chunk 1: Plugin skeleton and plan lifecycle (model: opus)

### S1: plugins/superpowers skeleton, marketplace entry, test and lint tasks

- Files: `plugins/superpowers/.claude-plugin/plugin.json`, `plugins/superpowers/LICENSE`, `plugins/superpowers/NOTICE`,
  `plugins/superpowers/tests/test_structure.py` (new), `mise-tasks/test/superpowers` (new),
  `mise-tasks/lint/superpowers` (new), `.claude-plugin/marketplace.json`, `scripts/tests/test_marketplace.py`
- Covers: 1.1 (plugin, LICENSE, NOTICE), 1.7 (marketplace entry), 1.10 (LICENSE and NOTICE exist)
- Test first: `test_structure.py`: plugin.json name `superpowers`, version `1.0.0`; LICENSE byte-equal to
  `$UP/LICENSE` content pinned as a sha256 constant in the test; NOTICE names `superpowers 7.0.0`, `Jesse Vincent`,
  `MIT` and lists what changed (vendored subset, adaptations, em dashes); marketplace has a `superpowers` entry with
  source `./plugins/superpowers` and version equal to plugin.json. `test_marketplace.py`: add `superpowers` to
  `PLUGINS` (the test pins the exact entry set, so it is no longer accurate without it) and keep packs logic.
  Seen failing: no plugin dir.
- Change: create the plugin dir; copy LICENSE verbatim; write NOTICE; add the marketplace entry (description: the
  development flow forked from superpowers 7.0.0, plan.md scope ladder, one gate, one implementer, one whole-diff
  reviewer, two fix rounds). `mise-tasks/test/superpowers` runs `pytest plugins/superpowers/tests`;
  `mise-tasks/lint/superpowers` runs `ruff check plugins/superpowers` then `shellcheck` on every `*.sh` and every
  extensionless `#!/usr/bin/env bash` file under `plugins/superpowers` (none yet: the task must pass on an empty set).
- Verify: `pytest plugins/superpowers/tests/test_structure.py scripts/tests/test_marketplace.py -q && mise run
  lint:superpowers && mise run lint:personal && mise run lint:root`; expect `passed` and exit 0.

### S2: init keeps a vendored plugin's LICENSE holder

- Files: `scripts/init_engine/finalize.py`, `scripts/tests/init_engine/test_finalize.py`
- Covers: 1.1 (upstream LICENSE kept verbatim)
- Test first: in `test_finalize.py`, a workbench with `plugins/vendored/LICENSE` plus `plugins/vendored/NOTICE`
  keeps its `Copyright (c) 2025 Jesse Vincent` line after `license_file` with `--license mit` and with
  `--license-file`, while `plugins/workbench/LICENSE` is rewritten. Seen failing: today every `plugins/*/LICENSE`
  is rewritten.
- Change: `finalize.license_file` skips a plugin LICENSE whose dir holds a `NOTICE` file (a vendored third-party
  plugin); docstring says so.
- Verify: `pytest scripts/tests/init_engine/test_finalize.py -q && ruff check scripts`; expect `passed`.

### S3: ticket.py, its subcommands, templates and tests move into plugins/superpowers

- Files: `git mv` of `plugins/workbench/skills/start-development/scripts/ticket.py` and `scripts/ticket_cmds/`
  (`__init__.py`, `close_cmd.py`, `migrate.py`) to `plugins/superpowers/scripts/`; `templates/{plan,
  implementation-plan,retro}.md` to `plugins/superpowers/templates/`; `references/tickets.md` to
  `plugins/superpowers/references/tickets.md`; the ticket tests (`conftest.py`, `ticket_repo_helpers.py`,
  `test_ticket_*.py`, `test_templates.py`) to `plugins/superpowers/tests/ticket/`, edited only in their path
  constants; new `plugins/superpowers/tests/ticket/test_workbench_resolver.py`;
  `plugins/workbench/hooks/tests/test_no_retired_words.py`; `plugins/workbench/scripts/tests/test_retired_epic_flow.py`.
  Sizing exception: the renamed test files change one path constant each and count as one entry.
- Covers: 1.6
- Test first: `test_workbench_resolver.py`: (a) from the source tree `ticket.py slug "A b"` prints `a-b`; (b) a copy
  of the plugin under a fake cache `<tmp>/cache/mkt/superpowers/1.0.0/` with the workbench plugin copied to
  `<tmp>/cache/mkt/workbench/3.0.0/` and `4.0.0/` resolves to `4.0.0` (asserted through a debug-free module call,
  `ticket.workbench_plugin_root()`); (c) with no workbench sibling it exits non-zero with
  `ticket.py: workbench plugin not found` on stderr. Seen failing: no `plugins/superpowers/scripts/ticket.py`.
- Change: move the files; in `ticket.py` replace the three `parents[...]` lookups (`_lib`, `scripts/lib`,
  worktree-create, worktree-merge) with `workbench_plugin_root()` per D6; `TEMPLATES` stays `parents[1] /
  "templates"`. Update the moved tests' `ROOT`/`SCRIPT` constants. In `test_no_retired_words.py` drop the
  `MIGRATOR` exemption and in `test_retired_epic_flow.py` drop the two moved paths from `EXEMPT` (the files left
  the plugin, so the exemptions are no longer accurate). `tickets.md` text: path
  `${CLAUDE_PLUGIN_ROOT}/scripts/ticket.py`.
- Verify: `pytest plugins/superpowers/tests -q && (cd plugins/workbench && pytest hooks/tests/test_no_retired_words.py
  scripts/tests/test_retired_epic_flow.py -q) && mise run lint:superpowers`; expect `passed`.

### S4: tooling references and scripts leave start-development for plugins/workbench

- Files: `git mv` of start-development `references/{workbench-config,hooks,merge-hosts,worktrees,user-run-steps}.md`
  to `plugins/workbench/references/`, `scripts/{deploy-hook,user-run-step}.py` to `plugins/workbench/scripts/`,
  `tests/test_{deploy_hook,user_run_step}.py` to `plugins/workbench/scripts/tests/`, start-review
  `references/review-checklist.md` to `plugins/workbench/references/`; edits in `plugins/workbench/agents/reviewer.md`,
  `plugins/workbench/agents/panel-reviewer.md`, `plugins/workbench/skills/worktree-merge/tests/test_merge_config_docs.py`,
  `scripts/tests/test_scratch_and_log_dirs.py`. Sizing exception: renames count as one entry.
- Covers: 1.9 (tooling references point at their new home; prerequisite of 1.8)
- Test first: the moved `test_deploy_hook.py` and `test_user_run_step.py` with their new script paths, and
  `test_merge_config_docs.py` reading `plugins/workbench/references/workbench-config.md`; seen failing before the
  moves.
- Change: move; `deploy-hook.py` imports `parents[1] / "lib"`; the two agents read
  `${CLAUDE_PLUGIN_ROOT}/references/review-checklist.md`; `test_scratch_and_log_dirs.py` keys the hooks.md entry by
  its new path. The start-development and start-review SKILL.md links to these files are updated so nothing dangles
  until chunk 4 deletes those skills.
- Verify: `(cd plugins/workbench && bash scripts/run-tests.sh --only scripts && bash scripts/run-tests.sh --only
  worktree-merge && bash scripts/run-tests.sh --only start-development) && pytest scripts/tests/test_scratch_and_log_dirs.py
  scripts/tests/test_plugin_paths.py -q && mise run lint:plugin`; expect every line `PASS`.

### S5: plugin-wide tests leave start-development

- Files: `git mv` of start-development `tests/{test_release,test_repo_hygiene,test_plugin_readme_rules}.py` to
  `plugins/workbench/scripts/tests/`, edited only in their root constants.
- Covers: 1.8 (nothing worth keeping is deleted with start-development)
- Test first: exception: rename-only move of passing tests; the move is seen green in the new location and the old
  paths are pinned untracked by S16.
- Change: move and fix `ROOT`.
- Verify: `(cd plugins/workbench && bash scripts/run-tests.sh --only scripts)`; expect `PASS  scripts`.

## Chunk 2: The vendored flow skills (model: opus)

Each step copies the named upstream files from `$UP/skills/<name>/`, adapts them as stated, and adds
`plugins/superpowers/tests/test_<skill_with_underscores>.py` pinning the adaptation by phrase (frontmatter `name`
equals the dir, `description` present, every `superpowers:<x>` names a vendored skill, every relative file it names
exists, no em dash, and the step's pinned phrases).

### S6: brainstorming produces plan.md and stops at one gate

- Files: `plugins/superpowers/skills/brainstorming/SKILL.md`, `.../brainstorming/builder-check-prompt.md`,
  `.../brainstorming/plan-writer-prompt.md` (new), `plugins/superpowers/tests/test_brainstorming.py`
- Covers: 1.2
- Test first: pins: "Size the Work" table kept; discovery lanes dispatched as subagents with research on opus
  (`workbench:codebase-cartographer`, `workbench:start-research`, the reuse hunt via `research-code-internal`), each
  brief ending in `## Plan inputs` with `reuse`, `do-not-build`, `fix-as-ac`, `ideas`; `ticket.py check --title` and
  `ticket.py new --title` with `${CLAUDE_PLUGIN_ROOT}/scripts/ticket.py`; one opus subagent briefed by
  `plan-writer-prompt.md` writes plan.md from `templates/plan.md` (What and why, scope ladder MVP..complete with a
  recommended rung, Non-goals, Design, Decisions with `(my call)`, open questions with `[recommended: ...]`,
  Research, Irreversible operations) and commits `docs(plan): <plan> plan`; HARD-GATE text "nothing is built until
  the user picks a rung and answers the open questions"; questions batched at ONE gate; the builder check prompt is
  kept. Absent: Visual Companion, `docs/superpowers/specs`, any second approval. Seen failing: no skill.
- Change: vendor and adapt per the pins; `plan-writer-prompt.md` carries the plan-mode and implementation-mode
  method (D7) taken from `plugins/workbench/agents/plan-writer.md`.
- Verify: `pytest plugins/superpowers/tests/test_brainstorming.py -q && mise run lint:em-dash`; expect `passed`.

### S7: writing-plans writes implementation-plan.md for the agreed rung only

- Files: `plugins/superpowers/skills/writing-plans/SKILL.md`, `plugins/superpowers/tests/test_writing_plans.py`
- Covers: 1.3
- Test first: pins: input is the user's gate answer verbatim, recorded in plan.md Agreed scope, `[answer: ...]` per
  question, `rung` set; output `ticket.py path <plan> implementation` from `templates/implementation-plan.md`, the
  agreed rung only; chunks `## Chunk <k>: <name> (model: <sonnet|opus>)`; steps with Files, Covers, Test first,
  Change, Verify; Files to delete, Final verify, After merge; commit `docs(plan): <plan> implementation plan`; "no
  second gate". Absent: "Native", "Subagent-driven" execution choice, `docs/superpowers/plans`,
  `superpowers:executing-plans`. Kept: file-structure and task right-sizing sections. Seen failing: no skill.
- Change: vendor and adapt.
- Verify: `pytest plugins/superpowers/tests/test_writing_plans.py -q && mise run lint:em-dash`; expect `passed`.

### S8: subagent-driven-development runs one implementer per chunk and one whole-diff reviewer

- Files: `plugins/superpowers/skills/subagent-driven-development/{SKILL.md,implementer-prompt.md,re-review-prompt.md,
  scripts/task-brief,scripts/review-package,scripts/sdd-workspace}`,
  `plugins/superpowers/tests/test_subagent_driven_development.py`
- Covers: 1.4
- Test first: pins: `ticket.py move <plan> in-progress` claims the plan and creates the tree; one
  `workbench:implementer` per chunk, sequential in one tree, model from the chunk header; one `workbench:reviewer`
  (sonnet) on `git diff <base>...HEAD` checking under-delivery against every agreed item, over-delivery of any change
  no step covers, then quality; `security-researcher` for diffs touching secrets, SOPS, RBAC, ingress, privilege, CI
  vars, image pins or hooks; "at most two fix rounds" by continuing the same agents; `undelivered` is a finding,
  `discovered` is recommended and never built; on a pass the reviewer writes retro.md from `templates/retro.md` with
  Recommendations; "Rulings, not stalls" and its four stop conditions plus "an irreversible operation not listed at
  the gate stops the run"; every dispatch sets the model explicitly. Absent: "5 rounds", model escalation, per-task
  reviewer, `task-reviewer-prompt.md`, `superpowers:executing-plans`. The three scripts pass shellcheck and
  `task-brief` extracts one chunk from a fixture implementation-plan.md (run in the test). Seen failing: no skill.
- Change: vendor and adapt; `task-brief` splits on `## Chunk <k>:` headers instead of upstream task headers;
  `re-review-prompt.md` becomes the fix-round prompt for the same reviewer.
- Verify: `pytest plugins/superpowers/tests/test_subagent_driven_development.py -q && mise run lint:superpowers`;
  expect `passed`, exit 0.

### S9: using-git-worktrees and requesting-code-review fit the plan tree and the whole-diff review

- Files: `plugins/superpowers/skills/using-git-worktrees/SKILL.md`,
  `plugins/superpowers/skills/requesting-code-review/{SKILL.md,code-reviewer.md}`,
  `plugins/superpowers/tests/test_worktrees_and_review.py`
- Covers: 1.4 (review half), 1.1 (these two skills vendored)
- Test first: using-git-worktrees names `ticket.py move <plan> in-progress` as the one way a plan tree is made and
  `ticket.py worktrees <plan> --refresh` for reuse; requesting-code-review dispatches `workbench:reviewer` (sonnet)
  with `code-reviewer.md`, which holds the under-delivery and over-delivery checklist, points at
  `references/review-checklist.md` of the workbench reviewer for quality, and ends with retro.md on a pass. Seen
  failing: no skills.
- Change: vendor and adapt.
- Verify: `pytest plugins/superpowers/tests/test_worktrees_and_review.py -q && mise run lint:em-dash`; expect `passed`.

### S10: finishing-a-development-branch lands without a menu

- Files: `plugins/superpowers/skills/finishing-a-development-branch/SKILL.md`,
  `plugins/superpowers/tests/test_finishing.py`
- Covers: 1.5
- Test first: pins: one `workbench:worktree-merger` (sonnet) given the absolute ticket.py path; meta mode `ticket.py
  close <plan> --verify '<final verify>'` (rebase, verify, fast-forward only when green); component mode
  `git-worktrees-commit`, `git-worktrees-push`, `pullrequests-update`, `pullrequests-watch` and merge "the moment it
  is green, mergeable and review-clean"; then `ticket.py move <plan> done` and `ticket.py reap --plan <plan>`; one
  closing message of at most three lines relaying retro.md's recommendations. Absent: the options menu ("Option 1",
  "Discard", "keep the branch as-is"). Seen failing: no skill.
- Change: vendor and adapt.
- Verify: `pytest plugins/superpowers/tests/test_finishing.py -q && mise run lint:em-dash`; expect `passed`.

## Chunk 3: Rung-2 skills (model: opus)

### S11: systematic-debugging vendored

- Files: `plugins/superpowers/skills/systematic-debugging/{SKILL.md,root-cause-tracing.md,defense-in-depth.md,
  condition-based-waiting.md,condition-based-waiting-example.ts,find-polluter.sh}`,
  `plugins/superpowers/tests/test_systematic_debugging.py`
- Covers: 2.1 (systematic-debugging)
- Test first: structure pins as in chunk 2; the four phases kept; a post-deploy failure continues from
  `grafana-debugging-start` when that pack is enabled; dispatches set a model; no CREATION-LOG or test-*.md files
  tracked (D8). Seen failing: no skill.
- Change: vendor, drop the em dashes, make `find-polluter.sh` shellcheck-clean.
- Verify: `pytest plugins/superpowers/tests/test_systematic_debugging.py -q && mise run lint:superpowers`; expect
  `passed`, exit 0.

### S12: test-driven-development, verification-before-completion, receiving-code-review, dispatching-parallel-agents

- Files: `plugins/superpowers/skills/test-driven-development/{SKILL.md,writing-good-tests.md}`,
  `plugins/superpowers/skills/verification-before-completion/SKILL.md`,
  `plugins/superpowers/skills/receiving-code-review/SKILL.md`,
  `plugins/superpowers/skills/dispatching-parallel-agents/SKILL.md`,
  `plugins/superpowers/tests/test_discipline_skills.py`
- Covers: 2.1 (the other four skills)
- Test first: structure pins; receiving-code-review names `pullrequests-review-loop` for PR threads and the two-round
  cap; dispatching-parallel-agents sets the model on every dispatch per AGENTS.md ground rule 2. Seen failing.
- Change: vendor and adapt.
- Verify: `pytest plugins/superpowers/tests/test_discipline_skills.py -q && mise run lint:em-dash`; expect `passed`.

### S13: using-superpowers and its SessionStart hook route a fresh session to this flow

- Files: `plugins/superpowers/skills/using-superpowers/SKILL.md`,
  `plugins/superpowers/skills/using-superpowers/references/{claude-code,codex,gemini,antigravity}-tools.md`,
  `plugins/superpowers/hooks/hooks.json`, `plugins/superpowers/hooks/session-start`,
  `plugins/superpowers/tests/test_using_superpowers.py`
- Covers: 2.2
- Test first: the skill names `brainstorming` as the entry for non-trivial work, one gate, the scope ladder, two fix
  rounds, and says user instructions take precedence; `hooks.json` runs `bash
  "${CLAUDE_PLUGIN_ROOT}/hooks/session-start"` on `startup|clear|compact`; running `session-start` with
  `CLAUDE_PLUGIN_ROOT` set prints JSON whose additional context contains the skill text (run in the test);
  no hermes, muse, pi references, no `run-hook.cmd`. Seen failing.
- Change: vendor and rewrite per the pins.
- Verify: `pytest plugins/superpowers/tests/test_using_superpowers.py -q && mise run lint:superpowers`; expect
  `passed`, exit 0.

## Chunk 4: Switch, reference rewrite and retirement (model: opus)

### S14: project settings switch to the vendored flow

- Files: `.claude/settings.json`, `scripts/tests/test_superpowers_settings.py` (new)
- Covers: 1.7 (settings)
- Test first: `enabledPlugins` has `superpowers@claude-code-tatara-workbench: true`,
  `superpowers@claude-plugins-official: false`, `workbench@workbench-template: false`, and the four existing
  `@claude-code-tatara-workbench` entries unchanged. Seen failing.
- Change: add the three keys.
- Verify: `pytest scripts/tests/test_superpowers_settings.py scripts/tests/test_marketplace.py -q`; expect `passed`.

### S15: every reference to the retired flow points at the vendored flow

- Files: `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/harnesses.md`, `docs/claude-cloud.md`, `docs/enterprise.md`,
  `scripts/tests/test_agents_md.py`, `scripts/tests/init_engine/test_project_files.py`,
  `scripts/tests/e2e/test_harness_targets.py`, `scripts/tests/harness/test_skills_emit.py`;
  `plugins/workbench/{README.md,rules/housekeeping.md,agents/reviewer.md,agents/worktree-merger.md,
  agents/reuse-hunter.md,agents/panel-reviewer.md,scripts/lib/agent_usage.py,scripts/tests/test_agent_usage.py}`;
  SKILL.md of `research-code-external`, `research-code-internal`, `research-docs`, `research-papers`,
  `start-research`, `worktree-merge`, `pullrequests-review-loop`, `worktree-create` and their structure tests
  (`research-code-internal/tests/test_research_skills_structure.py`, `start-research/tests/test_start_skills_structure.py`,
  `pullrequests-review-loop/tests/test_review_loop_structure.py`); `plugins/workbench-observability/skills/
  grafana-debugging-start/SKILL.md`. Sizing exception: one rewrite rule applied across these files; split into S15a
  (root docs and root tests) and S15b (plugin files) commits if it helps the review, same Verify.
- Covers: 1.9, 3.1 (AGENTS.md rules block names the vendored skills by bare name)
- Test first: `test_agents_md.py`: ground rule 1 names `brainstorming`, `writing-plans`,
  `subagent-driven-development`, `scope ladder`, `one approval gate`, `one implementer`, `one reviewer on the whole
  diff`, `two fix rounds`, `systematic-debugging`, `receiving-code-review`, and `superpowers:brainstorming` for
  Claude Code; `superpowers` leaves the banned list and `test_ground_rule_one_names_plan_run` becomes
  `test_ground_rule_one_names_the_flow` (plan-run retires, so the old needles are no longer accurate);
  `test_project_files.py` line 44 asserts `subagent-driven-development` instead of `plan-run`;
  `test_harness_targets.py` and `test_skills_emit.py` expect `brainstorming` where they expected
  `start-development`; `test_agent_usage.py` drops the `workbench:plan-writer` mapping; the structure tests drop
  their start-development assertions (`test_start_development_does_not_chain_superpowers` is deleted: it pins a
  retired skill). Seen failing.
- Change: rewrite ground rule 1 and CLAUDE.md "Claude Code only" (`superpowers:<skill>` for the flow,
  `workbench:<skill>` for tooling; `subagent-driven-development` dispatches in the background); every other file
  swaps the retired name for its successor: start-development, start-discovery -> brainstorming; plan-run ->
  subagent-driven-development; interrogate -> brainstorming's builder review; plan-writer -> brainstorming's
  plan-writer prompt; start-debugging, debug -> systematic-debugging; start-review, review -> requesting-code-review
  and receiving-code-review; `ticket.py` paths -> `plugins/superpowers/scripts/ticket.py`. Then `mise run
  harness-setup` regenerates the AGENTS.md block. AGENTS.md stays under 24000 bytes.
- Verify: `pytest scripts/tests/test_agents_md.py scripts/tests/init_engine/test_project_files.py
  scripts/tests/harness/test_skills_emit.py scripts/tests/test_no_epic_flow_refs.py -q && (cd plugins/workbench &&
  bash scripts/run-tests.sh --only scripts && bash scripts/run-tests.sh --only start-research && bash
  scripts/run-tests.sh --only research-code-internal && bash scripts/run-tests.sh --only pullrequests-review-loop)
  && mise run lint:harness && mise run lint:agents-md`; expect `passed`, every line `PASS`.

### S16: the workbench flow skills retire

- Files: delete `plugins/workbench/skills/{start-development,start-discovery,plan-run,interrogate,start-debugging,
  debug,start-review,review}/` and `plugins/workbench/agents/plan-writer.md`; new
  `plugins/workbench/scripts/tests/test_retired_workbench_flow.py`; new
  `scripts/tests/test_no_retired_flow_refs.py`
- Covers: 1.8, 1.10 (no tracked file names a retired skill), 2.1 (retire start-debugging, debug, start-review,
  review and their tests)
- Test first: `test_retired_workbench_flow.py` asserts `git ls-files` prints nothing for each of the nine paths
  and for every epic-* skill dir; `test_no_retired_flow_refs.py` scans `git ls-files` minus `docs/plans/**`,
  `**/CHANGELOG.md`, `MEMORY.md` and the two retirement tests for the retired names (built from parts:
  `start-development`, `start-discovery`, `plan-run`, `interrogate`, `plan-writer`, `start-debugging`,
  `start-review`, `workbench:debug`, `workbench:review`, `skills/debug`, `skills/review`, `epic-run`) and finds none.
  Both seen failing before the deletion. The deleted skill tests (start-development/tests remainder,
  start-discovery, plan-run, interrogate, start-debugging, start-review tests) go with their skills: they pin retired
  skills and are no longer accurate.
- Change: `git rm -r` the paths; fix any reference the scan still finds.
- Verify: `(cd plugins/workbench && bash scripts/run-tests.sh) && pytest scripts/tests -m "not slow" -q && mise run
  lint:plugin`; expect `PASS` lines only and `passed`.

### S17: in-flight plans stay on plan.md

- Files: `plugins/superpowers/tests/ticket/test_inflight_plans.py` (new)
- Covers: 2.3
- Test first: runs `ticket.py migrate --all --dry-run --root <repo>/docs/plans` and asserts the output is
  `migrate: nothing to change` and every dir under `docs/plans/todo` and `docs/plans/in-progress` holds `plan.md`.
  Exception to red-first: probed green on 2026-10-31 (plan.md Agreed scope); the test pins the state, it adds no
  behaviour.
- Change: none, unless the dry run lists a plan: then `ticket.py migrate <slug>` from the main checkout, one
  `chore(ticket)` commit each.
- Verify: `pytest plugins/superpowers/tests/ticket/test_inflight_plans.py -q`; expect `1 passed` or more.

## Chunk 5: Harness parity, template sync, upstream diff and docs (model: opus)

### S18: other harnesses get the vendored skills

- Files: `scripts/tests/harness/test_skills_emit.py`, `docs/harnesses.md`, `scripts/harness/skills_emit.py` (only
  if the test exposes a gap)
- Covers: 3.1
- Test first: with the repo's settings, `render_skills` emits `.agents/skills/<name>/SKILL.md` for all twelve
  vendored skills, the bodies contain no `superpowers:` prefix and their `scripts/`, `references/`, `templates/`
  paths point into `plugins/superpowers/` (e.g. `plugins/superpowers/scripts/ticket.py`); no name collides with a
  workbench skill. Run it before any change: a failure is the red; if it passes as written, the step records "pins
  behaviour S14 enabled, no code change" in its commit body (the narrow exception), and `skills_emit.py` stays
  untouched.
- Change: fix `skills_emit.py` only where the test fails; `docs/harnesses.md` support matrix gains a "Flow skills"
  note: skills generated like the others, the using-superpowers SessionStart hook is Claude-only (other harnesses
  read the ground rule), per-harness tool notes in `using-superpowers/references/`.
- Verify: `pytest scripts/tests/harness -q && mise run lint:harness`; expect `passed`.

### S19: a template update never brings the retired flow back

- Files: `scripts/init_engine/owned.py`, `scripts/init_engine/update.py`,
  `scripts/tests/init_engine/test_update_retired.py` (new),
  `plugins/workbench/skills/template-update/SKILL.md`
- Covers: 3.2
- Test first: a template commit that re-adds `plugins/workbench/skills/start-development/SKILL.md` and
  `plugins/workbench/agents/plan-writer.md` merged with `mise run init:update`'s engine leaves both untracked and
  absent after the update commit, while an unrelated template change lands. Seen failing.
- Change: `owned.RETIRED`: the nine paths of S16 plus `plugins/workbench/agents/plan-writer.md`; `update.owned_rels`
  includes them so `restore_owned` drops whatever the template stages there; the template-update SKILL.md says
  retired paths are kept out.
- Verify: `pytest scripts/tests/init_engine -q && (cd plugins/workbench && bash scripts/run-tests.sh --only
  template-update) && ruff check scripts`; expect `passed`, `PASS`.

### S20: UPSTREAM.md and mise run superpowers-diff

- Files: `plugins/superpowers/UPSTREAM.md`, `mise-tasks/superpowers-diff` (new), `scripts/superpowers_diff.py`
  (new), `scripts/tests/test_superpowers_diff.py` (new)
- Covers: 3.3
- Test first: two local git repos tagged `v7.0.0` and `v7.1.0` used as the upstream URL: the script prints, one per
  line, the files under the vendored skill dirs that changed, were added or were removed between the base version
  recorded in UPSTREAM.md and the given version, prints nothing else on no change, exits 0, and writes nothing under
  `plugins/superpowers` (asserted by `git status --porcelain`). Seen failing.
- Change: UPSTREAM.md records upstream URL `https://github.com/obra/superpowers`, tag pattern `v{version}`, base
  `7.0.0`, the vendored skill list and per-skill adaptations; the script shallow-clones both tags into a temp dir
  (`--upstream <url>` overrides the URL, for tests), compares only vendored paths and reports; the mise task wraps
  it with `<version>`.
- Verify: `pytest scripts/tests/test_superpowers_diff.py -q && mise run lint:root`; expect `passed`, exit 0.

### S21: docs, MEMORY entry and version bumps

- Files: `README.md`, `docs/architecture.md`, `plugins/superpowers/README.md` (new), `MEMORY.md`,
  `plugins/workbench/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `plugins/workbench/CHANGELOG.md`,
  `plugins/superpowers/tests/test_structure.py`
- Covers: 3.4
- Test first: `test_structure.py`: plugins/superpowers/README.md names each vendored skill and `mise run
  superpowers-diff`; workbench plugin.json and its marketplace entry are `4.0.0` with equal descriptions, and neither
  names a retired skill; `docs/architecture.md` names `plugins/superpowers`. Seen failing.
- Change: README "how to work" section describes brainstorming -> gate -> writing-plans ->
  subagent-driven-development -> finishing-a-development-branch; architecture lists the plugin; plugin README;
  MEMORY.md entry `2026-10-31: the development flow is the vendored superpowers 7.0.0 fork (plugins/superpowers);
  workbench keeps the tooling; why: user request, D1`; workbench plugin.json description drops the flow and keeps
  the tooling, version 4.0.0 in both places; CHANGELOG 4.0.0 entry.
- Verify: `pytest plugins/superpowers/tests/test_structure.py scripts/tests/test_marketplace.py -q && mise run
  lint:em-dash && mise run lint:personal`; expect `passed`, exit 0.

## Files to delete

- Chunk 1: none deleted outright; S3, S4 and S5 move files out of `plugins/workbench/skills/start-development/` and
  `plugins/workbench/skills/start-review/references/`.
- Chunk 4 (S16): `plugins/workbench/skills/start-development/`, `plugins/workbench/skills/start-discovery/`,
  `plugins/workbench/skills/plan-run/`, `plugins/workbench/skills/interrogate/`,
  `plugins/workbench/skills/start-debugging/`, `plugins/workbench/skills/debug/`,
  `plugins/workbench/skills/start-review/`, `plugins/workbench/skills/review/`,
  `plugins/workbench/agents/plan-writer.md`.
- Chunk 4 (S15): the test function `test_start_development_does_not_chain_superpowers` in
  `plugins/workbench/skills/start-research/tests/test_start_skills_structure.py`.

## Final verify

`mise run test && mise run lint` from the repo root; expect every test family `passed`/`PASS` and exit 0.

## After merge

1. User-run (Claude Code session in this repo): `/plugin marketplace update claude-code-tatara-workbench`, install
   `superpowers@claude-code-tatara-workbench`, then `/reload-plugins`; confirm `superpowers:brainstorming` is
   listed and `workbench:start-development` is not.
2. Q3: show the user the diff adding one line to `~/.claude/rules/workbench-flow.md` - "Repos whose
   .claude/settings.json enables superpowers@claude-code-tatara-workbench use superpowers:* as their flow; the table
   below does not apply there." - and write it on the user's ok.
3. Unblock `~/Documents/infrastructure` plan `superpowers-plan-flow` (it loads this fork from GitHub once main is
   pushed; pushing main stays with the user).
