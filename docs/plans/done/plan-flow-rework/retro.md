# Plan flow replaces epics and tasks retro

## Review

- Final verify: "components with tests: 26   assertions passed: 1936", "all green"; lint exit 0, no leaks found.
- One fix round: leftover `epic` naming in worktree-create `integration()` and a legacy epic/task key shim in the usage recorder were fixed in c581d0f.

## What went well

- Under-delivery check against all binding gate decisions found nothing missing.
- The new skills, agents and templates are short and consistent with each other.
- Retirement pins on git ls-files plus a no-epic-refs test keep the old flow from returning.

## What went wrong or could improve

- Leftover old-flow terms in code and tests outside docs (create.py, recorder) slipped past the docs-only retirement pin and cost a fix round.
- The no-epic-refs test covers docs only; extend it to scripts and hooks.

## Recommendations

- Discovered and not built: scripts/init_engine/owned.py still lists docs/plans/index.json, though the index is retired.
- Out-of-scope ideas: widen the no-epic-refs pin to scripts and hooks.
- Impossible at planning time: none.
