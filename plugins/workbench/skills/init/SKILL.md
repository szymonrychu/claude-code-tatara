---
name: init
description: >
  Turn this workbench template into a project: a new one with fresh components, or an
  adoption of existing checkouts, repo URLs or a monorepo. Asks the questions, confirms
  forge creation and runs the tested engine through mise, which generates harness files and
  fills the project block of AGENTS.md in one commit. Use when the user says "start a project", "new
  project", "adopt this repo", "init the workbench" or opens a fresh clone of the template.
---

# init

The engine is tested python that lives at the workbench root, outside the plugin. Call it
only through the mise tasks below. They run from the workbench root whatever the cwd, and
relative `--path` values resolve against where you ran them. Never call a script path.

## 1. Ask (one short question group at a time)

- New project or adopt existing code?
- Project name and purpose (one sentence).
- New: each component as `name` and language (python, go, node, ...) and its role.
  Adopt: each checkout path or repo URL, a component name if the default is wrong, a role.
  A monorepo is adopted as one component.
- Remote mode. New: `github`, `gitlab`, `url:<url>` or `local-bare[:<dir>]`; for a forge,
  the owner or group and whether repos are public (default private). Adopt: only
  `local-bare[:<dir>]` or none (adopted repos keep their own origin; forges are for new).
  Adopt accepts `local-bare[:<dir>]` only with `--path` on a checkout that has no origin,
  and never with `--url`.
- Packs to enable: infra, observability, secrets (optional).
- Harnesses to generate for besides Claude Code: copilot, cursor, codex, gemini,
  antigravity (optional).
- License: `mit` (and the holder, which defaults to the git author; it is written into the root LICENSE and every plugins/*/LICENSE), `none`, or a license file to copy.
- Hard rules every component obeys, and the highest-risk surface (optional).
- A deploy command and a command that verifies it (optional).

## 2. Confirm forge creation

This applies to `init:new` with a forge remote; adopt never creates forge repos.
Creating repos on github or gitlab has real side effects. State exactly what will be
created (owner, repo names, visibility) and ask the user to confirm explicitly. Pass
`--confirm-forge` only after an explicit yes; without it the engine refuses forge modes.
Other remote modes need no confirmation.

## 3. Run the engine

```sh
mise run init:new -- --name <project> --component <name>:<lang> --remote <mode> --purpose "<text>" --role <name>=<text> --pack <pack> --harness <target> --license mit --license-holder "<holder>"
mise run init:adopt -- --path <checkout> --name <component> --project <project> --purpose "<text>" --role <name>=<text>
mise run init:adopt -- --url <repo-url> --name <component> --project <project>
```

`--path` moves the checkout into `code/<name>`; the original path no longer exists
afterwards, so tell the user before running it.

Repeat `--component`, `--role`, `--hard-rule`, `--pack` and `--harness` as needed. For
`init:new` add `--confirm-forge` (after step 2), `--forge-owner` and `--public` when
answered. For both add `--risk`, `--deploy-command` and `--deploy-verify` when answered;
`init:adopt` has no forge flags. For several adopted repos run
`init:adopt` once for the first and `component-add` for the rest. If the engine refuses,
show its message, fix the input and rerun; nothing is half-applied on a refusal.

## 4. Harnesses and the AGENTS.md project block

Both happen inside the engine's one init commit, so do not run `harness-setup` or edit
`AGENTS.md` afterwards. Harness files are generated for the `--harness` targets before the
commit. The `workbench:project` block of `AGENTS.md` is filled from the answers collected in step 1, so collect the
purpose, roles, hard rules and highest-risk surface before step 3 and pass them as
`--purpose`, `--role`, `--hard-rule` and `--risk`. Ask for anything you still lack first.
Afterwards `git status` is clean and `mise run lint` passes; if a line is still
`_Filled by init ..._`, an answer was missing: rerun with it instead of editing and
committing separately.

## 6. Report

State the one commit the engine made (component add and remove each end in one commit too), the components and where their origins are, and next
steps: `mise run doctor` to check the setup, and push only when the user wants it.
