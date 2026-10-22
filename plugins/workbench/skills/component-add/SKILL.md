---
name: component-add
description: >
  Add one component to an initialised workbench: a new scaffolded one, an existing
  checkout or an existing repo URL, with its origin, as a submodule under code/. Use when
  the user says "add a component", "add a service", "add this repo to the workbench".
---

# component-add

Call the engine only through the mise task, which runs from the workbench root whatever
the cwd. Never call a script path.

## 1. Ask

- New component (name and language) or an existing checkout path or repo URL?
- Component name if the default is wrong, and its role in one line.
- Remote mode: `github`, `gitlab`, `url:<url>` or `local-bare[:<dir>]`; owner or group and
  visibility for a forge. For an existing checkout, `local-bare[:<dir>]` is accepted only
  with `--path` on a checkout that has no origin, and never with `--url`.

## 2. Confirm forge creation

A github or gitlab origin creates a repo. Say exactly what (owner, name, visibility) and
get an explicit yes. Pass `--confirm-forge` only after that yes.

## 3. Run

```sh
mise run component:add -- --component <name>:<lang> --remote <mode> --role <name>=<text>
mise run component:add -- --path <checkout> --name <name> --role <name>=<text>
mise run component:add -- --url <repo-url> --name <name> --role <name>=<text>
```

`--path` moves the checkout into `code/<name>`; the original path no longer exists
afterwards, so tell the user before running it.

Add `--confirm-forge`, `--forge-owner` and `--public` when answered. The engine refuses
when the workbench has staged changes, the name is taken or invalid, or the remote is
unusable; relay the message and fix the cause.

## 4. Report

Update the `workbench:project` block of `AGENTS.md` if the engine left the component's role
as a placeholder. State the commit and suggest `mise run doctor`.
