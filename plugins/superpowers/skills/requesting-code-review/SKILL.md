---
name: requesting-code-review
description: "Use when a plan's last chunk is committed, or before any merge to main: one workbench:reviewer (sonnet) reviews the whole diff against plan.md and implementation-plan.md (under-delivery, over-delivery, then quality) and writes retro.md on a pass."
---

# Requesting Code Review

Dispatch one reviewer subagent on the whole diff to catch issues before they land. The reviewer gets precisely crafted context for evaluation - never your session's history.

**Core principle:** one reviewer, the whole diff, against the agreed plan.

## When to Request Review

**Mandatory:**
- After the last chunk of a plan in superpowers:subagent-driven-development
- Before any merge to main

**Optional but valuable:**
- When stuck (fresh perspective)
- After fixing a complex bug outside a plan

## How to Request

**1. Get the range and the package:**
```bash
BASE=$(git -C <tree> merge-base main HEAD)
HEAD_SHA=$(git -C <tree> rev-parse HEAD)
bash ${CLAUDE_PLUGIN_ROOT}/skills/subagent-driven-development/scripts/review-package <plan file> "$BASE" "$HEAD_SHA"
```

The package (commits, stat and `git diff -U10`) is the whole diff, `git diff <base>...HEAD`, in one file. Never review `HEAD~1`: it drops every commit but the last.

**2. Dispatch the reviewer:**

One `workbench:reviewer` (sonnet), set explicitly, in the background, with the template at [code-reviewer.md](code-reviewer.md). The agent carries the review order and reads the workbench plugin's review checklist (`review-checklist.md` in its references) for quality; the template carries the plan, the range and the delivery checklist. A diff touching secrets, SOPS, RBAC, ingress, privilege, CI vars, image pins or hooks also gets one `security-researcher` (sonnet) on the same package.

**3. Act on feedback:**
- `undelivered`, `overDelivered` and every finding go back to the implementer, at most two fix rounds by continuing the same agents (superpowers:subagent-driven-development).
- A finding that is wrong is dropped with the technical reason, recorded as a ledger `Ruling:` line.
- A clean pass ends with retro.md, written by the reviewer.

## Example

```
[Chunk 3 of 3 committed]

BASE=$(git -C /path/tree merge-base main HEAD)
[review-package -> .superpowers/sdd/implementation-plan/review-a7981ec..3df7661.diff]

[Dispatch workbench:reviewer (sonnet) with code-reviewer.md]
  PLAN: docs/plans/in-progress/deploy-index/plan.md
  IMPLEMENTATION_PLAN: .../implementation-plan.md
  BASE: a7981ec  HEAD: 3df7661

[Reviewer returns]:
  verifyPassed: true
  undelivered: [{id: 1.3, evidence: "no --help in index-conversations"}]
  overDelivered: []
  findings: [{severity: minor, file:line: indexer.ts:130, what: "no progress counter"}]

[Fix round 1: continue the chunk's implementer with both findings]
[Continue the same reviewer with re-review-prompt.md]
  1.3 ADDRESSED (index-conversations:12); clean pass; retro.md written.
```

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "I'll just review the diff myself instead of dispatching a reviewer" | You're the coordinator - reviewing the diff inline burns the context window you need to keep driving the work. Dispatch the reviewer: the diff and the evaluation live in its context, and only the findings come back to you. |
| "The reviewer needs my whole session history to understand the change" | Hand it the plan, the range and the package, never your session's history. |
| "A review per chunk is safer" | One reviewer on the whole diff is the gate; a per-chunk review is a duplicate seat. |

## Red Flags

**Never:**
- Skip review because "it's simple"
- Ignore a finding without a recorded reason
- Merge with `undelivered` items or open findings
- Argue with valid technical feedback

**If the reviewer is wrong:**
- Push back with technical reasoning
- Show code/tests that prove it works
- Record the ruling

See template at: [code-reviewer.md](code-reviewer.md)
