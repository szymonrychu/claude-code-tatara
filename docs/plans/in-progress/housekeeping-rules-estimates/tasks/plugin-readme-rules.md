---
title: Plugin readme rules
status: done
repo: workbench
value: The plugin README names the housekeeping rules beside the other cross-cutting rules
files: [plugins/workbench/README.md, plugins/workbench/skills/start-development/tests/test_plugin_readme_rules.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint"
depends_on: [housekeeping-rules]
model: sonnet
review: ""
verified_head: 1dc8d46
---

# Plugin readme rules

## Requirement

Discovered by the housekeeping-rules implementer: `plugins/workbench/README.md` lines 287-289 list the plugin's cross-cutting rules (tdd, boy-scout, concise-orchestrator) without the new `housekeeping.md`. Add housekeeping to that list with a one-line description matching the rule file's frontmatter description, keep the list's existing format, ASCII only, no em dash. Add a test in `plugins/workbench/skills/start-development/tests/` (or extend the existing README-rules test if one exists) that asserts every file in `plugins/workbench/rules/` named in `scripts/harness/agents_md.py` RULE_FILES is named in the plugin README's rules list.

## Acceptance conditions

- AC1: the plugin README names housekeeping among the cross-cutting rules [evidence: command:grep -n "housekeeping" plugins/workbench/README.md]
- AC2: a test pins that every RULE_FILES entry is named in the plugin README [evidence: test:plugins/workbench/skills/start-development/tests/test_plugin_readme_rules.py::test_readme_lists_every_rules_block_file]

## Files

- `plugins/workbench/README.md`
- `plugins/workbench/skills/start-development/tests/test_plugin_readme_rules.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

1. Read `plugins/workbench/README.md` (the rules list near lines 287-289), `plugins/workbench/rules/housekeeping.md` (its frontmatter description) and `scripts/harness/agents_md.py` (RULE_FILES).
2. Write `test_plugin_readme_rules.py::test_readme_lists_every_rules_block_file` first; run `pytest plugins/workbench/skills/start-development/tests/test_plugin_readme_rules.py -q` and see it fail because housekeeping is missing from the README.
3. Add the housekeeping line to the README list in the existing format; run the verify once and see it green.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-24 todo: Estimate: 1 points

- 2026-10-24 done
