---
title: Template update skill
status: done
repo: workbench
value: "Users update a workbench by asking for it; the skill runs the engine and reports"
files: [plugins/workbench/skills/template-update/SKILL.md, plugins/workbench/skills/template-update/tests/test_template_update_skill.py, plugins/workbench/README.md]
verify: "cd plugins/workbench && bash scripts/run-tests.sh --only template-update && pytest skills/start-development/tests/test_release.py -q -k readme"
depends_on: [update-unrelated-history]
owns: []
uses: [init-update-command]
model: sonnet
estimate: 6
actual: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/template-update-skill-and-in--template-update-skill
branch: HEAD
verified_head: efddaf2cc90f64aeeab3532c577861fb6808608d
run: template-update-skill-and-in
provides: []
acs_for_audit: []
process_gaps: []
---

# Template update skill

## Requirement

Add the `template-update` skill (design D8, D5).

- `plugins/workbench/skills/template-update/SKILL.md` with frontmatter `name: template-update` and a folded `description: >` (over 80 characters) naming the triggers ("update from the template", "pull template updates", "refresh the workbench from the template").
- Body: run `mise run init:update` from the workbench root; add `-- --url <url>` or `--branch <branch>` only when the user named them. Ask the user nothing on the normal path. Report: the one commit (subject and sha), the template sha, every `kept project side:` file, and that nothing was pushed. Never call a script path, never push.
- Refusals: uninitialised workbench, say to run `init` first; dirty tree, list the paths and stop (do not stash or commit them for the user); conflicts outside the known paths, list them and name the manual route (merge `template/<branch>` by hand, resolve, `mise run init:refresh`); lint failure, show the tail and stop; up to date, say so.
- Unrelated history: show the candidate base the engine printed, ask the user to confirm it (the only question), then rerun `mise run init:update -- --base <sha>`.
- `plugins/workbench/README.md` Skills list gains a `template-update` line, and the paragraph after it mentions that it wraps `mise run init:update`.

## Acceptance conditions

- AC1: SKILL.md frontmatter is name template-update with a folded description [evidence: test:plugins/workbench/skills/template-update/tests/test_template_update_skill.py::test_frontmatter]
- AC2: the skill reaches the engine only through mise run init:update [evidence: test:plugins/workbench/skills/template-update/tests/test_template_update_skill.py::test_engine_only_through_mise_task]
- AC3: every flag the skill passes exists in cli.py update --help [evidence: test:plugins/workbench/skills/template-update/tests/test_template_update_skill.py::test_flags_exist_in_cli_help]
- AC4: the only question is the unrelated-history base confirmation [evidence: test:plugins/workbench/skills/template-update/tests/test_template_update_skill.py::test_asks_only_for_unrelated_history_base]
- AC5: the skill reports commit, template sha, kept project side files and the refusals, and never pushes [evidence: test:plugins/workbench/skills/template-update/tests/test_template_update_skill.py::test_reports_commit_and_refusals]
- AC6: the plugin README names the skill [evidence: test:plugins/workbench/skills/start-development/tests/test_release.py::test_readme_documents_the_template]
- AC7: the skill suite, the README test, frontmatter parsing and plugin lint pass [evidence: command:cd plugins/workbench && bash scripts/run-tests.sh --only template-update && pytest skills/start-development/tests/test_release.py -q -k readme && cd ../.. && pytest scripts/tests/harness/test_sources.py -q -k frontmatter && ruff check plugins/workbench/skills/template-update]

## Files

- `plugins/workbench/skills/template-update/SKILL.md`
- `plugins/workbench/skills/template-update/tests/test_template_update_skill.py`
- `plugins/workbench/README.md`

## Interfaces

Uses the `init-update-command` contract: `update` flags `--url`, `--branch`, `--base`.

## Expected outcome

`workbench:template-update` exists, is listed in the plugin README, runs only `mise run init:update`, asks at most the unrelated-history base question and reports the commit.

## Steps

Write `plugins/workbench/skills/template-update/tests/test_template_update_skill.py` first, mirroring `plugins/workbench/skills/init/tests/test_init_skills.py`: frontmatter shape, no `cli.py`/`init_engine`/`CLAUDE_PLUGIN_ROOT` in the body, every `--flag` on a `mise run init:update -- ...` line exists in `cli.py update --help`, the base question is the only question, the report names commit, sha and `kept project side`, and the body says it never pushes. Run `cd plugins/workbench && bash scripts/run-tests.sh --only template-update`; expect red (no SKILL.md). Write the skill and the README line until green.

## Notes

Resolve the CLI path as init's test does: `SKILLS = Path(__file__).resolve().parents[2]`, `ROOT = SKILLS.parents[2]`, `CLI = ROOT / "scripts" / "init_engine" / "cli.py"`. The plugin README test is `plugins/workbench/skills/start-development/tests/test_release.py::test_readme_documents_the_template`.
