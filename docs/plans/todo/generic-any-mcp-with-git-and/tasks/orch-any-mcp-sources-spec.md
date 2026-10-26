---
title: orch any-mcp sources spec
status: todo
repo: agents-orchestrator
value: presets and sessions carry a validated list of extra plugin sources
files: [src/agents_orchestrator/spec.py, openapi.json, README.md, MEMORY.md, tests/test_spec_any_mcp_sources.py]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_spec_any_mcp_sources.py tests/test_readme_api.py tests/test_sessions_repo.py && mise run lint"
depends_on: [orch-any-mcp-0-5-0-pin]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 977684
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch any-mcp sources spec

## Requirement

Goal G4 (epic README), verbatim: "agents-orchestrator renders the orchestrator plugin from the plugins repo at a pinned ref and accepts a list of extra plugin sources per preset and session, installed in agent pods." User request, verbatim: "In webUI add ability to provide links to such plugins (defined by repo, or dir in repo in git ref) (plus button, shows line textbox where it can be pasted- multiple plugins can be provided)." Design D8, verbatim: "`SessionSpec.any_mcp_sources: list[str] | None = None`, sparse and create-time (name avoids `spec.wrapper.plugins`). Validation: at most 20 entries of at most 500 characters (my call, the init_scripts caps' shape), each parsed by `any_mcp.sources.parse_source`; only `git::https://` and `github.com/` sources (gate Q1); each source renders as the plugin entry `{name, source}` with the name derived from the last subdir segment, else the repo name without `.git`, lower-cased, characters outside `[a-z0-9_-]` replaced by `-`, cut to 20 (my call); a name that does not match any-mcp's name pattern, repeats another derived name, equals `orchestrator`, or equals a plugin name of the effective any-mcp config (the spec's, else the settings default) is an error naming the index. ... `any_mcp_config` plugin entries with a `source` follow the same remote-only rule (gate Q1). No host allowlist (gate Q2)."

Scope (agents-orchestrator):
- `src/agents_orchestrator/spec.py`: the field, `ANY_MCP_SOURCES_MAX = 20`, `ANY_MCP_SOURCE_MAX_CHARS = 500`, a field validator (count, length, non-empty, any-mcp's parser, remote https only), `source_plugin_name(source: str) -> str` (used by task orch-render-plugin-sources), and in `validate_spec` the name checks against the effective any-mcp config and the remote-only rule for `any_mcp_config` entries with a `source`.
- `openapi.json`: regenerated (`uv run python -m agents_orchestrator.api.openapi > openapi.json`).
- `README.md`: the spec field in the session spec documentation, with the accepted forms and the name rule.
- `MEMORY.md`: a dated entry for the derived names and the remote-only rule, with the why.
- New `tests/test_spec_any_mcp_sources.py`.

## Acceptance conditions

- ac1: a preset or session spec without any_mcp_sources stores and returns no such key [evidence: test:tests/test_spec_any_mcp_sources.py::test_sparse_when_unset]
- ac2: git::https and github.com/ sources validate and round-trip in order [evidence: test:tests/test_spec_any_mcp_sources.py::test_remote_sources_accepted]
- ac3: local paths, git::ssh, git::file and any string any-mcp's parser refuses are errors naming the index and the reason [evidence: test:tests/test_spec_any_mcp_sources.py::test_refused_sources]
- ac4: more than 20 entries, an entry over 500 characters and an empty entry are refused [evidence: test:tests/test_spec_any_mcp_sources.py::test_caps]
- ac5: the derived name is the last subdir segment, else the repo name without .git, lower-cased, other characters replaced by -, cut to 20 [evidence: test:tests/test_spec_any_mcp_sources.py::test_source_plugin_name]
- ac6: a derived name that is invalid, repeated, equal to orchestrator, or equal to a plugin name of the spec's any_mcp_config, else of the settings default config, is refused naming the index [evidence: test:tests/test_spec_any_mcp_sources.py::test_name_collisions_refused]
- ac7: any_mcp_config plugin entries with a local or non-https source are refused [evidence: test:tests/test_spec_any_mcp_sources.py::test_any_mcp_config_sources_remote_only]
- ac8: creating a preset with an invalid source answers 422 naming any_mcp_sources and the index [evidence: test:tests/test_spec_any_mcp_sources.py::test_api_refuses_invalid_source]
- ac9: openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- ac10: README documents the field [evidence: command:grep -qF 'any_mcp_sources' README.md]
- ac11: lint passes [evidence: command:mise run lint]

## Files

- `src/agents_orchestrator/spec.py`
- `openapi.json`
- `README.md`
- `MEMORY.md`
- `tests/test_spec_any_mcp_sources.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
