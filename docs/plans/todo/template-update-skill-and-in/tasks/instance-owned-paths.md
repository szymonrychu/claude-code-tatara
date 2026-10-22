---
title: Instance owned paths
status: todo
repo: workbench
value: "New workbenches start with no template plans, contracts, research or memory, from one owned-path list"
files: [scripts/init_engine/owned.py, scripts/init_engine/finalize.py, scripts/tests/init_engine/test_finalize.py]
verify: "pytest scripts/tests/init_engine/test_finalize.py -q && ruff check scripts"
depends_on: []
owns: [instance-owned-paths]
uses: []
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

# Instance owned paths

## Requirement

Move the instance-owned path list into one module and make init's template-history cleanup derive from it (design D1, D2).

- New `scripts/init_engine/owned.py` defines `INSTANCE_OWNED`: an ordered tuple of `(path, kind)` entries, exactly `docs/plans/todo`, `docs/plans/in-progress`, `docs/plans/done` (kind `phase`), `docs/plans/contracts.json`, `docs/plans/index.json`, `docs/plans/facts.md`, `docs/research`, `docs/handoffs` (kind `delete`), `MEMORY.md`, `ROADMAP.md` (kind `rewritten`). It also defines `GENERATED_ON_CONFLICT` for update-conflicts-and-abort (design D4): `AGENTS.md`, `.mise.toml`, `docs/architecture.md`, `LICENSE`, `.claude-plugin/marketplace.json`, and the config-dir `settings.json` and `workbench.json` (resolved through `workbench.config_dir` by the caller). A module docstring says this is the one place these paths are named.
- `finalize.clear_template_history(root)` iterates `INSTANCE_OWNED`: `phase` entries are removed and recreated as an empty dir with `.gitkeep`; `delete` entries are removed (file or dir, missing is fine); `rewritten` entries are left for `project_files.memory_and_roadmap`. No path literal for these entries remains in finalize.py (`PHASES` goes away or is derived from the list).
- Behaviour stays first-init only (`finalize.py` `if first:`); a rerun keeps the project's epics and research (existing `test_rerun_keeps_epics_and_research` stays green).
- `.gitignore` gets no new docs/plans entry (user decision A1).

Interfaces: `owned.INSTANCE_OWNED: tuple[tuple[str, str], ...]`, `owned.GENERATED_ON_CONFLICT: tuple[str, ...]` (config-dir entries marked so the caller can resolve them; builder's choice of representation). `finalize.clear_template_history(root: Path) -> None` keeps its signature.

Steps: test first in `scripts/tests/init_engine/test_finalize.py`: seed tracked `docs/plans/contracts.json`, `docs/plans/index.json`, an epic under each phase, `docs/research/brief.md`, `docs/handoffs/h.md` and a template MEMORY.md entry, commit them, run `new`, then assert `git ls-files docs/plans` is exactly the three `.gitkeep` files and `git ls-files docs/research docs/handoffs` is empty. Run `pytest scripts/tests/init_engine/test_finalize.py -q`; expect the contracts.json assertion to fail first. Then implement.

Notes: the unit `workbench` fixture (`scripts/tests/init_engine/conftest.py`) has no git history; `init(run_cli, ...)` in test_finalize.py creates it. Retirement assertions use `git ls-files`, never the filesystem. The single-source test monkeypatches `owned.INSTANCE_OWNED` (import `owned` and `finalize` with `scripts/init_engine` on sys.path, as cli.py does) and calls `clear_template_history` directly on a temp dir.

## Acceptance conditions

- AC1: after init, git ls-files docs/plans lists only the three phase .gitkeep files and docs/research and docs/handoffs track nothing, with contracts.json and index.json seeded beforehand [evidence: test:scripts/tests/init_engine/test_finalize.py::test_init_tracks_only_plan_gitkeeps]
- AC2: clear_template_history follows INSTANCE_OWNED: an extra monkeypatched delete entry is removed and a rewritten entry is left in place [evidence: test:scripts/tests/init_engine/test_finalize.py::test_clear_template_history_follows_owned_list]
- AC3: after init MEMORY.md and ROADMAP.md hold no template entry and are the fresh init versions [evidence: test:scripts/tests/init_engine/test_finalize.py::test_init_writes_fresh_memory_and_roadmap]
- AC4: owned.py defines INSTANCE_OWNED and GENERATED_ON_CONFLICT [evidence: symbol:scripts/init_engine/owned.py::INSTANCE_OWNED]
- AC5: no new docs/plans entry in .gitignore [evidence: command:! grep -E '^/?docs/plans/(todo|in-progress|done|contracts)' .gitignore]
- AC6: the finalize tests and root lint pass [evidence: command:pytest scripts/tests/init_engine/test_finalize.py -q && ruff check scripts]

## Files

- `scripts/init_engine/owned.py`
- `scripts/init_engine/finalize.py`
- `scripts/tests/init_engine/test_finalize.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
