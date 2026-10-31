# <title> implementation plan

## Agreed rung

The rung of plan.md this plan delivers, its item numbers and the gate modifications; nothing outside them is built.

## Approach

Mode (meta or component), the tree and branch, the order of chunks and the rules every chunk follows.

## Chunk <k>: <name> (model: <sonnet|opus>)

One chunk per implementer, run in order in the same tree; a small plan has one chunk.

### S<n>: <title>

- Files: every file the step creates, edits or deletes.
- Covers: the plan.md items (<n>.<m>) this step delivers.
- Test first: the test written and seen failing before the change, or the named exception.
- Change: what the step changes, concretely.
- Verify: the exact command and the summary line to expect.

## Files to delete

Every path the plan removes, grouped by chunk; write "none" if none.

## Final verify

The repo's full test and lint command, run on the last commit.

## After merge

Steps that run in the main checkout after the merge, in order; write "none" if none.
