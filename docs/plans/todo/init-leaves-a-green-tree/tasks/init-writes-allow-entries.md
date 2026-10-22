---
title: init writes allow entries
status: todo
repo: workbench
value: "init and component add leave lint:personal green by recording the project's own vocabulary"
files: [scripts/init_engine/finalize.py, scripts/init_engine/cli.py, scripts/init_engine/project_files.py, scripts/tests/init_engine/test_new.py, scripts/tests/init_engine/test_adopt.py, scripts/tests/init_engine/test_component.py]
verify: "pytest scripts/tests/init_engine/test_new.py scripts/tests/init_engine/test_adopt.py scripts/tests/init_engine/test_component.py -q && mise run lint:personal"
depends_on: [personal-allow-file, license-every-plugin]
owns: []
uses: [personal-allow-local]
model: ""
estimate: 6
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

# init writes allow entries

## Requirement

After init (new and adopt) and component add write their files and before their commit, the engine scans every file it generated or changed (AGENTS.md, docs/architecture.md, MEMORY.md, ROADMAP.md, .gitmodules, LICENSE files, workbench.json, any other path in the commit) with check_personal's own _digest/_candidates (imported, not re-implemented). Each digest hit adds {"path": "**", "pattern": "<digest>"} to scripts/personal-allow.local.json (deduplicated, sorted, written with finalize.write_json, read with finalize.read_json); the file is staged in the same commit. component remove leaves entries in place. Literal pattern hits (/Users/, 192.168. ...) are never auto-allowed. After each step `mise run lint:personal` exits 0 for a project name and component owner whose digests are denylisted.

## Acceptance conditions

- AC1: init with a project name whose digest is denylisted writes the allow entry and lint:personal passes [evidence: test:scripts/tests/init_engine/test_new.py::test_init_allows_project_vocabulary]
- AC2: adopt with an owner whose digest is denylisted (in .gitmodules) writes the entry [evidence: test:scripts/tests/init_engine/test_adopt.py::test_adopt_allows_owner_vocabulary]
- AC3: component add writes entries for its own output, deduplicated and sorted [evidence: test:scripts/tests/init_engine/test_component.py::test_component_add_allows_owner_vocabulary]
- AC4: a literal pattern hit is not auto-allowed [evidence: test:scripts/tests/init_engine/test_new.py::test_literal_hits_not_auto_allowed]
- AC5: the personal lint family passes on the changed files [evidence: command:mise run lint:personal]

## Files

- `scripts/init_engine/finalize.py`
- `scripts/init_engine/cli.py`
- `scripts/init_engine/project_files.py`
- `scripts/tests/init_engine/test_new.py`
- `scripts/tests/init_engine/test_adopt.py`
- `scripts/tests/init_engine/test_component.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
