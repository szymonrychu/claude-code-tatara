---
name: plan-run
description: "Run one agreed plan after the gate of start-development: claim it, run its chunks through one implementer each, review the whole diff once with at most two fix rounds, land it through the worktree-merger. Use after the gate, or to run a plan prepared in another session."
---

Runs phase 4 of start-development (`../start-development/SKILL.md`, read it first; the flow is not restated
here). `<plan>` is the plan slug and `ticket.py` is
`python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py`, always run from the main checkout.
Hand agents paths, never file contents; every agent call, fix rounds via SendMessage included, runs in the
background, and the orchestrator keeps only each agent's capped report.

## Entry conditions

Stop and report the refusal if any fails:
- plan.md `rung` is set and implementation-plan.md exists next to it (`ticket.py move` enforces both).
- The plan is in `todo` or `in-progress` (a repeat claim reuses the tree).
- Main is clean and green.

## Run

1. Claim: `ticket.py move <plan> in-progress`; it creates the plan tree on branch `<plan>`.
2. Chunks, sequential, in the order of implementation-plan.md, skipping a chunk whose steps are all committed
   (read `git -C <tree> log`), so a rerun resumes. For each, dispatch one `workbench:implementer` per chunk with
   the chunk's model: first line `[wb <plan>/impl]`, then the plan path and the chunk number (never file
   contents), the tree path, branch `<plan>`, the instruction that every command starts with `cd <tree>`, the
   override "work only in the plan tree, never the main checkout, never docs/plans", and "report in at most 200
   words". Note the base: `git -C <tree> merge-base main HEAD`.
3. After the last chunk, one reviewer, `workbench:reviewer` (sonnet): first line `[wb <plan>/review]`, then the
   plan path, the tree path, branch `<plan>`, the base, the same override, and "report in at most 250 words".
   It reviews the whole diff, `git diff <base>...HEAD`, in this order: clean tree at HEAD, every step's Verify and
   the Final verify on HEAD, under-delivery (every agreed item and step), over-delivery (every changed hunk maps to
   a step), debt markers, then quality. A diff touching secrets, RBAC, ingress, privilege, CI vars, image pins or
   hooks also gets `security-researcher`.
4. Unmet items or findings: continue the same implementer (the one whose chunk owns the files, else the last)
   with `SendMessage` (the findings, nothing else), then the same reviewer. At most two fix rounds.
5. A clean review: the reviewer writes retro.md at `ticket.py path <plan> retro` in the main checkout and nothing
   else. Open findings after the cap are yours to judge: a sharper instruction, another approach, or
   `workbench:interrogate` once; never a smaller deliverable.
6. Land: `workbench:worktree-merger` (sonnet; opus when `merge.py --assess` predicts a conflict): first line
   `[wb <plan>/merge]`, then the plan, the mode and the Final verify command, "report in at most 150 words". Meta
   mode it runs `ticket.py close <plan> --verify '<final verify>'`; component mode the MR, watch and merge
   (`start-development` phase 4). Then `ticket.py move <plan> done` (meta mode: close already did it).

## What comes back

- `undelivered` is a finding: send it back in a fix round.
- `discovered` is recommended, never built: it goes to the reviewer's retro.md Recommendations.
- Over-delivery is a finding: the change is removed in a fix round.
- You never implement a step yourself and never merge a tree yourself.

## Exit

End with one closing message of three lines: the plan landed and how it was verified, the retro.md path, and
retro.md's recommendations relayed one line each.
