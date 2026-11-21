# workbench-lite

Portable, user-scope subset of the `workbench` plugin for repos that are not workbenches.
It works in any git repo: no workbench root, no `mise`, no orchestrator tools, no hooks.

## Contents

- Agents (read-only research and diagnostics): `codebase-cartographer`, `architect-researcher`,
  `reuse-hunter`, `submodule-auditor`, `scm-shepherd`, `spec-reviewer`,
  `research-docs-purist`, `research-practitioner`, `research-prior-art-scout`,
  `research-paper-scout`, `research-reviewer`.
- Skills: `start-research` (cited multi-lens research brief, written to `docs/research/`) and
  `handoff` (resume-in-a-fresh-session file, written to `.handoff/` at the git toplevel).
- `references/plan-inputs.md`: the `## Plan inputs` format the research agents end with.

Not included: the opt-in Stop verification hook (`verify-on-stop`), the destructive-command
guardrails and every other hook. They stay in the `workbench` plugin and apply only there.

## Install (user scope)

```sh
claude plugin marketplace add <this repo>
claude plugin install workbench-lite@claude-code-tatara-workbench --scope user
```

Never enable it together with `workbench` in the same project: both ship agents of the same
names, so they would collide. Inside a workbench use `workbench`; everywhere else use this.

## Worktrees in a flat repo

This pack targets flat repos (one repo per project). For single-repo subagent work there, use
the harness's native worktree isolation instead of `superpowers:using-git-worktrees`. A
workbench metarepo is different: the built-in isolation would isolate the superrepo, not
`code/<component>`, so the `workbench` plugin's own worktree skills apply there.

## superpowers v7 on demand

The flow spine is off by default. Enable `superpowers@claude-plugins-official` per project, only
for bounded or architectural work, with `/plugin enable superpowers@claude-plugins-official` or
in the project's settings:

```json
{ "enabledPlugins": { "superpowers@claude-plugins-official": true } }
```

Spikes and small fixes need no flow: use the native tools and the agents above.

## Shared CLAUDE.md layering guidance

Start Claude at the root that owns the instructions; short root
CLAUDE.md plus per-directory files or `.claude/rules/` with `paths:`; `claudeMdExcludes` for
untouched areas; LSP plugins and read-deny rules for generated code; `--add-dir` loads CLAUDE.md
only with `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1`; AGENTS.md is read natively since
v2.1.277 only when no CLAUDE.md exists (https://code.claude.com/docs/en/large-codebases.md,
/memory.md, checked 2026-11-18). No tool, native or community, has submodule-specific support
(15 READMEs grepped, 2026-11-18): our `git-submodules-*`, `submodule-auditor` and worktree
skills remain the differentiator.

## Maintenance

The agent and skill files are generated from `plugins/workbench` by `scripts/sync_lite.py`
(run it after editing a source; `mise run lint:lite` fails on drift). Rewrites that cannot be
expressed as substitutions live in `overrides/`. Edit the source or the override, never the
generated copy.
