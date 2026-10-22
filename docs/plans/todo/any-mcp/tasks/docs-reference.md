---
title: Docs reference
status: todo
repo: any-mcp
value: "Every config key, flag and transport behaviour has one documented meaning"
files: [docs/configuration.md, docs/transports.md, tests/test_docs_reference.py]
verify: "uv run --frozen pytest tests/test_docs_reference.py -q && mise run lint"
depends_on: [http-transport]
owns: []
uses: [any-mcp-config, any-mcp-cli]
model: sonnet
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Docs reference

## Requirement

Write the configuration and transport references (design D5, D10, D14).

- `docs/configuration.md` sections: `File format`, `Environment variables` (`${VAR}`, `${VAR:-default}`, `ANY_MCP_CONFIG`), `server`, `tools`, `plugins`, `Exit codes`. Every config key appears as its dotted path in backticks (for example `server.http.bearer_token`) with type, default and meaning.
- `docs/transports.md` sections: `stdio`, `Streamable HTTP` (host, port, path, Origin, bearer token), `Protocol versions` (2026-07-28 and handshake-era clients), `Tool list changes` (what the adapter sends per era, from the fastmcp-adapter probe notes, and that correctness never depends on it), `Security` (no credential forwarding, loopback default), `Registering with Claude Code` (`claude mcp add --scope user any-mcp -- any-mcp --config <path>`, a `.mcp.json` stdio entry, `--mcp-config`).
- Every CLI flag of `build_parser()` appears in one of the two pages.
- `tests/test_docs_reference.py` walks the config models recursively and checks every dotted key is documented, and checks every CLI flag is documented.

## Acceptance conditions

- AC1: every config key path of the config models is documented in configuration.md [evidence: test:tests/test_docs_reference.py::test_every_config_key_documented]
- AC2: every CLI flag is documented in configuration.md or transports.md [evidence: test:tests/test_docs_reference.py::test_every_cli_flag_documented]
- AC3: the configuration reference has an Exit codes section [evidence: doc-section:docs/configuration.md#Exit codes]
- AC4: the configuration reference has an Environment variables section [evidence: doc-section:docs/configuration.md#Environment variables]
- AC5: the transport reference has a Streamable HTTP section [evidence: doc-section:docs/transports.md#Streamable HTTP]
- AC6: the transport reference has a Tool list changes section [evidence: doc-section:docs/transports.md#Tool list changes]
- AC7: the transport reference has a Registering with Claude Code section [evidence: doc-section:docs/transports.md#Registering with Claude Code]
- AC8: lint passes [evidence: command:mise run lint]

## Files

- `docs/configuration.md`
- `docs/transports.md`
- `tests/test_docs_reference.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
