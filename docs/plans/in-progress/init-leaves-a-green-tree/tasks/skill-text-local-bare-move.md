---
title: skill text local bare move
status: in-progress
repo: workbench
value: init and component-add skills tell the truth about local-bare and the --path move
files: [plugins/workbench/skills/init/SKILL.md, plugins/workbench/skills/component-add/SKILL.md, plugins/workbench/skills/init/tests/test_init_skills.py]
verify: mise exec -- pytest plugins/workbench/skills/init/tests/test_init_skills.py -q
depends_on: [license-every-plugin]
owns: []
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/init-leaves-a-green-tree-skill-text-local-bare-move
branch: init-leaves-a-green-tree-skill-text-local-bare-move
verified_head: ""
run: ""
provides: []
---

# skill text local bare move

## Requirement

plugins/workbench/skills/init/SKILL.md step 1 says adopt accepts local-bare[:<dir>] only with --path on a checkout that has no origin, and never with --url; step 3 says --path moves the checkout into code/<name> (the original path no longer exists). plugins/workbench/skills/component-add/SKILL.md says the same for its existing-checkout mode. test_init_skills.py pins both statements.

## Acceptance conditions

- AC1: init SKILL.md states the local-bare limits and the --path move [evidence: test:plugins/workbench/skills/init/tests/test_init_skills.py::test_init_skill_states_local_bare_and_move]
- AC2: component-add SKILL.md states the --path move [evidence: test:plugins/workbench/skills/init/tests/test_init_skills.py::test_component_add_skill_states_move]

## Files

- `plugins/workbench/skills/init/SKILL.md`
- `plugins/workbench/skills/component-add/SKILL.md`
- `plugins/workbench/skills/init/tests/test_init_skills.py`

## Interfaces

none

## Expected outcome

Both SKILL.md files state the local-bare limits and that --path moves the checkout into code/<name>.

## Steps

- Add the two failing doc assertions to test_init_skills.py; run red.
- Edit init SKILL.md steps 1 and 3 and component-add SKILL.md; run green.

## Notes

Design D6. Engine facts: adopt.plan_path accepts local-bare only with --path and no origin; cli.cmd_adopt refuses it with --url; the move is os.rename in adopt.py.
