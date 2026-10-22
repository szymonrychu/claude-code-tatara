# Architecture

## Components

```
claude-code-tatara/
  code/
    claude-code-wrapper/  (python)
    any-mcp/  (python)
```

- `code/claude-code-wrapper` (python): HTTP microservice that runs long-lived interactive Claude Code sessions under PTYs and exposes turns, an SSE event stream and lifecycle hooks
- `code/any-mcp` (python): MCP server that exposes any API as MCP tools through a plugin system (stdio and streamable HTTP)
