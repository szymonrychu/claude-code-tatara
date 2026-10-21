---
name: component-remove
description: >
  Remove one component from an initialised workbench, only when nothing would be lost.
  Explains every refusal. Use when the user says "remove a component", "drop this
  service", "detach this repo from the workbench".
---

# component-remove

Call the engine only through the mise task, which runs from the workbench root.

## 1. Ask

Which component (its name under `code/`)? Restate that the submodule and its checkout
leave the workbench and ask for a yes.

## 2. Run

```sh
mise run component:remove -- --name <name>
```

## 3. Refusals

The engine checks everything before changing anything and refuses, with nothing changed,
when the component has state that exists nowhere else. Explain each one it names:

- Not a component of this workbench: the name is wrong; list the entries under `code/`.
- Not checked out: its local state cannot be verified; check it out first.
- Uncommitted or untracked changes: commit or discard them.
- Commits that are not on any remote branch: push them.
- Stashes: they are never pushed; apply or drop them.
- Linked worktrees: remove them first.
- The workbench has staged changes: commit or unstage them first.

Never work around a refusal by deleting by hand. Once the user has resolved the cause,
rerun.

## 4. Report

State the commit and that the component's row left the `workbench:project` block; suggest
`mise run doctor`.
