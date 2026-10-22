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

Before running with a `--url` other than the default template URL (the one the engine
uses with no `--url`), show the user that URL and ask them to confirm it: the update runs that template's refresh and lint scripts on this machine before
it commits. Run only on confirmation.

Every run prints `template: <url> <branch> <commit>` before it merges; that is the source
actually used.

## Report

On success, say in a few lines:

- the one commit the engine made: the subject from its `committed <subject>` line, and the
  commit sha from `git rev-parse HEAD` (the engine does not print it);
- the template sha it merged: the 12-character sha in that subject, or the full sha in the
  `Template-Commit:` trailer (`git log -1 --format=%B`);
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
- `--url` differs from the existing `template` remote: show both URLs and the engine's
  `git remote set-url template <url>` line; changing the remote is the user's call.
- A `--branch` or `--base` value starting with `-`: relay the refusal.
- Local ignored files the template would overwrite (for example a note in `docs/research`):
  list them and ask the user to move them aside.

## Unrelated history

When the workbench shares no history with the template, the engine prints a `candidate base`
and the rerun line. Show the candidate to the user and ask them to confirm it. Besides the
non-default `--url` confirmation, this is the only other question this skill asks. On confirmation, rerun:

    mise run init:update -- --base <sha>

Keep any `--url` or `--branch` from the first run. If there is no candidate, ask the user for
the template commit the project was copied from.
