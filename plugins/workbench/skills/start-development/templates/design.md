# <Topic> design

## Summary

The outcome in 3-6 lines: what is being built, for whom, and the headline decisions.

## Intent and why

The problem or opportunity behind the request, in the user's terms, and why it matters now.

## Goals

What must be true when this is done; each goal checkable.

## Non-goals

What this work deliberately does not do, so nobody builds it by accident.

## Anti-goals

Outcomes that would make the work a failure even if every goal is met (regressions, scope creep, cost, lock-in).

## Constraints

Hard limits the builder must respect: compatibility, tooling, budget, deadlines, house rules.

## Decisions

One `### D<n>: <title>` H3 per decision, each with the decision, the alternatives, why, and `(my call)` where the agent chose a default the user did not state, and the approval ids it serves (from the ledger).

## Research

One row per lens (table: lens, ran or skipped with reason, adopted ideas, rejected ideas), each idea with a citation (URL, file:line, or doc section).

## Research inputs

| Source | Entry | Lands in |
|---|---|---|
| design doc section, URL or file | the finding | the task(s) that act on it |

## Decision coverage

Every design decision (`### D<n>` above) maps to the task(s) that deliver it, by task slug.

| Decision | Tasks |
|---|---|
| D1 <title> | task-slug-a, task-slug-b |

## Contracts

A contract is a shared part: one owner task lists it in `owns`, every consumer lists it in `uses`, and it is defined in exactly one file. Owner and consumers are task slugs.

| Part | Owner | Consumers | Where defined |
|---|---|---|---|
| `<part>` | task-slug-a | task-slug-b | `path/to/file` |

## Review focus

- Where reviewers should look hardest: high-risk code, shared parts, invariants that tests match.

## Left to the builder

Choices intentionally not made here, with the boundary the builder may decide within.

## Assumptions and unknowns

Facts assumed without proof and questions still open; each says how it will be confirmed (a probe, never a guess) or who can answer.

## Open questions

Product questions that need the user, collected across epics by `ticket.py questions`. One line each: open `- Q<n>: <question> [recommended: <answer>]`, answered `- Q<n>: <question> [answer: <text>]`. Add and answer them with `ticket.py questions --add` and `--answer`; write "none" if there are none.

## Irreversible operations in scope

Anything that cannot be undone (deletes, force pushes, migrations, releases, sends), each with the approval or safeguard that covers it; write "none" if none.
