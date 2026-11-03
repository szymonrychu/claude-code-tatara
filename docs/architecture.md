# Architecture

## Components

```
workdir/
  code/
    claude-code-wrapper/  (python)
    any-mcp/  (python)
    agents-orchestrator/  (python)
    agents-helmfile/  (generic)
    agents-web/  (typescript)
    agents-common/  (python)
    agents-webhook/  (python)
    agents-schedule/  (python)
    agents-matrix-connector/  (python)
    any-mcp-tatara-plugins/  (python)
    agents-usage/  (python)
    agents-history/  (python)
    agents-taskboard/  (python)
    agents-app-connector/  (python)
    agents-boox-sketch/  (generic)
```

- `code/claude-code-wrapper` (python): HTTP microservice that runs long-lived interactive Claude Code sessions under PTYs and exposes turns, an SSE event stream and lifecycle hooks
- `code/any-mcp` (python): MCP server that exposes any API as MCP tools through a plugin system (stdio and streamable HTTP)
- `code/agents-orchestrator` (python): Web UI and headless API orchestrating Kubernetes pods of claude-code-wrapper agents: sessions, round-robin dispatch, chat history (Python backend, React frontend, helm chart)
- `code/agents-helmfile` (generic): helmfile managing namespace agents: CNPG database and the agent-orchestrator release, applied with local mise tasks
- `code/agents-web` (typescript): Web UI of the agents system (React/MUI SPA served as static files by nginx-unprivileged), reaching each backend (agent-orchestrator first) through its documented HTTP API on one host
- `code/agents-common` (python): Python library shared by the trigger services (agents-webhook, agents-schedule): settings, Postgres pool, migrator, guarded queue transitions, orchestrator client, run tracker
- `code/agents-webhook` (python): Python microservice with its own Postgres database that receives GitHub/GitLab PR, issue and comment webhooks and Grafana alerts, queues them FIFO with dedup and limits, and starts agent clusters from presets through the orchestrator API
- `code/agents-schedule` (python): Python microservice mapping cron schedules to presets; fires agent clusters through the orchestrator API; own database
- `code/agents-matrix-connector` (python): Python microservice with its own Postgres database: connects to the Matrix homeserver as a bot user, auto-discovers Messenger chats bridged by mautrix-meta, applies allow/deny rules and routes allowed chats to agents-orchestrator sessions
- `code/any-mcp-tatara-plugins` (python): Bucket of platform-specific any-mcp plugins grouped into topic subdirectories, installed by any-mcp from a git repo, subdirectory and ref (terraform-module-like source notation)
- `code/agents-usage` (python): Python microservice with its own Postgres that collects Claude plan usage windows (5-hour, weekly) pushed by the agents' claude-code-wrapper statusLine relay, with a lazy CLI probe as fallback, and records session start/end marks; serves current, history and marks for the orchestrator's usage gate and the web UI
- `code/agents-history` (python): Python microservice with its own Postgres that stores and searches historical agent session logs (transcripts) exported by agents-orchestrator, with retention cleanup and user-only delete; serves read and search to superleaders
- `code/agents-taskboard` (python): Python microservice with its own Postgres: tasks, decisions answered once, todo, comments and history for users and agents; agents reach it through an orchestrator relay, user answers notify the asking session
- `code/agents-app-connector` (python): Python microservice with its own Postgres and a PVC: client-plugin connector for user devices; plugin sketch pairs Boox devices, takes sketch uploads, translates them into versioned markdown specs through a sketch-translator agent session, streams progress and hands specs off to sessions
- `code/agents-boox-sketch` (generic): Kotlin Android app for BOOX e-ink tablets: pen board with pages, multi-page sketch upload to agents-app-connector, spec panel, hand-off; signed APKs on GitHub Releases

## Plugins

The development flow is the vanilla superpowers plugin (`superpowers@claude-plugins-official`,
enabled in `.claude/settings.json`), never modified here. The root marketplace
(`.claude-plugin/marketplace.json`) offers the plugins under `plugins/`:

- `plugins/workbench`: helpers to vanilla superpowers: agents, research, worktree,
  submodule and pull request skills, init and template-update, hooks.
- `plugins/workbench-infra`, `plugins/workbench-observability`, `plugins/workbench-secrets`:
  optional packs.
