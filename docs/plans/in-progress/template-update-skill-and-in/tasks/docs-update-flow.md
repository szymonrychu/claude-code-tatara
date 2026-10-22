---
title: Docs update flow
status: in-progress
repo: workbench
value: "The README tells users to run the skill instead of a manual merge, and the decision is on record"
files: [README.md, MEMORY.md]
verify: "python3 scripts/check_personal.py && grep -q init:update README.md"
depends_on: [template-update-skill]
owns: []
uses: [init-update-command]
model: sonnet
estimate: 5
actual: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Docs update flow

## Requirement

Point the docs at the new flow (design D9).

- README.md `## Pulling template updates`: replace the manual `git remote add` / `git merge template/main` steps with the `template-update` skill and `mise run init:update` (optional `--url`, `--branch`, `--base`); state what arrives (tooling, plugins, rules, generated blocks) and what never does (template plans and records, contracts.json, index.json, facts.md, research, handoffs, MEMORY.md and ROADMAP.md entries); the refusals (uninitialised, dirty tree, conflicts outside the known paths with the manual route, lint failure) and the unrelated-history `--base` case; that it ends in one local commit and never pushes; `mise run doctor` afterwards.
- README.md `## What init does`: one bullet saying init removes the template's own docs (plans, records, contracts, research, handoffs) and starts MEMORY.md and ROADMAP.md fresh.
- Root MEMORY.md: one dated entry (2026-10-22 or the landing date) headed `template update` recording D3 (git merge with owned-path restore over a copier-style sync, and why), D5 (graft for unrelated histories), D6 (merge commit as the record), D7 (lint inside the engine), and that `scripts/init_engine/owned.py` is the one owned-path list.

## Acceptance conditions

- AC1: README.md has the Pulling template updates section [evidence: doc-section:README.md#Pulling template updates]
- AC2: the section names the skill and init:update and no longer documents the manual merge [evidence: command:grep -q 'template-update' README.md && grep -q 'init:update' README.md && ! grep -q 'git merge template/main' README.md]
- AC3: README What init does states that template docs are removed at init [evidence: judgement:]
- AC4: MEMORY.md records the update mechanism decision [evidence: command:grep -qi 'template update' MEMORY.md && grep -q 'owned.py' MEMORY.md]
- AC5: the personal-reference lint passes [evidence: command:python3 scripts/check_personal.py]

## Files

- `README.md`
- `MEMORY.md`

## Interfaces

None beyond the files listed; no public signature changes.

## Expected outcome

README.md tells users to run the template-update skill (or `mise run init:update`) and what it keeps out; MEMORY.md records the mechanism decision.

## Steps

- Doc edit only (TDD exception: a comment or doc edit); say so in `tests.note`.
- Rewrite README.md `## Pulling template updates` and add the `## What init does` bullet.
- Append the MEMORY.md entry.
- Run `python3 scripts/check_personal.py && grep -q init:update README.md`; expect exit 0.

## Notes

README.md must keep passing the personal-reference lint (`python3 scripts/check_personal.py`); the template URL is already allowed there. MEMORY.md is also edited by flow-speed-and-token-optimiz/cache-prefix-change; append a separate entry, never rewrite others.
