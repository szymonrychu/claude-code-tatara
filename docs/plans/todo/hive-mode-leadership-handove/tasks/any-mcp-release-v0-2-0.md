---
title: any-mcp release v0.2.0
status: todo
repo: any-mcp
value: the orchestrator can install the plugin from a pinned tag
files: [pyproject.toml, uv.lock, CHANGELOG.md, README.md, tests/test_release.py]
verify: "uv run pytest tests/test_release.py -q -k 'versions_agree or pinned_install_line or workflow_shape' && uv run ruff check . && uv run ruff format --check ."
depends_on: [orchestrator-plugin]
owns: [any-mcp-release-v0-2-0]
uses: [any-mcp-orchestrator-plugin]
model: ""
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

# any-mcp release v0.2.0

## Requirement

Foundation part F1 release (X1): any-mcp v0.2.0 carries `OrchestratorPlugin`.

- `pyproject.toml` version `0.2.0`, `uv lock`.
- `CHANGELOG.md` top entry `## v0.2.0` describing the built-in orchestrator plugin (all nine tools by name, including orchestrator_scale and the init-script tools; config; credential handling).
- README and CHANGELOG pinned install line and onStart line say `@v0.2.0` (`python -m venv /opt/any-mcp && /opt/any-mcp/bin/pip install "any-mcp @ git+https://github.com/szymonrychu/any-mcp@v0.2.0"`).
- `tests/test_release.py`: version expectations `0.2.0`, `PINNED_LINE` at `v0.2.0`.
- Release step, run by the orchestrator once this epic's any-mcp PR is merged to `main`: push tag `v0.2.0` on the merge commit (irreversible, listed in design.md), confirm the release workflow is green and `pip install "any-mcp @ git+https://github.com/szymonrychu/any-mcp@v0.2.0"` installs; then amend `orch-pin-bumps` to the tag.

## Acceptance conditions

- AC1: pyproject, package metadata, the CHANGELOG top entry and the README pinned tag all say 0.2.0 [evidence: test:tests/test_release.py::test_versions_agree]
- AC2: README and CHANGELOG state the v0.2.0 pinned onStart install line [evidence: test:tests/test_release.py::test_pinned_install_line_documented]
- AC3: the CHANGELOG v0.2.0 entry names the orchestrator plugin [evidence: command:grep -q "^## v0.2.0" CHANGELOG.md && grep -qi "orchestrator" CHANGELOG.md && grep -q "orchestrator_scale" CHANGELOG.md && grep -q "orchestrator_init_scripts_edit" CHANGELOG.md]
- AC4: tag v0.2.0 exists on origin on the merge commit and its release workflow run is green [evidence: judgement:]
- AC5: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `pyproject.toml`
- `uv.lock`
- `CHANGELOG.md`
- `README.md`
- `tests/test_release.py`

## Interfaces

- Owns part `any-mcp-release-v0-2-0`: tag `v0.2.0` of `github.com/szymonrychu/any-mcp`, installable with `pip install "any-mcp @ git+https://github.com/szymonrychu/any-mcp@v0.2.0"`.

## Expected outcome

The repo says 0.2.0 everywhere; after the merge, tag v0.2.0 has a green release run.

## Steps

- Red: change the expectations in `tests/test_release.py` to 0.2.0; run `uv run pytest tests/test_release.py -q -k versions_agree`: fails.
- Green: bump pyproject, `uv lock`, CHANGELOG and README; run the verify command: passes.
- After merge (orchestrator): `git tag v0.2.0 <merge sha> && git push origin v0.2.0`; watch the release workflow with `gh run watch`.

## Notes

- `tests/test_release.py:16-19` (`PINNED_LINE`) and `:51-60` hard-code the version.
- The tag is pushed only from the merged `main` commit; never re-pointed.
