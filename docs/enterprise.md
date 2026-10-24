# Enterprise rollout

How to run the workbench template under managed Claude Code policy. Everything
here is a setting an admin owns; the template does not try to work around any of
it. Names in angle brackets are yours to fill in. `<mkt>` is the marketplace name
init wrote (`<project-slug>-workbench`, see `.claude-plugin/marketplace.json`).

## How the template loads

The repo root carries `.claude-plugin/marketplace.json` and the project
`.claude/settings.json` declares it as a directory marketplace
(`{"source": "directory", "path": "./"}`) and enables `workbench@<mkt>`. The
plugins load in place from the clone once the folder is trusted. Nothing is read
from anyone's home directory: the working rules are embedded in `AGENTS.md`.

## Managed settings

Set these in the managed settings file of your platform (or the server-managed
console). Keys that are not set impose nothing.

| Key | Effect on the template | What to set |
|---|---|---|
| `strictKnownMarketplaces` (alias `allowedMarketplaces`) | Allowlist of marketplace sources. `[]` blocks every source. An allowlist of only github entries blocks the template's directory marketplace (`Marketplace "<mkt>" is not in the allowed marketplace list`). | Add a `pathPattern` entry for where clones live, anchored: `{"source": "pathPattern", "pathPattern": "^/srv/.*/workspace/"}`. Directory entries need absolute paths, so a pattern is the way to cover many clones. Also add `{"source": "skills-dir"}` if you want skills-directory plugins to keep loading. |
| `blockedMarketplaces` | Checked before the allowlist. Same objects plus `pathPattern` and `hostPattern`. | Do not block the clone prefix. Block the sources you do not want next to it. |
| `allowManagedHooksOnly` | Does not trust hooks from plugins users enable themselves. The workbench hooks (guard-bash, verification ledger, worktree isolation) then do not run. | Force-enable the plugin in managed `enabledPlugins` (below); force-enabled plugin hooks run. |
| `disableWorkflows` | Turns off all workflows, including plugin ones. `workbench:plan-execute` and `workbench:hook-probe` stop working. | Leave unset to keep plan-execute. If you set it, run `mise run harness-setup -- <target>` for your harness and use the `plan-execute` fallback skill (phases run by the agent with its own subagents: no script-held state, no resume, no fan-out caps). |
| `strictPluginOnlyCustomization` | Blocks user and project skills, agents, hooks and MCP that do not come from plugins or managed settings. | Compatible: all template tooling is packaged as plugins. Loose project `.claude/skills` you add yourself would be blocked. |
| `disableSideloadFlags` | Rejects `--plugin-dir`, `--plugin-url`, `--agents`, `--mcp-config` and `CLAUDE_CODE_PLUGIN_DIRS`. | Nothing: the template never relies on `--plugin-dir`. Do not suggest it to users. |

Managed `enabledPlugins` set to `false` blocks a plugin at every scope; `true`
force-enables it and wins name conflicts.

## Admin alternative: managed marketplace plus force-enable

Instead of relying on repo trust, register the template's marketplace from git
and force-enable the plugins:

```json
{
  "extraKnownMarketplaces": {
    "<mkt>": {
      "source": {"source": "git", "url": "https://git.example.com/<org>/<workbench>.git"}
    }
  },
  "enabledPlugins": {
    "workbench@<mkt>": true,
    "workbench-infra@<mkt>": false,
    "workbench-observability@<mkt>": false,
    "workbench-secrets@<mkt>": false
  },
  "strictKnownMarketplaces": [
    {"source": "git", "url": "https://git.example.com/<org>/<workbench>.git"}
  ]
}
```

Turn on only the packs a team uses. This satisfies `allowManagedHooksOnly`. For
containers and CI, `CLAUDE_CODE_PLUGIN_SEED_DIR` can pre-seed a read-only plugin
directory; it is still subject to the allow and block lists.

## CI and headless use

- Trust: there is no dialog in `-p`. Write
  `projects["<absolute repo path>"].hasTrustDialogAccepted = true` into
  `~/.claude.json` (or the file under `CLAUDE_CONFIG_DIR`).
- Plugin install: set `CLAUDE_CODE_SYNC_PLUGIN_INSTALL=1` so plugins are
  installed before the first turn.
- Workflows: add a permission allow rule `Workflow(workbench:plan-execute)` so
  `claude -p` can start it without a prompt. The exact rule syntax for namespaced
  plugin workflows is not documented by Anthropic; verify it with your Claude
  Code version.
- Project-scope plugins do not show in `claude plugin list`. To check loading
  run `CLAUDE_CODE_SYNC_PLUGIN_INSTALL=1 claude -p --output-format stream-json --verbose --max-turns 1 "hi"`
  and read `init.plugins`.

## Authentication and models

### API key, Bedrock, Vertex

Subagents inherit the caller's environment, so API key, Bedrock and Vertex
credentials work as they do for the interactive session. Bedrock and Vertex use
their own variables (`CLAUDE_CODE_USE_BEDROCK`, `CLAUDE_CODE_USE_VERTEX` and the
cloud credentials).

### Model availability

The model table in `AGENTS.md` names research `opus`, implementation `sonnet`,
review `sonnet`, very complex architecture `fable`. Your provider may not offer
`fable`, and the Workflow tool may be unavailable.

- Without `fable`: the `interrogate` panel (fable, opus, sonnet) has no model A.
  Run it with the strongest model you have in that slot, and keep the other two
  panelists; the lead verdict is unchanged. The `start-development` last-resort
  review and architecture steps use your strongest available model instead.
- Without `fable` in the model table: read "very complex architecture" as the
  strongest model you have, set on every dispatch. Nothing else in the table
  changes.
- Without the Workflow tool (or with `disableWorkflows`): `plan-execute` cannot
  run as a script. Use the generated `plan-execute` fallback skill (see
  `docs/harnesses.md`). Heartbeat and hook-probe are also workflow-based.
- Other harnesses use `inherit` for subagent models; override per harness in
  `.claude/workbench.json` under `harness.models`.

## Per-user opt-out

A user who does not want the plugins in their own session writes
`"workbench@<mkt>": false` (and the packs) under `enabledPlugins` in the
gitignored `.claude/settings.local.json`. Local settings override project
settings key by key. Managed `true` cannot be overridden this way.

## Cloud sessions

Cloud (web) sessions do not apply repo marketplaces or project `enabledPlugins`,
so the plugins do not load there. Use the managed route above, or the
`mise run harness-setup -- <target>` generated files for the harness in use.
