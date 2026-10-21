# workbench-infra

Optional infrastructure pack for the workbench template. It requires the workbench core plugin.

## What it adds

| Agent | Model | Does |
|---|---|---|
| `tf-planner` | sonnet | `terraform plan` one discovered root module (a directory with `*.tf` and a backend or provider block); create/update/destroy summary, never applies |
| `helmfile-differ` | sonnet | `helmfile diff` releases in a discovered helmfile directory; stages read from the helmfile; compressed summary, never applies |

Both agents find the workbench root at run time (`git rev-parse --show-superproject-working-tree`, else `git rev-parse --show-toplevel`) and ask the core's locator (`plugins/workbench/scripts/lib/workbench.py root` or `components`) which components exist. They work on any layout. Credentials come from the repo's documented secret loader (the workbench-secrets pack's `secrets-env` skill when enabled).

## Requires the workbench core plugin

The pack calls the core's locator script and relies on its guard hooks. Enable the core first.

## Enable

In `.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "workbench@workbench-template": true,
    "workbench-infra@workbench-template": true
  }
}
```

## Tests

`mise run test:pack-infra`
