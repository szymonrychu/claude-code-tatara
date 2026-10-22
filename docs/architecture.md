# Architecture

## Components

```
claude-code-tatara/
  code/
    claude-code-wrapper/  (python)
    any-mcp/  (python)
    agent-orchestrator/  (python)
    agents-helmfile/  (generic)
```

- `code/claude-code-wrapper` (python): HTTP microservice that runs long-lived interactive Claude Code sessions under PTYs and exposes turns, an SSE event stream and lifecycle hooks
- `code/any-mcp` (python): MCP server that exposes any API as MCP tools through a plugin system (stdio and streamable HTTP)
- `code/agent-orchestrator` (python): Web UI and headless API orchestrating Kubernetes pods of claude-code-wrapper agents: clusters, round-robin dispatch, chat history (Python backend, React frontend, helm chart)
- `code/agents-helmfile` (generic): helmfile managing namespace agents: CNPG database and the agent-orchestrator release, applied with local mise tasks
