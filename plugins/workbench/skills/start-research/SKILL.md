---
name: start-research
description: "Fan-out internet research into a verified, cited brief via persona research subagents plus an adversarial reviewer. Use to research a topic or gather prior art before a design."
---

# start-research

Researches a topic across the internet using several persona research subagents
in parallel and one adversarial reviewer subagent, then synthesizes a verified,
cited brief at `docs/research/<date>-<slug>.md`. Spawns subagents via
the `Agent` tool - never the `Workflow` tool.

## Procedure

1. **Scope.** Restate the topic in one line. Pick the researchers from the
   `lenses` argument (any subset of `docs-purist`, `practitioner`,
   `prior-art-scout`, `paper-scout`):
   - Default `lenses`: the three core personas (`docs-purist`, `practitioner`,
     `prior-art-scout`). Add `paper-scout` when the topic has a research-paper
     dimension.
   - Broad topic: split one lens across two researchers with different
     sub-scopes. A topic focus goes to `workbench:research-practitioner` as a
     focus line in its prompt; no custom persona is run. Hard cap of 5
     researchers.

2. **Research (parallel).** Get each lens's output path first:
   `bash ${CLAUDE_PLUGIN_ROOT}/skills/start-research/scripts/doc_path.sh research "<topic>-<persona>"`.
   Spawn all researchers in a SINGLE message (multiple `Agent` calls) so they
   run concurrently. Each is `subagent_type: workbench:research-<persona>`
   (e.g. `workbench:research-docs-purist`) with `model: sonnet` set explicitly
   in the call. The persona's method and output contract live in its agent
   file; the prompt carries only the topic and the output path for that
   lens's brief.

3. **Review (adversarial).** Get the reviewer's output path with
   `doc_path.sh research "<topic>-review"`. Spawn one
   `subagent_type: workbench:research-reviewer` with `model: sonnet` set
   explicitly. Its prompt carries only the topic, every lens brief path, and
   its own output path. It marks each claim supported / unsupported /
   contradicted and lists gaps and missing angles.

4. **Follow-up (bounded).** If the reviewer reports material gaps, run ONE more
   round of targeted researcher(s) scoped to those gaps, then a quick reviewer
   re-check. Do not loop further.

5. **Synthesize and write.** Drop reviewer-killed claims. Get the brief path:
   ```
   mise exec -- bash ${CLAUDE_PLUGIN_ROOT}/skills/start-research/scripts/doc_path.sh research "<topic>"
   ```
   (`${CLAUDE_PLUGIN_ROOT}/skills/start-research/scripts/brief_path.sh "<topic>"` is the equivalent path helper.) Write the
   brief there and return its path plus an inline executive summary.

## Brief format

Markdown: title + date + topic; executive summary; themed sections with inline
`[n]` citations; explicit "Best practices" and "Prior art" sections; an "Open
questions / gaps" section from the reviewer; a numbered "Sources" list. Every
non-trivial claim cites a source; killed claims do not appear.

The brief ends with a mandatory final `## Plan inputs` section, defined once in
`${CLAUDE_PLUGIN_ROOT}/skills/start-development/references/plan-inputs.md` (lists: `reuse`,
`do-not-build`, `fix-as-ac`, `ideas`).

## Notes

- Runnable standalone (`/start-research <topic>`) and called by
  `start-development` during its discovery and design phases.
- The four `research-*` skills (`research-docs`, `research-code-external`,
  `research-code-internal`, `research-papers`) are the single-lens entry points;
  use this skill when several lenses are wanted at once.
- Always set each subagent's model explicitly (do not inherit the session
  default).
- `docs/research/` is gitignored; briefs stay local.
