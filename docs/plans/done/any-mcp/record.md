# any-mcp record

## Summary

Asked: any-mcp, a Python MCP server that exposes any API or group of APIs as MCP tools through a plugin ABC (stdio default, streamable HTTP, FastMCP 4.x behind one adapter), with docs, examples, pip/git install and tag v0.1.0.
Shipped: 30 task files, all `done` (28 planned + 2 discovered: python 3.12 pin, http client aclose; the 5 post-review security/hardening tasks are among the 30). All landed in PR #1 (merged as 2b9cc65), tag v0.1.0 pushed, release workflow run succeeded. Full suite on the tip: 202 passed (`full-suite2.log`), lint clean (62 files formatted).
Verdict: pass (whole-diff review, security pass, scope audit A-J landed). Open items: see Discovered and blocked (nothing undelivered; several runtime behaviours were never exercised live).

## Planned vs built

Status, rounds and verifier head are read from the plan-execute returns (return1-5) and checked against `git log origin/main` for the code/any-mcp repo. "Red" is the implementer's own `tests.red` run; no `tdd-revert` output is quoted anywhere. Where the verifier's evidence was only merge.py's `verify: pass <cmd>` line, the pytest count shown is the implementer's `selfVerification` and is labelled (self). No task ended without a verifier head, so none is `unverified`; earlier returns that listed tasks as `dependency-failed` or `impl-agent-died` were superseded by later runs (rows below use the final run).

| Task | Status | Rounds | Files | Verifier head | Verification tail / red |
|---|---|---|---|---|---|
| scaffold | done | 2 | README.md (+ scaffold) | da45c0d | `verify: pass` test_package + lint; 4 passed (self). No red: doc exception |
| core-types | done | 1 | types.py, errors.py, test_types.py | 162fcc2 | pass; 5 passed (self). Red: collection error on missing module |
| response-shaping | done | 0 | response.py, test_response.py | 5806230 | pass; 8 passed (self). Red: ModuleNotFoundError any_mcp.response |
| config-model | done | 0 | config.py, test_config.py | bf625c2 | pass; 10 passed (self). Red: collection error |
| http-binding | done | 2 | http.py, test_http_binding.py | d93aa22 | pass; 8 passed (self). Red: 1 failed, 7 passed (credentials case-insensitive) |
| schemas-and-validation | done | 3 | schema.py, test_schema.py | ecfba3d | pass; 11 passed (self). Red: 1 failed, 10 passed (root self-ref) |
| plugin-abc | done | 3 | plugin.py, test_plugin.py | 6f038a3 | pass; 13 passed (self). No red for the bytes fix (self-reported, process gap) |
| plugin-discovery | done | 2 | discovery.py, test_discovery.py | f3d1086 | pass; 8 passed (self). Red: 1 failed, 7 passed (import-time failure) |
| registry | done | 1 | registry.py, test_registry.py | 81e3ae5 | pass; 8 passed (self). Red: ModuleNotFoundError any_mcp.registry |
| call-pipeline | done | 2 | validation.py, pipeline.py, test_pipeline.py | 3a3161b | pass; 10 passed (self). No red: round-2 fixes written test-after (process gap) |
| input-required-core | done | 2 | plugin.py (docstring) | 2782d30 | pass; 28 passed (self). No red: doc exception |
| fastmcp-adapter | done | 1 | _fastmcp_adapter.py, test_adapter.py, test_import_boundary.py | 58ff97c | pass; 11 passed, 1 warning (self). Red: ModuleNotFoundError + 1 failed, 1 passed |
| cli-stdio | done (ruled) | 1, stopped fix-agent-died | cli.py, __main__.py, log.py, test_cli.py, fixtures | cf2da99 | `11 passed in 7.77s`, lint clean (verifier evidence). No red: CLI written first, tests after |
| testing-harness | done | 2 (no-progress, re-run 1) | testing.py, test_testing_harness.py | 7e77db3 (first run f01a60a: 13 passed) | pass; 13 passed (self). Red (first run): 3 failed, 8 passed |
| http-transport | done | 2 | config.py, _fastmcp_adapter.py, test_http_transport.py | cfe0936 | pass; 30 passed (self). Red: empty bearer 1 failed, 8 deselected |
| openapi-plugin | done (re-run) | 1 | openapi.py, context.py, discovery.py, test_openapi.py, fixtures | 5d7213c | pass; 10 passed (self). Red: ModuleNotFoundError any_mcp.openapi |
| examples-small-medium | done | 1 | examples/hello, single_endpoint, github_issues, test_examples_small.py | 2fbcb27 | pass; 7 passed (self). No red |
| examples-big-group | done | 1 | examples/petstore, examples/group, test_examples_big.py | 11ffef9 | pass; 6 passed (self). No red (process gap) |
| input-required-adapter | done | 2 | examples/confirm_delete.py, test_input_required_transports.py | 8a45132 | pass; 17 passed (self). Red: mutation run (state dropped) 1 failed, 5 deselected |
| uv-picks-cpython-3-15-for-th | done (discovered) | 1 | .python-version, test_package.py | 45351e7 | pass; 6 passed (self). Red: 2 failed, 4 passed ((3,15) != (3,12)) |
| nothing-ever-calls-aclose-on | done (discovered) | 3 | test_discovery.py (source already correct) | 89302aa | pass; 32 passed (self). No red; mutation check claimed, not re-run by reviewer |
| docs-authoring | done (ruled) | 3, stopped gate-repeat | docs/plugin-authoring.md | 78faf4e | `3 passed in 0.69s`, lint clean (verifier evidence). No red: doc exception |
| docs-reference | done (ruled) | 2, stopped gate-repeat | docs/transports.md | c967152 | `4 passed in 1.06s`, lint clean (verifier evidence). No red: doc exception |
| docs-readme-concepts | done (ruled) | 2, stopped gate-repeat | README.md | b51a318 | `5 passed in 0.13s`, lint clean (verifier evidence). No red: doc exception |
| release | done | 2 | CHANGELOG.md, tests/test_release.py | 9e90317 | pass; 7 passed in 21.09s (self). No red: fix removes a skip marker |
| workflow-hardening | done | 1 | ci.yml, release.yml, test_release.py | 5a6d804 | pass; 9 passed (self). Red: 2 failed, 7 deselected |
| openapi-credential-hosts | done | 1 | openapi.py, http.py, tests | 4ece80b | pass; 22 passed (self). Red: 4 failed, 18 passed |
| bounded-upstream-bodies | done | 2 | http.py, plugin.py, test_plugin.py, docs/plugin-authoring.md | 3d87728 | pass; 39 passed (self). Red: four-byte test 1 failed, 13 deselected (but see Discovered: the same return also records a "tests after implementation" gap) |
| http-auth-on-non-loopback | done | 2 | docs/transports.md (code in 6ec801e) | 8a5f4f4 | pass; 14 passed (self). No red: round-2 diff docs-only |
| error-redaction-and-cleanup | done | 3 | errors.py, plugin.py, pipeline.py, test_pipeline.py | 18adc9d | pass; 43 passed (self). Red: 2 failed, 11 passed |

Continuations: five workflow continuations were logged (`continue2.log`-`continue6.log`); per-task continuation counts are unknown (not recorded in the returns).

Approvals (`approvals.json`, final status from the latest return per id, then rulings):

| Id | Text (short) | Decisions | Tasks | Status |
|---|---|---|---|---|
| A | Core proxy plus plugin ABC hooks | D2 D3 D6 D7 D8 D9 | core-types, http-binding, response-shaping, schemas-and-validation, plugin-abc, registry, call-pipeline, nothing-ever-calls-aclose-on, openapi-credential-hosts, bounded-upstream-bodies, error-redaction-and-cleanup | delivered |
| B | stdio default, streamable HTTP | D10 | cli-stdio, http-transport, fastmcp-adapter, http-auth-on-non-loopback | delivered |
| C | Well documented | D14 D19 | docs-readme-concepts, docs-authoring, docs-reference | delivered (gate-repeat escalations accepted by ruling) |
| D | Small and big runnable examples | D12 D13 | openapi-plugin, testing-harness, examples-small-medium, examples-big-group | delivered |
| E | Plugins easy to implement | D2 D4 D5 D13 | plugin-abc, plugin-discovery, config-model, testing-harness | delivered |
| F | Python/uv/ruff/pytest/mise/CI component | D17 | scaffold, uv-picks-cpython-3-15-for-th, workflow-hardening | delivered |
| G | FastMCP 4.x behind own ABC, tokens not forwarded | D1 D7 D8 D11 | fastmcp-adapter, call-pipeline, schemas-and-validation, registry, http-transport, http-binding | delivered |
| H | Tools only, pinned tag v0.1.0 | D15 D16 D19 | fastmcp-adapter, release | delivered (tag pushed, release run success; agent-orchestrator image consumption not confirmed here) |
| I | pip-installable like claude-code-wrapper | D18 D20 | scaffold, cli-stdio, release, docs-readme-concepts, config-model | delivered (gate-repeat on docs-readme-concepts accepted by ruling) |
| J | Input-required (2026-07-28) hook, adapter, docs, tests | D19 | input-required-core, input-required-adapter, docs-authoring | delivered (gate-repeat on docs-authoring accepted by ruling) |

The approvals the returns reported as `escalated` (return1-3) were mid-run states; the last return that carried each id (return2, 4, 5) or a ruling cleared them. Ids B/D/E/F/G were last `delivered` in return2, A/B/F in return5, H/I in return4. C and J were last reported `escalated` (return3/return2); they are `delivered` only through the rulings below.

## Deviations and rulings

- cli-stdio, accept: fix agent died (safety classifier rate-limited) on findings the reviewer itself judged false positives (NotImplementedError at cli.py:107 is the exception suppressed around `add_signal_handler`; cli.py:96/97/154 are explanatory comments). Verified on cf2da99: 11 passed, lint clean. Cost if wrong: a real stub or deferred work stays in the CLI; the later whole-diff review and 202-test suite did not surface one.
- docs-authoring and docs-reference, accept: gate-repeat on parking-wording false positives. plugin-authoring.md:460/462 state the input-required kind and the 2026-07-28-only caveat the task requires; transports.md:46 and :107 state protocol-era behaviour and that TLS terminates at a proxy. Verified on 78faf4e (3 passed) and c967152 (4 passed). Cost if wrong: a doc sentence that really defers work ships in v0.1.0.
- docs-readme-concepts, accept: README.md:11-19 "once published to an index; until then use the git forms" is mandated verbatim by AC8 and pinned by `test_readme_install_forms`. Verified on b51a318 (5 passed). Cost if wrong: README advertises index installs that do not work until publication; the text says so.
- openapi-plugin: re-run after a rate-limited implementer (impl-agent-died in return1); the re-run landed 5d7213c.
- testing-harness: first run stopped on `no-progress` with a medium finding (the "ambiguous local name" branch has no test; test is named `..._unknown_and_ambiguous` but only covers unknown). The re-run landed 7e77db3 and its `declined` entry calls this a naming nit. Cost if wrong: an untested branch in `PluginHarness._exposed`.
- Discovered tasks built: python 3.12 pin (`uv-picks-cpython-3-15-for-th`) and http client aclose (`nothing-ever-calls-aclose-on`). The probe-notes doc was folded into docs-reference rather than made a task.
- Post-review security tasks (workflow-hardening, openapi-credential-hosts, bounded-upstream-bodies, http-auth-on-non-loopback, error-redaction-and-cleanup) were added after the whole-diff review and security pass.
- `forwardMerged`: empty in every return; no forward merges.

Declined verifier/reviewer findings (all judged speculative hardening or false positives by the reviewer, not settled by a ruling) are in the returns' `declined` arrays; the ones that could matter are carried to the next section.

## Duplicates reconciled

The returns' `duplicates` arrays are empty. The git log shows two pairs of commits with identical subjects: `cfe0936` and `61a1b3c` ("fix(http): reject empty bearer_token, treat only None as unset") and `e089fc9` and `edff6df` ("docs: configuration and transport references with tests"). I did not diff them; they are most likely a rebase or a repeated landing of the same change and the final tree holds one implementation each. Treated as unknown, not reconciled.

## Discovered and blocked

Blocked: none. Undelivered: none (`undelivered` empty in every return).

Not exercised or not verified (taken from `cannotVerify` and `declined`; each is cleared by the repo owner, Szymon, adding the named test or running it live):
- Release workflow runtime: the run on tag v0.1.0 completed `success` (1m16s); the git+https install from the real tag was not separately re-run by me. Cleared by: owner running `pip install git+https://github.com/szymonrychu/any-mcp@v0.1.0`.
- agent-orchestrator image actually consuming v0.1.0: not checked. Cleared by: the agent-orchestrator epic.
- Live behaviour: SIGTERM before the registry finishes starting; real SIGTERM in stdio with a blocked stdin thread; non-POSIX signal handling; uvicorn graceful shutdown on `--transport http`; non-loopback bind behind a reverse proxy; exit 78 from a real process (tests assert `cli.main` returns 78 only).
- Real entry-point discovery from an installed package (tests monkeypatch `entry_points`); `pip install ./examples/petstore` discovery and hatchling wheel bundling of `petstore.yaml`.
- Live upstreams (api.zippopotam.us, api.github.com), real hostile or very large upstream memory behaviour, real third-party clients receiving `tools/list_changed`.
- Stateless multi-worker HTTP with 2026-07-28 `requestState` (per-process sealing key), and a forged `requestState` rejected by the SDK.
- Docs accuracy: hook-default and error-kind claims in docs/concepts.md against the source; Claude Code `.mcp.json` approval behaviour; Markdown rendering of the yaml fence in plugin-authoring.md; Origin 403, bearer 401, exit codes 78/2 as documented.
- Known unhardened edges the reviewer left alone: `load_plugins` partial failure leaves earlier plugins' clients unclosed; max_length below the 7-char hash suffix can exceed max_length; malformed server URL raises `ValueError` instead of `ConfigError` (still fails closed); redaction does not cover JSON-escaped or URL-encoded secrets or URL userinfo.
- Test-first not shown: call-pipeline round-2 fixes, plugin-abc bytes fix, cli-stdio, examples-small-medium, examples-big-group, nothing-ever-calls-aclose-on (mutation check claimed, not re-run). bounded-upstream-bodies is internally inconsistent: the return records both a red run (`wroteTestFirst: true`) and a process gap saying tests were written after implementation. The files win only partly: I cannot see the red run, so it is quoted as the implementer's claim.
- Python 3.12 behaviour: fastmcp-adapter and http-transport were verified on the CPython 3.15 venv (http-transport also under `UV_PYTHON=3.12`); the 3.12 pin was added afterwards.

## Research that changed the plan

- fastmcp 4.1.3 resolves to httpx2 v2.16.0 (scaffold, confirmed with `uv tree` and `uv.lock`; recorded only in the scaffold commit body): shaped the HTTP-client assumption for the adapter and http-binding.
- uv picked CPython 3.15 despite the mise 3.12 pin (fastmcp-adapter finding): added the `.python-version` pin task and a test.
- Registry finding that nothing calls `aclose()` on per-plugin httpx clients (registry task): added the `nothing-ever-calls-aclose-on` task (LoadedPlugins.aclose, CLI and harness callers).
- fastmcp takes whole-second cache TTLs and rejects 0, so the adapter sets the SDK `CacheHint` in ms directly (fastmcp-adapter, pinned by `test_list_result_cacheable`).
- Security review of the whole diff produced the five hardening tasks listed under Deviations.

## Cost

- Agents by role: per-role counts are not in the returns. Recorded: 33 triage calls in total (return1 15, return2 10, return3 2, return5 6, return4 0), 5 workflow continuations, whole-diff review (sonnet), one security pass, one scope audit. Wall-clock: unknown.
- Estimates come from the task files; `actual` and `actual_roles` are empty in all 30 task files, so no actual minutes are recorded. README `Time`: Estimate 150 agent-min, Critical path 80 min, expected wall 3.3 h (P=1.5, k=2.0), Actual 0 min, Remaining 0 min. Sum of per-task estimates: 150 over the 28 tasks that have one.

| Task | estimate (min) | actual (min) |
|---|---|---|
| scaffold, plugin-abc, openapi-plugin, cli-stdio, examples-small-medium, examples-big-group, input-required-core, bounded-upstream-bodies, error-redaction-and-cleanup, http-auth-on-non-loopback | 6 each | unknown |
| release, core-types, response-shaping, config-model, http-binding, schemas-and-validation, plugin-discovery, registry, call-pipeline, fastmcp-adapter, http-transport, input-required-adapter, testing-harness, docs-authoring, docs-reference, docs-readme-concepts, workflow-hardening, openapi-credential-hosts | 5 each | unknown |
| nothing-ever-calls-aclose-on, uv-picks-cpython-3-15-for-th | none (discovered) | unknown |

## MRs and deploy

- PR https://github.com/szymonrychu/any-mcp/pull/1: merged as 2b9cc65, CI passed.
- Tag v0.1.0 pushed. `gh run list --workflow release.yml --limit 1`: run 39879113219 "Merge pull request #1 from szymonrychu/any-mcp", push on v0.1.0, completed success, 1m16s, 2026-10-23T00:36:24Z.
- Full suite on the tip: 202 passed in 46.56s; lint: all checks passed, 62 files formatted.
- Deploy: no PyPI publishing by design (git tag only). Consumption by the agent-orchestrator agent image is not confirmed in this record.

## Lessons routed to

- Parking-wording gate flags factual doc sentences (6 false-positive escalations: cli-stdio, docs-authoring, docs-reference, docs-readme-concepts, bounded-upstream-bodies, release; `NotImplementedError` as an exception type). Mechanical: add a test for the gate with these sentences as fixtures and scope it to added lines in code files plus a banned-phrase list, not generic words, so verifier verdicts do not depend on a model reading a line it cannot see (the verdicts quoted "output does not show the wording").
- Escalation verdicts labelled `real` whose reason is "verification output does not show the line": add a check in the verifier that a `real` verdict must quote the offending line; otherwise downgrade to `unconfirmed`. Mechanical.
- merge.py prints no `baseBefore` SHA, leaving `land.base` empty or wrong (`""`, `"\"\""`, "not printed by merge.py") in 15+ tasks: make merge.py print it and add a test asserting the field. Mechanical.
- Landed tasks' verifier evidence is only `verify: pass <cmd>` with no pytest summary line: make verify-task echo the summary line and add a test that the evidence contains `passed`. Mechanical.
- Tests written after implementation (call-pipeline, plugin-abc, cli-stdio, examples-*, nothing-ever-calls-aclose-on, bounded-upstream-bodies): add a gate that rejects a code task without a recorded `tests.red` unless a TDD exception is declared (exception names are the ones in tdd.md). Mechanical.
- The fix agent and the implementer for openapi-plugin died on classifier rate limits: retry with a backoff in plan-execute rather than escalating. Judgement call; edit the plan-execute skill's retry rule.
- Approval statuses in a return reflect only that run's tasks, so ids appear `escalated` after later runs delivered them: the record writer must take the latest return per id, and plan-execute should merge the ledger across continuations. Judgement call; edit start-development's record step.
