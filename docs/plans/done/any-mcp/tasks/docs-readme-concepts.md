---
title: Docs README concepts
status: done
repo: any-mcp
value: "A README that installs and runs any-mcp in a minute, and a concepts guide"
files: [README.md, docs/concepts.md, tests/test_docs_links.py]
verify: "uv run --frozen pytest tests/test_docs_links.py -q && mise run lint"
depends_on: [docs-authoring, docs-reference]
model: sonnet
review: ""
verified_head: b51a31886360dd2981d51350e29364f0d13d6c95
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: 4
actual_tokens: 880389
actual_roles: "impl 3, review 2"
actual_role_tokens: "impl 722391, review 157998"
---

# Docs README concepts

## Requirement

Write the README and the concepts guide (design D14, D18).

- `README.md` sections: `What it is` (MCP-to-API proxy, does nothing on its own, plugins provide the business logic), `Installation` (also an `Agent hook install` paragraph with the exact line `python -m venv /opt/any-mcp && /opt/any-mcp/bin/pip install "any-mcp @ git+https://github.com/szymonrychu/any-mcp@v0.1.0"`, the console script `/opt/any-mcp/bin/any-mcp`, and that the config file may be JSON; design D20; Python >= 3.12; the same install forms as claude-code-wrapper's README, verbatim shape: `pip install any-mcp` from a package index, `pip install git+https://github.com/szymonrychu/any-mcp`, the pinned form `pip install "any-mcp @ git+https://github.com/szymonrychu/any-mcp@v0.1.0"`, `pip install .` from a checkout, `pipx install any-mcp`, `uv tool install any-mcp`, then `any-mcp --version`; the index forms `pip install any-mcp`, `pipx install any-mcp` and `uv tool install any-mcp` are marked in the README as "once published to an index; until then use the git forms"), `Quickstart` (the hello plugin, its config, `any-mcp --config any-mcp.yaml`, and the `claude mcp add` line), `Examples`, `Documentation` (links to `docs/concepts.md`, `docs/plugin-authoring.md`, `docs/testing-plugins.md`, `docs/configuration.md` and `docs/transports.md`, which exist by then), `License`.
- `docs/concepts.md` sections: `Plugins`, `Hooks` (each hook, its default, when to override), `Call pipeline`, `Reload`, `Tool names`, `Errors`, `Security`.
- `tests/test_docs_links.py`: every relative link in `README.md` and `docs/*.md` resolves to a file and, for `#anchor` links, to a heading; the README quickstart plugin block equals `examples/hello/hello.py` and its YAML block loads with `load_config`; the README Installation block contains all six install commands and `any-mcp --version`.

## Acceptance conditions

- AC1: the README has an Installation section [evidence: doc-section:README.md#Installation]
- AC2: the README has a Quickstart section [evidence: doc-section:README.md#Quickstart]
- AC3: the concepts guide has a Call pipeline section [evidence: doc-section:docs/concepts.md#Call pipeline]
- AC4: the concepts guide has a Hooks section [evidence: doc-section:docs/concepts.md#Hooks]
- AC5: the concepts guide has a Security section [evidence: doc-section:docs/concepts.md#Security]
- AC6: every relative link and anchor in README.md and docs resolves [evidence: test:tests/test_docs_links.py::test_relative_links_resolve]
- AC7: the README quickstart plugin equals examples/hello/hello.py and its config loads [evidence: test:tests/test_docs_links.py::test_readme_quickstart_matches_example]
- AC8: the README Installation block lists pip from an index, pip from git, the pinned tag, pip from a checkout, pipx and uv tool, and any-mcp --version, and marks the index install forms (pip install any-mcp, pipx, uv tool) as "once published to an index; until then use the git forms" [evidence: test:tests/test_docs_links.py::test_readme_install_forms]
- AC9: concepts explains every hook's default and when to override it in plain terms [evidence: judgement]
- AC10: lint passes [evidence: command:mise run lint]

## Files

- `README.md`
- `docs/concepts.md`
- `tests/test_docs_links.py`

## Interfaces

None in code. Pages other docs link to: `README.md`, `docs/concepts.md`.

## Expected outcome

A reader learns what any-mcp is, installs it, and runs a working plugin from the README alone; concepts explains the model behind it.

## Steps

- Write `tests/test_docs_links.py`; run `uv run --frozen pytest tests/test_docs_links.py -q`; expect failures.
- Write `README.md` and `docs/concepts.md`; rerun (all pass), then `mise run lint`.

## Ruling

- 2026-10-22 accepted: gate-repeat on a parking-wording false positive: README.md:11-19 'once published to an index; until then use the git forms' is mandated verbatim by the task requirement (AC8) and pinned by test_readme_install_forms; it states a real condition, defers no work. Verified on b51a318: 5 passed, lint clean.

## Notes

This task runs after docs-authoring and docs-reference, so its link test covers every page. Mirror the claude-code-wrapper README Installation layout (`code/claude-code-wrapper/README.md` lines 40-54). No PyPI publishing is in scope; the index form is documented because the package is a standard one.

- 2026-10-23 run any-mcp: dependency-failed on docs-authoring, docs-reference
