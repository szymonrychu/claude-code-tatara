---
title: E2e template update
status: todo
repo: workbench
value: The whole init cleanup and update round trip is proven on a real template copy with real lint
files: [scripts/tests/e2e/test_template_update.py, scripts/init_engine/update.py]
verify: "pytest scripts/tests/e2e/test_template_update.py -q && ruff check scripts"
depends_on: [update-unrelated-history]
owns: []
uses: [init-update-command]
model: sonnet
estimate: 8
actual: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# E2e template update

## Requirement

Replace the manual-merge e2e with an end-to-end run of `mise run init:update` on a real template copy (design D2, D3, D4).

- `scripts/tests/e2e/test_template_update.py` drops the manual `git merge` plus `git checkout --ours` flow.
- `test_init_leaves_no_template_docs`: run `init new` in the `template` fixture (which carries this repo's real tracked docs/plans, including contracts.json); assert `git ls-files docs/plans` is exactly the three phase `.gitkeep` files, `git ls-files docs/research docs/handoffs` is empty, and MEMORY.md holds only the init header and the `project initialised` line.
- `test_template_update_roundtrip`: clone the template fixture to `upstream` before init (as today), run `init new` with purpose, hard rule, risk and `--harness cursor`; in the project add and commit its own epic `docs/plans/todo/my-epic/README.md`. In upstream: append a rule line to `plugins/workbench/rules/tdd.md` and rebuild with `scripts/harness/setup.py`, change a plugin file (for example `plugins/workbench/skills/handoff/SKILL.md`), add `docs/plans/done/template-epic/README.md`, append a dated MEMORY.md entry, force-add `docs/research/template-brief.md`, modify `docs/plans/contracts.json`; commit. Then `mise run init:update -- --url <upstream>` exits 0, and:
  - the rule line is in AGENTS.md and the plugin change is in the file;
  - `git ls-files docs/plans/done/template-epic docs/research docs/plans/contracts.json` is empty and the template MEMORY.md entry text is absent;
  - the project's purpose, hard rule and risk are in AGENTS.md, `docs/plans/todo/my-epic/README.md` is unchanged, no `<<<<<<<` in AGENTS.md;
  - exactly one new commit, subject `chore(workbench): template update <sha>`, `git status --porcelain` empty;
  - `scripts/doctor.py` reports `metarepo` and `components: 1`, and `mise run lint` exits 0.

Interfaces: uses the `init-update-command` contract through `mise run init:update` only.

Steps: write the two tests; run `pytest scripts/tests/e2e/test_template_update.py -q`. The engine tasks have landed, so the tests may pass at once: say so in `tests.note` (they pin delivered behaviour end to end); if they fail, the failure is a real gap in the engine and gets fixed in update.py within this task.

Notes: fixtures `template`, `engine`, `mise` in `scripts/tests/e2e/conftest.py` and `helpers.git/run`. The engine's lint gate runs the real `mise run lint` inside the project here, which is the "lint green" proof. Retirement assertions use `git ls-files`.

## Acceptance conditions

- AC1: after init on the real template copy, git ls-files shows only the three plan .gitkeep files and no research or handoffs, and MEMORY.md is fresh [evidence: test:scripts/tests/e2e/test_template_update.py::test_init_leaves_no_template_docs]
- AC2: init:update brings the rule and plugin changes, keeps the template epic, research, contracts and MEMORY entry out, keeps the project's answers and own epic, ends in one commit with lint green [evidence: test:scripts/tests/e2e/test_template_update.py::test_template_update_roundtrip]
- AC3: the manual git merge flow is gone from the e2e test [evidence: command:! grep -q 'checkout", "--ours' scripts/tests/e2e/test_template_update.py]
- AC4: the e2e file and root lint pass [evidence: command:pytest scripts/tests/e2e/test_template_update.py -q && ruff check scripts]

## Files

- `scripts/tests/e2e/test_template_update.py`
- `scripts/init_engine/update.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
