---
title: Close entry docs
status: todo
repo: workbench
value: "An epic close always passes ticket.py close's gates; no doc offers a way around them"
files: [plugins/workbench/agents/worktree-merger.md, plugins/workbench/skills/worktree-merge/SKILL.md, plugins/workbench/skills/worktree-merge/tests/test_close_entry_docs.py, plugins/workbench/skills/start-development/scripts/ticket.py]
verify: "cd plugins/workbench && bash scripts/run-tests.sh --only start-development && bash scripts/run-tests.sh --only worktree-merge && bash scripts/run-tests.sh --only workflows && cd ../.. && mise run lint"
depends_on: [sweep-guard]
owns: []
uses: []
model: sonnet
estimate: 25
actual: ""
review: light
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Close entry docs

## Requirement

Close the two phase 5 review findings (scratchpad epic-review.md and scope-audit.md), both verified against the code by the orchestrator.

- The epic close has one entry point, `ticket.py close <epic> --verify '<full suite and lint>'` (design D5, `references/phases-5-7.md` step 3). `plugins/workbench/agents/worktree-merger.md` "## Epic close" (about lines 89-100) and `plugins/workbench/skills/worktree-merge/SKILL.md` "## Epic close" (about lines 83-93) instead tell the merger to run `merge.py --name <epic> --base main --keep --verify ...` itself. That skips the done-task gate, the review gate and `close.json`. Rewrite both sections. The close is run by the orchestrator through `ticket.py close`. The merger is dispatched for an epic close only to resolve a rebase conflict of `<epic>` onto main inside the integration tree, and it never fast-forwards main itself. Name `ticket.py close` as the command that is rerun afterwards. No direct `merge.py --name <epic> --base main` close command remains in either file.
- `plugins/workbench/skills/start-development/scripts/ticket.py` defines `LEGACY_SEP = "--"` twice (about lines 37 and 39). Keep one definition, with an accurate comment: the old `<epic>--<task>` separator, used by the collision guard, worktree lookup and the sweep.
- Test first: a new test pins the docs, and the ticket.py change is a deletion covered by the existing suite.

## Acceptance conditions

- AC1: worktree-merger.md and worktree-merge SKILL.md name ticket.py close as the epic close and contain no direct merge.py --name <epic> --base main close command [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_close_entry_docs.py::test_epic_close_goes_through_ticket_close]
- AC2: both docs limit the merger's epic-close role to a rebase conflict in the integration tree [evidence: test:plugins/workbench/skills/worktree-merge/tests/test_close_entry_docs.py::test_merger_close_role_is_conflict_only]
- AC3: ticket.py defines LEGACY_SEP exactly once [evidence: command:test "$(grep -c '^LEGACY_SEP = ' plugins/workbench/skills/start-development/scripts/ticket.py)" = 1]

## Files

- `plugins/workbench/agents/worktree-merger.md`
- `plugins/workbench/skills/worktree-merge/SKILL.md`
- `plugins/workbench/skills/worktree-merge/tests/test_close_entry_docs.py`
- `plugins/workbench/skills/start-development/scripts/ticket.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
