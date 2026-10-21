# Harness support

The workbench works in Claude Code with zero setup. In GitHub Copilot, Cursor, OpenAI Codex,
Gemini CLI and Antigravity it works after one `mise run harness-setup -- <target>` (or `all`),
which writes that harness's files from one source: `AGENTS.md`, `.claude/rules/*.md`, the
plugin skills and agents, and `.mcp.json` if the project has one. The generated files are
committed, so colleagues on the same harness need nothing but the first-run trust steps below.

See Supported platforms below.

## Supported platforms

macOS, Linux and WSL. Native Windows is unsupported: every generated hook runs
`python3 plugins/workbench/hooks/adapter.py`, and Cursor guards fail closed when that command
cannot run.

## Support matrix

Legend: native = the harness reads the source as is; generated = `harness-setup` writes the
named file; degraded = a weaker substitute, see "What degrades". Copilot CLI, VS Code and the
Copilot cloud agent share the `copilot` target.

| Row | Claude Code | Copilot CLI | VS Code | Copilot cloud agent | Cursor | Codex | Gemini CLI | Antigravity |
|---|---|---|---|---|---|---|---|---|
| Instructions | native (`CLAUDE.md` imports `AGENTS.md`) | native `AGENTS.md` | native `AGENTS.md` | native `AGENTS.md` | native `AGENTS.md` | native `AGENTS.md` | native `AGENTS.md` | native `AGENTS.md` |
| Rules | native `.claude/rules/` | generated `.github/instructions/<rule>.instructions.md` | same file | same file | generated `.cursor/rules/<rule>.mdc` | degraded: `workbench:path-rules` block in `AGENTS.md` | degraded: `workbench:path-rules` block in `AGENTS.md` | generated `.agents/rules/<rule>.md` |
| Skills | native (plugin) | generated `.agents/skills/<name>/SKILL.md` | same | same | same | same | same | same |
| Agents | native (plugin) | generated `.github/agents/<name>.agent.md` | same | same | generated `.cursor/agents/<name>.md` | generated `.codex/agents/<name>.toml` | generated `.gemini/agents/<name>.md` | generated `.agents/agents/<name>.md` |
| Hooks | native (plugin) | generated `.github/hooks/workbench.json` | same (needs `chat.useClaudeHooks` or the same file, see trust) | degraded: unverified | generated `.cursor/hooks.json` | generated `.codex/hooks.json` | generated `.gemini/settings.json` | generated `.agents/hooks.json` |
| MCP | native `.mcp.json` | native root `.mcp.json` | generated `.vscode/mcp.json` | manual: repository Settings | generated `.cursor/mcp.json` | generated `.codex/config.toml` | generated `.gemini/settings.json` | generated `.agents/mcp_config.json` |
| Workflows | native (Workflow scripts) | degraded: `plan-execute` fallback skill | degraded | degraded | degraded | degraded | degraded | degraded |

Only the guards with an equivalent are registered on non-Claude harnesses: `guard-bash`,
`protect-files` and `subagent-commit-guard`. `verify-recorder`, `bash-output-filter` and
`format-file` are Claude-only.

## Run it

    mise run harness-setup                     # sync AGENTS.md blocks, regenerate recorded targets
    mise run harness-setup -- copilot          # one target
    mise run harness-setup -- cursor codex     # several targets
    mise run harness-setup -- all              # every target
    mise run harness-setup -- --check          # exit 1 listing generated files that drifted
    mise run harness-setup -- --clean cursor   # remove only the files cursor wrote

With no arguments it rebuilds the generated `AGENTS.md` blocks (the `workbench:rules` block from
`plugins/workbench/rules/`, which also works in a Claude-only tree) and rewrites every recorded
target; it is idempotent and exits 0. Targets: `copilot`, `cursor`, `codex`, `gemini`, `antigravity`. An unknown target exits 2.
`--check` regenerates the recorded targets in memory and compares; `mise run lint` runs it, so
drift fails CI. Ownership is recorded in `harness-manifest.json` in the config directory, which
is how `--clean` removes only generated files. The shared skills output (`.agents/skills/`) is
written with every target. Re-run after changing `AGENTS.md`, rules, agents, skills or
`.mcp.json`.

Start the harness at the workbench root. Codex walks `AGENTS.md` from the git root, and a
`code/<x>` submodule is its own git root, so starting there hides the root instructions. Other
harnesses resolve project files from the opened folder in the same way.

## Config directory per harness

Each harness has a directory: `.claude` (Claude Code), `.github` (Copilot), `.cursor`,
`.codex`, `.gemini`, `.agents` (Antigravity). The workbench's own config follows the harness.

- `harness-setup <target>` with exactly one target generates, then moves `workbench.json`,
  `settings.local.json`, the ownership record and the `worktrees/` directory to that
  harness's directory and records `harness.active`.
- `harness-setup claude` moves them back to `.claude/` and generates nothing.
- Several targets, or `all`, generate without moving and print the active directory.
- `harness-setup <target> --no-migrate` generates one target without moving anything.
- `--clean <target>` of the active harness moves back to `claude` first.
- Never moved: Claude Code's own `.claude/settings.json` and `.claude/rules/`, and any file a
  generator owns in the destination.
- The move refuses (exit 1, nothing moved) while a registered git worktree lives under the
  current directory's `worktrees/` (merge or remove them first; `git worktree move` cannot move
  worktrees that contain submodules), and when the destination already holds a different
  `workbench.json`. It is idempotent and reversible.

### Migration is repo-wide

- The migration is a repo-wide choice. `workbench.json` (with `harness.active`) is tracked, so
  the move is committed for the whole team; a mixed team would otherwise flip the config dir and
  worktree location per commit. Teammates on another harness run
  `mise run harness-setup -- <their target> --no-migrate` (or several targets / `all`) to
  generate their files without migrating the dir. Switching back is `harness-setup claude`.

## What degrades

What degrades, and why.

- Workflow scripts (`plan-execute`, `hook-probe`) are Claude-only. The generator emits a
  `plan-execute` fallback skill that lists the phases for the agent to run with its own
  subagents: implement test-first in one worktree per task, verify on the committed HEAD,
  review, at most three fix rounds, one scope audit. It loses script-held state, resume and
  fan-out caps.
- Plugin auto-enable has no equivalent. Generated, committed files replace it.
- Per-agent models map to `inherit` (Cursor, Gemini CLI, Antigravity) or are omitted (Copilot,
  Codex), so each harness uses its default model. Override per target in
  `workbench.json`: `{"harness": {"models": {"codex": {"opus": "<model>"}}}}`.
- Copilot cloud agent MCP cannot be generated. Add servers by hand under repository Settings,
  Copilot, Coding agent, MCP configuration.
- `SubagentStop` has no equivalent on Gemini CLI and Antigravity; the commit guard falls back
  to `Stop` (Gemini `AfterAgent`).
- Read-only agent restrictions are instruction-only on Codex, Gemini CLI and Antigravity: the
  agent file says not to write, but nothing enforces it. Cursor uses `readonly: true`.
- Codex and Gemini CLI have no path-scoped rules, hence the generated block in `AGENTS.md`.
- Claude-only skills (`heartbeat`, `hook-probe`) are not emitted.

## First run and trust

Each harness asks once before it runs project hooks or reads project config.

- Claude Code: accept the trust dialog; approve the marketplace plugins from project settings.
- Copilot CLI: trust the folder when prompted.
- VS Code: grant Workspace Trust; enable `chat.useClaudeHooks` if you rely on Claude-format
  hooks.
- Copilot cloud agent: nothing locally; MCP is the manual Settings step above.
- Cursor: open the folder as a trusted workspace so project hooks and MCP servers run.
- Codex: trust the project, then review hooks in `/hooks` and approve their hash. A changed
  hook file needs approval again.
- Gemini CLI: approve each hook fingerprint on first run; a changed hook asks again.
- Antigravity: open the workspace as trusted so `.agents/hooks.json` runs.

## Unverified

These behaviours are taken from documentation only. Treat each as unverified, and check it in
that harness before relying on it:

- Copilot accepts PascalCase nested hook output from the generated hooks.
- Cursor passes Claude-format hook stdin to the generated guards.
- Copilot honours the agent `model` field.
- VS Code reads the root `.mcp.json` (the generated `.vscode/mcp.json` is the supported path).
- Copilot cloud agent runs `.github/hooks/workbench.json`.

## Project MCP servers

Put servers in a root `.mcp.json`:

    {"mcpServers": {"docs": {"command": "npx", "args": ["-y", "some-mcp-server"]}}}

Claude Code and Copilot CLI read it directly. Run `mise run harness-setup -- <target>` (or
`mise run harness-setup` for the recorded ones) to
translate it into the other harnesses' files, and add the servers by hand for the Copilot
cloud agent.

## Local bare repositories (git 2.38+)

A project whose component remotes are local (`file://` or a plain path) needs
`git -c protocol.file.allow=always submodule add` (or `update`) on git 2.38 and newer. The
template's production code never sets that option; only the end-to-end tests do.
