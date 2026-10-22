---
title: skill text local bare move
status: todo
repo: workbench
value: init and component-add skills tell the truth about local-bare and the --path move
files: [plugins/workbench/skills/init/SKILL.md, plugins/workbench/skills/component-add/SKILL.md, plugins/workbench/skills/init/tests/test_init_skills.py]
verify: pytest plugins/workbench/skills/init/tests/test_init_skills.py -q
depends_on: []
owns: []
uses: []
model: ""
estimate: 5
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
