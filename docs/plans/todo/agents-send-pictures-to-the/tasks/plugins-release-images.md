---
title: plugins release images
status: todo
repo: any-mcp-tatara-plugins
value: the picture tool ships as a plugins release the orchestrator and helmfile can pin
files: [orchestration/orchestrator/pyproject.toml, uv.lock, orchestration/orchestrator/README.md, tests/test_source_install.py]
verify: "uv run --frozen pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint"
depends_on: [plugin-chat-send-image]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 545296
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# plugins release images

## Requirement

README Goal G5, verbatim: "released and deployed in order (plugins, connector, orchestrator, web, helmfile) and proven by a live smoke that posts one real picture with a caption to the owner's Messenger DM."

Design D9, verbatim: "Placeholders, as hive-decoupling does: `<MIGRATION>` (next free connector migration), `<TAG>`/`<VERSION>` (next free plugins minor, expected v0.6.0). The first task that needs one reads the real number from main at build time and amends the dependent tasks (`ticket.py amend`); no number is assumed."

User decision (binding), verbatim: "Release numbers are placeholders resolved at build time, exactly as /workdir/workdir/docs/plans/in-progress/hive-decoupling does (read its design.md 'Build-time settlements' and tasks orch-activity-route, plugins-release-0-4-0, orch-plugins-pin-0-4-0, helmfile-deploy-pin for the pattern): <MIGRATION> for the connector migration (0003 is claimed by immediate-message-delivery-w), <TAG>/<VERSION> for the plugins release (v0.3.0-v0.5.0 claimed). The first task needing each reads it from main and amends dependents."

Repo README `## Releases`: releases are `vX.Y.Z` tags on `main`; pins use `?ref=` to a release tag; nothing is published beyond the tag.

This is the first task that needs `<TAG>` and `<VERSION>`. Before the first implementer is dispatched the orchestrator session (not a subagent: `ticket.py amend` and `git ls-remote` are its tools) reads the newest `vX.Y.Z` tag on the any-mcp-tatara-plugins origin (`git ls-remote --tags https://github.com/szymonrychu/any-mcp-tatara-plugins 'v*'`), takes the next minor, and replaces `<TAG>` (with the `v`) and `<VERSION>` (without it) by `ticket.py amend` in this task, orch-plugins-pin-and-tool and helmfile-pictures-pin (Requirement and acceptance conditions), and edits the same placeholders in their bodies. The task slug keeps its name.

Scope (any-mcp-tatara-plugins):
- `orchestration/orchestrator/pyproject.toml`: version `<VERSION>`; `uv lock` updates `uv.lock`.
- `orchestration/orchestrator/README.md`: the example source pins `?ref=<TAG>`.
- `tests/test_source_install.py::test_orchestrator_distribution_metadata` is no longer accurate (named): it pins the previous release version; it asserts `<VERSION>`.
- Release step, run by the orchestrator session (never a subagent) once this repo's PR is merged to `main` with green CI: `git tag <TAG> <merge sha> && git push origin <TAG>` (irreversible, listed in design.md). ac3 and ac4 are checked after that push; the task is not done before the tag exists.

## Acceptance conditions

- ac1: the plugin's pyproject and installed metadata say <VERSION> (updated, named) [evidence: test:tests/test_source_install.py::test_orchestrator_distribution_metadata]
- ac2: the plugin README example pins the new release and no older one [evidence: command:test "$(grep -oE "ref=v[0-9.]+" orchestration/orchestrator/README.md | sort -u)" = "ref=<TAG>"]
- ac3: (orchestrator session, after the push) tag <TAG> exists on origin at the main merge commit, whose CI is green [evidence: command:test -n "$(git ls-remote --tags origin <TAG>)"]
- ac4: (orchestrator session, after the push) the tagged tree carries the image tool [evidence: command:git fetch origin tag <TAG> && git show <TAG>:orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py | grep -q chat_send_image]
- ac5: (orchestrator session, before dispatch) the real next plugins minor read from origin replaces <TAG> and <VERSION> in this task, orch-plugins-pin-and-tool and helmfile-pictures-pin [evidence: judgement:orchestrator quotes the tag list read and a grep of the three task files showing no placeholder left]
- ac6: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint]

## Files

- `orchestration/orchestrator/pyproject.toml`
- `uv.lock`
- `orchestration/orchestrator/README.md`
- `tests/test_source_install.py`

## Interfaces

- Distribution `any-mcp-tatara-orchestrator` version `<VERSION>`; git tag `<TAG>` on the `main` merge commit.

## Expected outcome

The orchestrator plugin with `orchestrator_chat_send_image` is released as tag `<TAG>`, so the orchestrator and agents-helmfile can pin it.

## Steps

- Orchestrator session, before dispatch: read the tags (`git ls-remote --tags https://github.com/szymonrychu/any-mcp-tatara-plugins 'v*'`), take the next minor, amend the three tasks (ac5).
- Confirm `<TAG>` does not exist on origin and that `main` carries the newest tag; stop and report otherwise.
- Red: change `test_orchestrator_distribution_metadata` to `<VERSION>`; run `uv run --frozen pytest tests/test_source_install.py::test_orchestrator_distribution_metadata`: fails.
- Green: bump the plugin pyproject, `uv lock`, the README example; run the task's verify: passes. Quote the summary line.
- After the merge (orchestrator session): wait for CI green on the merge commit, `git tag <TAG> <merge sha> && git push origin <TAG>`, then check ac3 and ac4; only then mark done.

## Notes

- Dependency-bump TDD exception for the version values; the metadata test is the guard.
- `tests/test_source_install.py::test_orchestrator_plugin_installs_from_sources` fails in agent pods with git 2.39 (`--end-of-options`, baseline 2026-10-29); CI is the gate for it.
- Retro (deploy-safe-agent-sessions): a release once was marked done before its artifact existed; ac3 and ac4 prevent that here.
