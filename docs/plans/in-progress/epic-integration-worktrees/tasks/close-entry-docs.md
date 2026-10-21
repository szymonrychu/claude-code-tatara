---
title: Close entry docs
status: done
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
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/epic-integration-worktrees--close-entry-docs
branch: epic-integration-worktrees--close-entry-docs-landed
verified_head: c6f82cd125dc21f376866c469b6583880a728aa1
run: epic-integration-worktrees
provides: []
acs_for_audit: []
process_gaps: []
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

- `ticket_cmds/close_cmd.py` (`ticket.py close`) is the close; unchanged here.
- `ticket.py:LEGACY_SEP` keeps its value `"--"`.

## Expected outcome

Both merger docs send the epic close through `ticket.py close`; `LEGACY_SEP` is defined once.

## Steps

- Red: write `test_close_entry_docs.py`; run `cd plugins/workbench && pytest skills/worktree-merge/tests/test_close_entry_docs.py -q`; expect failures.
- Green: rewrite both Epic close sections; drop the duplicate `LEGACY_SEP`.
- Run the task's verify command; expect all green.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
