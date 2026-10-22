---
title: Examples big group
status: todo
repo: any-mcp
value: A runnable packaged OpenAPI plugin and a group-of-APIs config users can copy
files: [examples/petstore/pyproject.toml, examples/petstore/src/petstore_plugin/__init__.py, examples/petstore/src/petstore_plugin/petstore.yaml, examples/petstore/any-mcp.yaml, examples/group/any-mcp.yaml, tests/test_examples_big.py]
verify: "uv run --frozen pytest tests/test_examples_big.py tests/test_import_boundary.py -q && mise run lint"
depends_on: [openapi-plugin, examples-small-medium]
owns: []
uses: [openapi-plugin, plugin-harness, any-mcp-cli, plugin-abc]
model: sonnet
estimate: 6
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

# Examples big group

## Requirement

Write the big example (a packaged OpenAPI plugin) and the group-of-APIs config, runnable and tested offline (design D12, D13, D4).

- `examples/petstore/`: an installable package. `pyproject.toml` (hatchling, depends on `any-mcp`, entry point `[project.entry-points."any_mcp.plugins"] petstore = "petstore_plugin:PetstorePlugin"`), `src/petstore_plugin/__init__.py` with `PetstorePlugin(OpenAPIPlugin)`: `name = "petstore"`, `Config` defaults `spec` to the packaged `petstore.yaml` (resolved with `importlib.resources`) and `allow` to `["listPets", "getPet", "createPet"]`, `reload_every = 300`, and a `shape_response` that projects pets to `id`, `name`, `status`; `src/petstore_plugin/petstore.yaml` (OpenAPI 3.0 with `servers: [{url: https://petstore.example.com/v1}]`).
- `examples/petstore/any-mcp.yaml` runs it by `module:Class` with `python_path: ["src"]`.
- `examples/group/any-mcp.yaml`: one server exposing hello, github_issues (namespace `gh`) and petstore together, with `python_path` pointing at the other example directories.
- `tests/test_examples_big.py` exercises both through `PluginHarness` with an `httpx.MockTransport`, checks the entry-point declaration resolves to `PetstorePlugin`, and lists the group's tools through the CLI offline.

## Acceptance conditions

- AC1: PetstorePlugin loads its packaged spec, exposes only the allowed operations, reloads every 300 seconds and projects pet fields through the harness [evidence: test:tests/test_examples_big.py::test_petstore_example]
- AC2: the petstore pyproject declares the any_mcp.plugins entry point and its target resolves to PetstorePlugin [evidence: test:tests/test_examples_big.py::test_petstore_entry_point_declared]
- AC3: the group config serves hello, gh and petstore tools together, sorted and prefixed [evidence: test:tests/test_examples_big.py::test_group_config]
- AC4: any-mcp --list-tools on the group config succeeds offline [evidence: test:tests/test_examples_big.py::test_group_cli_list_tools]
- AC5: the import boundary holds and lint passes [evidence: command:uv run --frozen pytest tests/test_import_boundary.py -q && mise run lint]

## Files

- `examples/petstore/pyproject.toml`
- `examples/petstore/src/petstore_plugin/__init__.py`
- `examples/petstore/src/petstore_plugin/petstore.yaml`
- `examples/petstore/any-mcp.yaml`
- `examples/group/any-mcp.yaml`
- `tests/test_examples_big.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
