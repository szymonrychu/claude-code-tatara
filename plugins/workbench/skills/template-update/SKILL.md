---
name: template-update
description: >
  Update an initialised workbench from its template: fetch the template, merge its tooling
  (plugins, scripts, mise tasks) and keep this workbench's own docs, memory and project
  files. Runs the tested engine through mise, makes one commit and pushes nothing. Use
  when the user says "update from the template", "pull template updates", "refresh the
  workbench from the template" or "get the latest template".
---

# template-update

The engine is tested python at the workbench root, outside the plugin. Call it only through
the mise task below, from the workbench root. Never call a script path. Never push.

## Run

Ask the user nothing on the normal path. Run:

    mise run init:update

Add `-- --url <url>` or `-- --branch <branch>` only when the user named a template URL or
branch (for example `mise run init:update -- --url <url> --branch next`).

## Report

On success, say in a few lines:

- the one commit the engine made: subject and sha;
- the template sha it merged;
- every `kept project side:` file the engine printed (instance-owned files whose template
  change was dropped);
- that nothing was pushed.

## Refusals

The engine refuses before changing anything, or aborts cleanly. Relay it, do not work around it.

- Uninitialised workbench: say to run `init` first.
- Dirty tree: list the paths and stop. Do not stash or commit them for the user.
- Conflicts outside the known paths: list them and name the manual route: merge
  `template/<branch>` by hand, resolve, then `mise run init:refresh`.
- Lint failure: show the tail of the output and stop.
- Already up to date: say so; there is no commit.

## Unrelated history

When the workbench shares no history with the template, the engine prints a `candidate base`
and the rerun line. Show the candidate to the user and ask them to confirm it. This is the
only question this skill asks. On confirmation, rerun:

    mise run init:update -- --base <sha>

Keep any `--url` or `--branch` from the first run. If there is no candidate, ask the user for
the template commit the project was copied from.
