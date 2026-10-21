---
name: start-discovery
description: >
  Builds the evidence base before any design or planning happens: maps the
  existing codebase (LSP symbols, grep, per-repo recon agents) and
  sweeps external prior art in parallel, then reports what is known, what is
  assumed, and what is still unknown. Use as phase 1 of start-development, or
  standalone before planning any change to an unfamiliar or large codebase.
  Read-only - it never edits, plans, or designs.
---

# start-discovery

Phase 1 of the development flow. It exists because plans written against an
unread codebase produce work that duplicates what is already there, misses the
call sites that matter, and reinvents a decision the repo already made.

Discovery is read-only and ends in a written brief. It does not design, does not
propose an approach, and does not ask the user to choose anything - that is the
design phase's job (phase 2), and it needs this brief as input.

## The four lanes

Run all four **in a single message** so they execute concurrently. They are
independent; nothing here needs another lane's output.

Skip a lane only when it is genuinely inapplicable, and say in the brief which
lane was skipped and why. A silently skipped lane is how discovery ends up
shallow.

### Lane 1 - LSP symbol sweep (internal, exact)

Where a language server is available for the repo's language, use it for the
questions grep answers only approximately: definitions, all references, call
hierarchy, implementations. This is the lane that stops a plan from missing the
seventh call site. Without a language server, grep is the codebase fallback:
targeted patterns, then Read of the hits.

Available servers are per-repo, and the plugin only configures the connection -
the binary must be installed. Current coverage in this workbench:

| Language | Plugin | Binary required |
|---|---|---|
| Go | `gopls-lsp` | `gopls` |
| Python | `pyright-lsp` | `pyright-langserver` |
| TypeScript | `typescript-lsp` | `typescript-language-server` |

There is no language server for HCL or YAML, so terraform, helm, and helmfile
work gets nothing from this lane - use Lane 2 and grep there instead, and say
so in the brief rather than implying the lane ran.

The binary being on PATH is not sufficient: the agent doing the looking must
have the `LSP` tool in its own tool list. If a cartographer reports no LSP tool
while the server binary exists, that is a config gap to report, not a silent
fallback to grep.

### Lane 2 - Per-repo recon agents (internal, deep)

Dispatch one `codebase-cartographer` agent per repo in scope, all in the same
message. Each returns shape, entrypoints, boundaries, conventions, the repo's
verbatim verification commands, blast radius for the stated change, and its own
unknowns.

Give each agent the actual task, not just the repo name - blast radius is only
meaningful relative to a specific change.

The verification commands each cartographer returns are load-carrying for later
phases: they become what the implementation agents run and what the review loop
checks against. Collect them into the brief verbatim.

### Lane 3 - External prior art (outside)

Invoke `start-research` on the task's external dimension: the library, protocol,
upstream tool, or design pattern involved, with `lenses` defaulting to
`prior-art-scout` and `docs-purist`; `paper-scout` is added on the
research-papers trigger (the task touches an algorithm or published method). It
fans out persona researchers in parallel plus an adversarial reviewer and
returns a cited brief ending in `## Plan inputs`.

Skip only when the task has no external surface at all (pure internal
refactoring of code nobody else has an opinion about). "I already know this" is
not a reason to skip - the model's training data goes stale, and this is the
lane that catches a deprecated API before it is written into a plan.

### Lane 4 - Reuse hunt (internal, dedup)

Invoke `research-code-internal` when its trigger holds: the plan will add any
helper, reader, parser, schema field or subsystem, or a repo in scope has more
than ~200 source files. It hunts the repos for near-duplicate helpers and
existing parts the plan would otherwise rebuild, and writes the shared-parts
map: each part, where it lives, and who should reuse it. Skip only when the
change adds nothing new (pure edit of existing behaviour in a small repo).

## Output: the discovery brief

Write to `docs/research/<date>-<slug>-discovery.md` (gitignored,
same location `start-research` uses). Structure:

1. **Task** - one line, restated.
2. **Repos in scope** and why each is in.
3. **What exists today** - the map, per repo. Entrypoints, boundaries, the parts
   that already do something adjacent to this task.
4. **Verification commands, per repo, verbatim.** Later phases depend on this.
5. **Blast radius** - files and call sites a change would touch, cross-repo
   dependencies, generated artifacts that must be regenerated rather than edited.
6. **External findings** - cited, from Lane 3. Versions where they matter.
7. **Prior art in-tree** - anything here that already solves part of this. Name
   it; reimplementing it is the most common waste this phase prevents.
8. **Unknowns and assumptions** - explicit. What could not be determined, what
   is being assumed, and what would settle each. This section going empty is a
   signal the discovery was shallow, not that the codebase was simple.
9. **Lanes skipped** and why, including any research lenses skipped.
10. **Plan inputs** - one `## Plan inputs` section as defined in
    `${CLAUDE_PLUGIN_ROOT}/skills/start-development/references/plan-inputs.md`, merged and
    de-duplicated from every lane (Lane 3's `## Plan inputs` and Lane 4's shared-parts map).

## Rules

- Read-only throughout. No edits, no branches, no worktrees.
- All four lanes dispatch in one message. Serial discovery is slow discovery.
- Never let a lane report "nothing found" without saying what it looked for.
- The brief ends with unknowns, not with a recommendation. Handing the
  design phase a conclusion pre-empts the approval gate that follows it.
