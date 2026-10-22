# Architecture

## Components

```
claude-code-tatara/
  code/
    claude-code-wrapper/  (python)
```

- `code/claude-code-wrapper` (python): HTTP microservice that runs long-lived interactive Claude Code sessions under PTYs and exposes turns, an SSE event stream and lifecycle hooks
