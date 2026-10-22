---
title: Update conflicts and abort
status: todo
repo: workbench
value: Generated-file conflicts resolve themselves and any other failure leaves the project exactly as it was
files: [scripts/init_engine/update.py, scripts/tests/init_engine/test_update_conflicts.py, scripts/tests/init_engine/conftest.py]
verify: "pytest scripts/tests/init_engine/test_update.py scripts/tests/init_engine/test_update_conflicts.py -q && ruff check scripts"
depends_on: [update-command]
owns: []
uses: [instance-owned-paths, init-update-command]
model: sonnet
estimate: 8
actual: ""
review: full
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Update conflicts and abort

## Requirement

Handle conflicts, the lint gate and every abort path of `update` (design D4, D7).

- Conflicts under `owned.INSTANCE_OWNED` are already resolved by update-command's restore.
- Conflicted paths in `owned.GENERATED_ON_CONFLICT` (config-dir entries resolved through `workbench.config_dir`) resolve to the project side (`git checkout --ours -- <path>` then `git add`); the refresh then regenerates their generated blocks. The output names each such file on one line `kept project side: <path>`.
- After the merge, keys in the config-dir `settings.json` `enabledPlugins` and `extraKnownMarketplaces` that end in `@workbench-template` (from `finalize.TEMPLATE_MARKET`) are renamed to the project's marketplace name read from `.claude-plugin/marketplace.json`; existing project keys and their values win.
- Any other conflicted path: `git merge --abort`, remove every untracked file the run created, print `refused: template update conflicts outside the known paths:` and one path per line on stderr, exit 1. HEAD, index, worktree and `git status --porcelain` equal the pre-run state; no MERGE_HEAD.
- Lint failure (gate added by update-command): abort exactly as above, print the last 20 lines of lint output, exit 1.
- A failing refresh subprocess aborts the same way.

## Acceptance conditions

- AC1: a conflict in AGENTS.md resolves to the project side, the project answers survive, and the output names kept project side: AGENTS.md [evidence: test:scripts/tests/init_engine/test_update_conflicts.py::test_generated_conflict_keeps_project_side]
- AC2: a template-added enabledPlugins key suffixed @workbench-template is renamed to the project marketplace [evidence: test:scripts/tests/init_engine/test_update_conflicts.py::test_template_market_keys_renamed]
- AC3: a conflict outside the known paths aborts with exit 1, lists the path, and leaves HEAD, status and MERGE_HEAD as before [evidence: test:scripts/tests/init_engine/test_update_conflicts.py::test_unknown_conflict_aborts_cleanly]
- AC4: a failing lint command aborts with exit 1 and the same clean state, printing the lint tail [evidence: test:scripts/tests/init_engine/test_update_conflicts.py::test_lint_failure_aborts_cleanly]
- AC5: a failing refresh aborts with exit 1 and the same clean state [evidence: test:scripts/tests/init_engine/test_update_conflicts.py::test_refresh_failure_aborts_cleanly]
- AC6: the update test files and root lint pass [evidence: command:pytest scripts/tests/init_engine/test_update.py scripts/tests/init_engine/test_update_conflicts.py -q && ruff check scripts]

## Files

- `scripts/init_engine/update.py`
- `scripts/tests/init_engine/test_update_conflicts.py`
- `scripts/tests/init_engine/conftest.py`

## Interfaces

Uses `owned.GENERATED_ON_CONFLICT` and the `init-update-command` contract (including the hidden `--lint-command`).

## Expected outcome

Conflicts in generated files resolve to the project side and are named in the output; any other conflict, a red lint or a failed refresh leaves HEAD, index, worktree and MERGE_HEAD exactly as before the run.

## Steps

Write `scripts/tests/init_engine/test_update_conflicts.py` first, reusing the `upstream_pair` fixture from `scripts/tests/init_engine/conftest.py`. Conflict cases: upstream and project edit the same line of AGENTS.md's project block region; upstream adds `enabledPlugins["workbench-new@workbench-template"]`; upstream and project edit the same line of a plain tracked file (for example `docs/enterprise.md`). Run `pytest scripts/tests/init_engine/test_update_conflicts.py -q`; expect red. Implement until green, then rerun test_update.py.

## Notes

The abort may remove untracked files safely only because the preflight refused any untracked state; keep that invariant explicit in a comment. Assert state with `git rev-parse HEAD`, `git status --porcelain` and `git rev-parse -q --verify MERGE_HEAD`.
