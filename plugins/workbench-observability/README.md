# workbench-observability

Optional pack for the workbench metarepo template. Read-only Kubernetes
diagnosis.

## Contents

- `skills/kubectl-logs-query` - read-only kubectl dig (pod logs, `--previous`
  crash logs, events, describe) for workloads whose logs are not in Loki.
- `agents/k8s-triage.md` (`k8s-triage`) - read-only cluster sweep that finds
  unhealthy workloads and reports the likely cause.

Both use the current kubectl context (`kubectl config current-context`) and
never switch it. `kubectl` and `stern` must be on PATH (mise-pinned in the
project when used).

## Requirements

Requires the workbench core plugin (`workbench`).

## Enable

Add the pack to the project's `.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "workbench@workbench": true,
    "workbench-observability@workbench": true
  }
}
```

## License

MIT, see `LICENSE`.
