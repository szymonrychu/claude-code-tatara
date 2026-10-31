# Implementer Prompt Template

Use this template when dispatching the implementer of one chunk. The `workbench:implementer` agent carries the
method (test-first, commit per step, resume from the git log, builds nothing outside the steps, the report
shape); this prompt carries the chunk.

```
Agent (workbench:implementer):
  description: "Implement chunk K of <plan>"
  model: [MODEL - REQUIRED: the model from the chunk header,
         `## Chunk <k>: <name> (model: <sonnet|opus>)`; an omitted model
         silently inherits the session's most expensive one]
  run_in_background: true
  prompt: |
    [wb <plan>/impl]
    Plan: [IMPLEMENTATION_PLAN_PATH], chunk [K]. Earlier chunks are committed
    in the tree; build on them.
    Your chunk, extracted: [BRIEF_FILE]. Read it first: it is your
    requirements, with the exact values to use verbatim. Read plan.md next to
    the plan for the Agreed scope.
    Tree: [TREE], branch <plan>. Every command starts with `cd [TREE]`.
    Work only in the plan tree, never the main checkout, never docs/plans.
    ticket.py, if a step needs it: [TICKET] (absolute path).
    [Rulings from the ledger that bind this chunk, one line each, if any.]

    You do not dispatch subagents: not helpers, and never a reviewer. Review
    arrives from the controller after your report, on the whole diff.

    Report in at most 200 words: complete, summary, commits, undelivered,
    discovered, questions, tests, verification.
```

## Fix rounds

A fix round continues the same agent with SendMessage: the reviewer's open findings verbatim, nothing else.

```
SendMessage to [IMPLEMENTER_AGENT_ID]:
  Fix round [R] of 2. Findings:
  [FINDINGS, verbatim, one per bullet]
  Judge each; for each real one, first a test that reproduces it, then the
  fix. Verify, commit and report again in the same shape.
```

**Placeholders:**
- `[MODEL]` - REQUIRED: the chunk header's model
- `[IMPLEMENTATION_PLAN_PATH]` - absolute path of implementation-plan.md in the tree
- `[K]` - the chunk number
- `[BRIEF_FILE]` - the path `scripts/task-brief` printed
- `[TREE]` - absolute path of the plan tree
- `[TICKET]` - absolute path of `${CLAUDE_PLUGIN_ROOT}/scripts/ticket.py`, resolved by the controller
- `[FINDINGS]` - the open findings of the review, copied verbatim
