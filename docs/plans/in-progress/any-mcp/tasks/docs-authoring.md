---
title: Docs authoring
status: escalated
repo: any-mcp
value: A plugin authoring guide from small to big plugins whose samples are the tested examples
files: [docs/plugin-authoring.md, docs/testing-plugins.md, tests/test_docs_snippets.py]
verify: "uv run --frozen pytest tests/test_docs_snippets.py -q && mise run lint"
depends_on: [examples-big-group, input-required-adapter]
owns: []
uses: [plugin-harness, input-required-hook]
model: sonnet
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/any-mcp-docs-authoring/any-mcp
branch: any-mcp-docs-authoring
verified_head: 78faf4eeb3e7f8f3de762e26fc196bc49875ed64
run: any-mcp
provides: []
acs_for_audit: [AC9]
process_gaps: []
---

# Docs authoring

## Requirement

Write the plugin authoring guide (small and big plugins) and the testing guide (design D14).

- `docs/plugin-authoring.md` sections: `Small plugins`, `The hello plugin` (embeds `examples/hello/hello.py`), `A single endpoint` (embeds `examples/single_endpoint/zippopotam.py`), `Medium plugins` (the github_issues example: config model, credentials, before_call, shape_response), `Big plugins` (embeds `examples/petstore/src/petstore_plugin/__init__.py`; OpenAPIPlugin options), `Packaging a plugin` (entry point group `any_mcp.plugins`, `pip install -e`), `Groups of APIs` (embeds `examples/group/any-mcp.yaml`), `Asking the client for input` (the optional `request_input` hook, `InputRequired`, `call.input_responses` and `request_state`, the 2026-07-28-only caveat and the opaque-state note; embeds `examples/confirm_delete.py`), `Hook reference` (every hook signature and default).
- `docs/testing-plugins.md` sections: `The harness`, `Mocking HTTP`, `Testing a config`, each with a runnable snippet against the examples.
- Each embedded example is a fenced block preceded by `<!-- example: <path> -->` and equal to that file.
- `tests/test_docs_snippets.py`: marked blocks equal their files; every `python` block compiles; the `The harness` snippet of `docs/testing-plugins.md` runs (exec in an async test) against `examples/hello` and passes.

## Acceptance conditions

- AC1: the authoring guide has a Small plugins section [evidence: doc-section:docs/plugin-authoring.md#Small plugins]
- AC2: the authoring guide has a Big plugins section [evidence: doc-section:docs/plugin-authoring.md#Big plugins]
- AC3: the authoring guide has a Groups of APIs section [evidence: doc-section:docs/plugin-authoring.md#Groups of APIs]
- AC5a: the authoring guide has an Asking the client for input section with the confirm_delete example [evidence: doc-section:docs/plugin-authoring.md#Asking the client for input]
- AC4: the authoring guide has a Hook reference section [evidence: doc-section:docs/plugin-authoring.md#Hook reference]
- AC5: the testing guide has a The harness section [evidence: doc-section:docs/testing-plugins.md#The harness]
- AC6: every block marked with an example path equals that file [evidence: test:tests/test_docs_snippets.py::test_example_blocks_match_files]
- AC7: every python block in both guides compiles [evidence: test:tests/test_docs_snippets.py::test_python_blocks_compile]
- AC8: the harness snippet from the testing guide runs and passes against the hello example [evidence: test:tests/test_docs_snippets.py::test_testing_snippet_runs]
- AC9: a newcomer can write a single-endpoint plugin and a decorator plugin from the guide alone [evidence: judgement]
- AC10: lint passes [evidence: command:mise run lint]

## Files

- `docs/plugin-authoring.md`
- `docs/testing-plugins.md`
- `tests/test_docs_snippets.py`

## Interfaces

None in code. The `<!-- example: <path> -->` marker convention, shared with docs-reference.

## Expected outcome

The guide walks from a 10-line plugin to a packaged OpenAPI plugin, and every code sample in it is the code that CI tests.

## Steps

- Write `tests/test_docs_snippets.py`; run `uv run --frozen pytest tests/test_docs_snippets.py -q`; expect failures.
- Write both pages; rerun (all pass), then `mise run lint`. The docs-readme-concepts task links them from the README.

## Notes

Follow the simonw/llm plugin tutorial shape (prior-art D1): smallest working thing first, then one concept per section.

- 2026-10-23 run any-mcp: dependency-failed on examples-big-group, input-required-adapter
