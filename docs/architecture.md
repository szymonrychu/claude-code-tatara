# Architecture

## Components

```
claude-code-tatara/
  code/
    claude-code-wrapper/  (python)
    any-mcp/  (python)
    agent-orchestrator/  (python)
    agents-helmfile/  (generic)
    agents-web/  (typescript)
    agents-common/  (python)
    agents-webhook/  (python)
```

- `code/claude-code-wrapper` (python): HTTP microservice that runs long-lived interactive Claude Code sessions under PTYs and exposes turns, an SSE event stream and lifecycle hooks
- `code/any-mcp` (python): MCP server that exposes any API as MCP tools through a plugin system (stdio and streamable HTTP)
- `code/agent-orchestrator` (python): Web UI and headless API orchestrating Kubernetes pods of claude-code-wrapper agents: clusters, round-robin dispatch, chat history (Python backend, React frontend, helm chart)
- `code/agents-helmfile` (generic): helmfile managing namespace agents: CNPG database and the agent-orchestrator release, applied with local mise tasks
- `code/agents-web` (typescript): Web UI of the agents system (React/MUI SPA served as static files by nginx-unprivileged), reaching each backend (agent-orchestrator first) through its documented HTTP API on one host
- `code/agents-common` (python): Python library shared by the trigger services (agents-webhook, agents-schedule): settings, Postgres pool, migrator, guarded queue transitions, orchestrator client, run tracker
- `code/agents-webhook` (python): Python microservice with its own Postgres database that receives GitHub/GitLab PR, issue and comment webhooks and Grafana alerts, queues them FIFO with dedup and limits, and starts agent clusters from presets through the orchestrator API
