---
name: release
description: >
  Cut a release of the workbench plugin. For maintainers of the template's plugin only. Judges the size of the deliverable (major,
  minor, patch) from the commits since the newest v* tag, bumps plugin.json and
  the root marketplace.json entry, writes the CHANGELOG section, commits and creates an
  annotated tag locally. Use when the user asks to release, tag or bump the
  version. Never pushes.
---

# release

This skill is for maintainers of the template's `workbench` plugin. One script does the
whole release. It judges, you confirm, it writes. It finds the template root from its own
location (the root must hold `.claude-plugin/marketplace.json`) and errors clearly when run
from a copy outside a template tree. Plugin releases bump the one root marketplace, so
versions never disagree.

```sh
python3 "${CLAUDE_PLUGIN_ROOT}/skills/release/scripts/release.py" --dry-run
python3 "${CLAUDE_PLUGIN_ROOT}/skills/release/scripts/release.py" [--level major|minor|patch]
```

## Size

Commits since the newest `v*` tag (with no tag yet: since the last commit touching
"version" in `plugins/workbench/.claude-plugin/plugin.json`, else the root commit):

- **major**: any breaking commit (`type!:` subject or a `BREAKING CHANGE:` footer), or a
  commit that deletes a `plugins/workbench/skills/<name>/` directory or a
  `plugins/workbench/agents/<name>.md` file.
- **minor**: any `feat`.
- **patch**: everything else.

It prints the level and the commits that drove it. `--level` overrides; the override is
printed and recorded in the release commit body and the tag message.

## Steps

1. Run with `--dry-run`: read the level, drivers, next version and changelog section.
   Nothing is written.
2. If the judged level is wrong, re-run with `--level`.
3. Run for real. It bumps `version` in `plugins/workbench/.claude-plugin/plugin.json` and the `workbench`
   entry in the root `.claude-plugin/marketplace.json`, prepends `## vX.Y.Z - YYYY-MM-DD`
   to `plugins/workbench/CHANGELOG.md`
   (created if missing; Breaking / Features / Fixes / Other; `chore(ticket)` and
   `docs(record|plan)` commits omitted), commits `chore(release): vX.Y.Z`, then creates the
   annotated tag `vX.Y.Z` whose message is that section.

## Refusals

A dirty tree, a branch other than `main`, an existing tag `vX.Y.Z`, or no commits since the
range start. The script never pushes: pushing the commit and tag is the user's call.
