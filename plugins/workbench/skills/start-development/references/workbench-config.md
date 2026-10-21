# Per-repo workbench config

Location: `<repo>/.claude/workbench.json`, at the git top-level of the repo. A JSON
object; every key is optional. An unknown key, a wrong type or malformed JSON is an
error naming the file and the key. Only `${CLAUDE_PLUGIN_ROOT}/scripts/lib/workbench.py` parses it
(`load_config`, `config_for_repo`, or the CLI
`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lib/workbench.py config [--repo <dir>] [--plans-root <dir> --repo-name <name>]`).

```json
{
  "refRunners": {"*.go": "go test ./... -run {name}", "tests/*.bats": "bats {file}"},
  "suites": ["make test", "make lint"],
  "deploy": {"command": "make deploy", "verify": "make smoke"},
  "overlapIgnore": ["docs/**", "*.lock"]
}
```

## Keys

- `refRunners`: glob to command template for an acceptance-condition test ref.
  Placeholders: `{ref}` the whole ref, `{file}` the file path, `{name}` the test name,
  `{pkg}` the basename of the nearest package directory (not its path). The command
  already runs with that package root as cwd, so a `cd {pkg}` template is wrong. A glob
  without `/` matches the basename of the ref's file, so `*.go` matches `pkg/x_test.go`.
  Overrides the built-in runners (pyproject.toml,
  package.json, package.xml). Read by verify-task and the plan lint (validate-tasks).
- `suites`: shell commands the merger runs as the repo's test suites after the fast-forward
  (skip with `--no-suites`; a failing suite exits 4 and leaves the merge in place).
  Read by worktree-merge (merge.py).
- `deploy`: `{command, verify}`, both shell strings; deploy after merge, then verify.
  Read by the deploy hook.
- `overlapIgnore`: globs of doc files whose overlap never forces `dependsOn` and whose
  merge conflicts the merger union-merges. Read by validate-tasks, plan-execute and
  worktree-merge. Your list is appended to the defaults.

## Default overlapIgnore

`*README.md`, `MEMORY.md`, `**/SKILL.md`, `tests/README.md`, `CHANGELOG.md`.

Glob rules: `**/` matches zero or more directories; a pattern without `/` matches the
basename.
