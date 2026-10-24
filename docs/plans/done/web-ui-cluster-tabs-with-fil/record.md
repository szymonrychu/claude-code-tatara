# web ui cluster tabs with filesystem chat and terminal panels record

## Summary

Asked (2026-10-23): replace the left cluster ribbon with top tabs; each cluster tab is a three-panel workspace (filesystem tree, chat, multi-tab terminal) with resizable separators and minimize/maximize; chat unchanged; headless parity for every capability.

Shipped: top tab bar plus hamburger menu (sessions list, empty settings section), the three-panel workspace with persisted layout and phone switch, agents strip in the chat header, lazy filesystem tree with preview and event-driven refresh, xterm terminal tabs over a WebSocket PTY, wrapper file and terminal APIs, orchestrator /api/v1 proxies and WebSocket relay behind a mandatory Origin allowlist, API-only e2e tests (wrapper service and kind), wrapper and orchestrator pins, helmfile pin. 25 tasks built (21 planned at approval, 4 added during the run), all `status: done`. Merged: claude-code-wrapper#2 (1ced775), agent-orchestrator#4 (f1baa5b), agents-helmfile#6 (78299cc).

Verdict: pass (epic review 2026-10-24). Not live-verified: helmfile apply, LAN smoke and the hairpin-NAT check are user-run steps, so the deploy is pinned and merged but unconfirmed running. Real-browser behaviour (pointer drag, xterm fit, tab overflow) was only exercised under jsdom mocks.

## Planned vs built

Source of each cell: task frontmatter (`status`, `verified_head`, `actual_roles`), git history of the three component repos, and the first plan-execute return (`/tmp/claude-0/-home-user-claude-code-tatara/8fe589da-3f22-5560-aa23-25819f182e28/scratchpad/webui-return.json`). The return covers run 1 only; tasks that finished in later runs (marked "later") have no return value, so rounds are unknown and the verifier head is the frontmatter `verified_head`. "Verifier head" is the SHA the independent verifier ran on (`tasks[].verification.head`); the tail below it is the landing verify result, and any count quoted from the implementer is labelled `impl`.

Run 1 landed 18 of 21 planned tasks; wrapper-sha-pin stopped `blocked`, kind-e2e-workspace and deploy-pin `dependency-failed`. Those three, plus the 4 added tasks, finished in continuation runs (6 `apply-run` commits in total, 00:28Z to 01:56Z).

| Task | Repo | Status | Review rounds | Continuations | Files (git) | Verifier head | Verification tail |
|---|---|---|---|---|---|---|---|
| pty-resize-and-raw-ring | wrapper | done | 1 | 0 | pty_proc.py, ring.py, 2 tests | 2f6788d | land verify pass (test_pty_proc, test_ring, ruff); impl: ruff clean, 277 files formatted |
| wrapper-file-api | wrapper | done | 1 | 0 | files.py, api/files.py, app.py, config.py, config.example.yaml, README, 2 tests | f63dee9 | land verify pass (test_api_files, test_readme_api, test_readme_config, test_config, ruff) |
| terminal-registry | wrapper | done | 3 | 0 | terminals.py, config.py, manager.py, README, test_terminals.py | 5f8f1e2 | land verify pass; impl: 83 passed, 1 deselected (test_shutdown_stops_all, container-only), ruff clean |
| terminal-websocket-api | wrapper | done | 1 | 0 | api/terminals.py, api/auth.py, app.py, README, 3 tests | 09b9276 | land verify pass; impl: 44 passed across test_api_terminals/test_api_auth/test_readme_api, ruff clean |
| wrapper-workspace-e2e | wrapper | done (ruling: accepted) | 2, stopped `gate-repeat` | 0 | tests/test_e2e_workspace.py | bd2c023 | land verify pass (test_e2e_workspace, ruff); no pytest summary line in the land output; processOnly, see red table |
| wrapper-security-followups | wrapper | done (ruling: accepted) | unknown (later) | later run | terminals.py, api/terminals.py, service.py, config.py, README, test_terminals.py, pyproject.toml, uv.lock | 354e669 | tail not in files; ruling says verified on HEAD 354e669; wrapper full suite 1653 passed, 2 container-only failures |
| origin-allowlist | orch | done | 2 | 0 | settings.py, api/origin.py, app.py, README, chart README, e2e/values-kind.yaml, test_origin.py | 2a8ce4f | land verify pass (test_origin, test_settings, ruff); impl: 32 passed, 100 files formatted |
| wrapper-proxy-seam | orch | done | 1 | 0 | api/workspace.py, app.py, wrapper/client.py, db/agents.py, 3 tests, README, MEMORY.md | 093a155 | land verify pass; impl: 85 passed, ruff clean |
| file-proxy-routes | orch | done | 2 | 0 | workspace.py, schemas.py, fake_wrapper.py, test_api_files.py, contract test, README, openapi.json, schema.d.ts | f2a3dfd | land verify pass (incl. check:api, ruff); impl: 28 passed, 11 deselected |
| terminal-proxy-routes | orch | done | 1 | 0 | workspace.py, schemas.py, fake_wrapper.py, test_api_terminals.py, contract test, README, openapi.json, schema.d.ts | fbd686b | land verify pass (incl. check:api, ruff); impl: 78 passed |
| terminal-ws-relay | orch | done | 2 | 0 | workspace.py, pyproject.toml, uv.lock, test_terminal_relay.py, README | 876c5be | land verify pass; impl: 36 passed, ruff clean, uv lock --check ok. The independent verifier errored (script error, see Contradictions); head is from the landing tree |
| fake-wrapper-workdir-regress | orch | done | unknown (later) | later run | fake_wrapper.py, 5 test files | 1885121 | tail not in files; added after run 1 found `test_session_workdir_matches_rendered_workdir_path` red on the integration branch; orchestrator full suite 472 passed afterwards |
| wrapper-sha-pin | orch | done | 0 in run 1, then later | later run | pyproject.toml, uv.lock, e2e/agent-test.Dockerfile, README Images, tests/test_images.py | 2edeb38 | run 1 tail (48 passed, ruff clean) ran at 504b870, before the pin moved, so it does not cover the pin; final head 2edeb38 tail not in files |
| kind-e2e-workspace | orch | done (ruling: accepted) | unknown (later) | later run | tests/e2e/test_e2e_kind.py (+165 lines) | 5675058 | local real-wrapper stack: 3 passed, 8 deselected in 1.70s (green.txt); kind run is the PR CI e2e job, green |
| be-review-fixes | orch | done | n/a | later run | cli.py (ws_max_size=65536), test_cli.py, db/agents.py | 96a6aa1 | tail not in files; covered by orchestrator suite 472 passed |
| fe-deps-and-storage | orch | done | 1 | 0 | package.json, lockfile, vite.config.ts (ws: true), api/client.ts, layout/storage.ts + test | fa1456d | land verify pass (storage + designRules tests, lint, build); impl: 15 passed |
| fe-top-bar | orch | done | 2 | 0 | TopBar.tsx, SessionsMenu.tsx, TopBar.test.tsx | 997f078 | land verify pass; impl: 19 passed, lint clean, build ok |
| fe-retire-ribbon | orch | done | 2 | 0 | App.tsx, App.test.tsx, ClusterForm.test.tsx; Shell, Ribbon, ClusterRow, Ribbon.test deleted | c58e220 | land verify pass; impl: 32 passed; on disk: no Shell.tsx, Ribbon.tsx, ClusterRow.tsx, AgentRow.tsx, AgentFilter.tsx |
| fe-agents-strip | orch | done | 2 | 0 | AgentsStrip.tsx + test, ChatView.tsx, AgentFilter/AgentRow removed | d5bce5e | land verify pass; impl: 45 passed (5 files); implementer did not rerun lint/build, the landing verify did |
| fe-panel-workspace | orch | done | 2 | 0 | Workspace.tsx, panelLayout.ts, Workspace.test.tsx, App.tsx | e666c3a | land verify pass; impl: 40 passed (3 files) |
| fe-filesystem-panel | orch | done | 1 | 0 | api/files.ts, files/useFileTree.ts, fileEvents.ts, FilesPanel.tsx + test, App.tsx | 4ce96df | land verify pass; impl: 36 passed (3 files) |
| fe-terminal-socket | orch | done | 1 | 0 | api/terminals.ts, terminal/terminalSocket.ts + test, api/client.ts | 236c334 | land verify pass; impl: 27 passed (2 files); a reviewer ran only the socket test and tsc, the landing verify ran lint and build |
| fe-terminal-panel | orch | done | 2 | 0 | XtermView.tsx, TerminalPanel.tsx + test, theme.ts, App.tsx | 25e24cc | land verify pass; impl: 63 passed (5 files) |
| fe-review-fixes | orch | done | n/a | later run | terminalSocket.ts, TerminalPanel.tsx, TopBar.tsx and their tests | 6227ccc | tail not in files; frontend suite 164 passed, build and check:api clean |
| deploy-pin | helmfile | done (ruling: accepted) | unknown (later) | later run (was `dependency-failed` in run 1) | helmfile.yaml.gotmpl, values/agent-orchestrator/common.yaml, tests/test_orchestrator_release.py (3 files, +36/-11) | feec968 | release tests pass with 2 chart-pull tests deselected (Harbor and cloudnative-pg blocked by the container network policy); ruff clean |

Note on fake-wrapper-workdir-regress: the head 1885121 is the commit in the orchestrator log; the frontmatter `verified_head` is 18851216ec9bf98b5f86640d64674fa6d3b06ddd.

Branch totals from git: wrapper ca2ddf3..354e669 is 23 files, +3351/-33; orchestrator d5a7738..6227ccc is 68 files, +7822/-515; agents-helmfile 38a2543..feec968 is 3 files, +36/-11.

Return fields for the 3 run-1 unfinished tasks: wrapper-sha-pin `verified: true` with `stopped: blocked` and `complete: false`; kind-e2e-workspace and deploy-pin `verification: null`, listed in `unverified`. After continuation all three have a `verified_head` in the task files.

### Red evidence (implementer `tests.red`)

No `tdd-revert` result is quoted here: it restores every non-test file to base at once, so a new test importing new code fails trivially.

| Task | Implementer red | Note |
|---|---|---|
| pty-resize-and-raw-ring | `AttributeError` in test_resize_reaches_child, test_resize_rejects_bad_sizes_and_states, test_raw_keeps_escapes_and_caps | genuine, per behaviour |
| wrapper-file-api | collection ImportError (`claude_code_wrapper.files` absent) | module-level only |
| terminal-websocket-api | ImportError on collection; test_api_auth websocket bearer cases and test_readme_api cases failed; later test_relay_cancellation_stays_with_the_canceller[2,3] failed with `CancelledError` | test_api_terminals tests were not seen failing one by one |
| wrapper-proxy-seam | ImportError for `workspace`; `WrapperClient.request_json` missing | module-level |
| origin-allowlist | mutation: `add_middleware(OriginAllowlist)` commented out, test_create_app_wires_origin_and_source_allowlists failed | wiring pre-existed; verifier did not rerun |
| terminal-proxy-routes | `test_create_on_agent: assert 404 == 201`; 6 contract terminal cases failed before the fake existed | genuine |
| fe-deps-and-storage | `./storage` fails to resolve | module-level |
| fe-filesystem-panel | FilesPanel.tsx hidden, import fails | process gap: not per behaviour, run after the implementation existed |
| fe-panel-workspace | mutation (onLayoutChanged early return): 3 new tests failed, 13 passed | tests added to existing behaviour |
| fe-terminal-socket | `../api/terminals` fails to resolve | module-level |
| fe-terminal-panel | `fit_skipped_while_host_hidden: expected 2 to be 1` | genuine |
| wrapper-workspace-e2e | none admissible. The recorded run reverted every dependency-provided src file to ca2ddf3 (`ModuleNotFoundError: claude_code_wrapper.terminals`), which is the tdd-revert shape. The only teeth check is the implementer's scrub-disabled mutation failing test_terminal_over_real_service; the verifier did not rerun it | ruling accepted, processOnly |
| kind-e2e-workspace | none for the feature. red.txt shows 3 failures on a local stack: `read_until` pattern `^still-42\r?$` did not match PTY output with `\r\n` after the echo; this is a test defect fixed by 5675058, not a failing-before-implementation run. green.txt: 3 passed | test-only task over landed surfaces |
| terminal-registry, wrapper-security-followups, origin-allowlist (wiring), file-proxy-routes, fake-wrapper-workdir-regress, fe-retire-ribbon, fe-agents-strip, fe-top-bar, deploy-pin, wrapper-sha-pin, be/fe-review-fixes | not recorded in the run return, or exception stated | terminal-registry round 3 changed no code; fe-top-bar was a comment edit; fe-retire-ribbon/fe-agents-strip rewrites of passing tests; wrapper-sha-pin dependency bump (its implementer claimed a red Dockerfile test that was green at 504b870); fake-wrapper-workdir-regress process gap: new root assertion not run red before the fix |

### Approvals

Run-1 return statuses are shown first; the later status for K, J and H is derived from the task files (all their tasks `done`) and the merged PRs, not from a return value.

| Id | Text | Decisions | Tasks | Run-1 status | Status now |
|---|---|---|---|---|---|
| A | Left ribbon replaced by a top tab bar (state mark, slug, gauge; New cluster and Discard; no Edit) | D10 D12 D13 | fe-retire-ribbon, fe-top-bar | delivered | delivered |
| B | Hamburger menu: sessions from the top, settings pinned to the bottom (empty until presets epic) | D14 | fe-top-bar, fe-retire-ribbon | delivered | delivered |
| C | Three panels with draggable separators, minimize/maximize rules, persisted layout, phone layout | D7 D15 D16 | fe-deps-and-storage, fe-panel-workspace | delivered | delivered |
| D | Per-agent rows move into an agents strip in the chat header | D17 | fe-agents-strip | delivered | delivered |
| E | Terminal panel with several tabs, shell per agent pod over WebSocket PTY, xterm.js | D2 D3 D6 D11 D18 D19 D20 D21 | fe-terminal-panel, fe-terminal-socket, pty-resize-and-raw-ring, terminal-proxy-routes, terminal-registry, terminal-websocket-api, terminal-ws-relay, wrapper-workspace-e2e | delivered | delivered |
| F | Filesystem panel: lazy tree, event-driven refresh, read-only preview | D1 D8 D23 D24 D25 | fe-filesystem-panel, file-proxy-routes, wrapper-file-api | delivered | delivered |
| G | `@mui/icons-material` 9.5.0 added | D26 | fe-deps-and-storage, fe-top-bar, fe-panel-workspace, fe-filesystem-panel | delivered | delivered |
| H | Headless parity: documented public API and an API-only e2e test per capability | D28 | wrapper-file-api, terminal-websocket-api, wrapper-workspace-e2e, file-proxy-routes, terminal-proxy-routes, terminal-ws-relay, kind-e2e-workspace | escalated (kind-e2e-workspace dependency-failed) | delivered; kind leg ran in orchestrator PR CI (green), not in this container |
| I | Wrapper file and terminal API plus orchestrator proxies with confinement and caps | D4 D27 | file-proxy-routes, terminal-proxy-routes, terminal-ws-relay, wrapper-proxy-seam | delivered | delivered |
| K | Mandatory Origin allowlist (ORCH_ALLOWED_ORIGINS) on every WebSocket upgrade | D5 D22 | deploy-pin, origin-allowlist, terminal-proxy-routes, terminal-ws-relay | escalated (deploy-pin dependency-failed) | delivered; helmfile sets `ORCH_ALLOWED_ORIGINS: https://agents.szymonrichert.pl` |
| J | Wrapper image, orchestrator image and chart pinned in agents-helmfile; apply and smoke by the user | D9 | wrapper-sha-pin, kind-e2e-workspace, deploy-pin | blocked (wrapper PR merge sha, orchestrator can clear) | delivered for the pins; apply and smoke unverified, user-run |

## Deviations and rulings

Costs below are the record author's reading of what a wrong call would cost; the design file states the rulings but not their costs.

1. Interrogate verdict (2026-10-23, panel fable/opus/sonnet), 13 items acted on, no "consider" items.
   - Shell env contract: the env `manager._child_env(ctx)` builds for Claude minus every secret-kind `ClaudeEnv` name and CCW_AUTH_TOKEN, CCW_PEER_TOKEN, CCW_HOOK_TOKEN (was `service_env` minus four names). Why: requirement, D11 and ruling 4 contradicted each other. Cost if wrong: a secret reaches the shell env; mitigated only by the same-uid /proc trust model.
   - Scrub tests must seed every scrubbed name before asserting absence (item 2). Cost if wrong: vacuous test, silent leak.
   - Close-code mapping: 1005 maps to 1000; 1006, 1015 and no code map to 1011; 1005/1006/1015 never re-sent (item 3). Cost if wrong: relay crash on invalid close frames.
   - terminal_id format pinned (`^term_[0-9a-f]{12}$` form, one definition), 422 `invalid_request` otherwise (item 4). Cost if wrong: the derived bearer is sent to other upstream paths.
   - README error codes `session_not_active`, `invalid_size`; cap reserved synchronously and unregister before awaiting close (items 5, 6); WrapperTarget.token `repr=False` with a DEBUG caplog test (7); lazy shared httpx client (8); file read via O_NOFOLLOW|O_NONBLOCK plus fstat (9); 64 KiB input frames (10); kill the whole shell session, not the process group (11); redaction stance documented (12); bookkeeping (13).
2. Builder check rulings (design.md `Builder check rulings`), 11 entries. Notable: `terminals_max` counts every registered terminal, alive or exited (2); reconnect only on 1006, 1011, 1013, 4409 with 1 s to 30 s backoff, at most 10 attempts (6); only the active cluster's Workspace is mounted (9); only configured origins work, dev example http://localhost:5173 (10); missing workdir root renders as an empty tree (11). Cost if wrong: ruling 2 means exited shells hold cap slots until the next reaper tick (users hit `terminal_limit` sooner); ruling 10 means a dev server on another origin gets 1008.
3. terminal-registry review finding rejected: the finding said the cap should count live terminals only (task text), ruling 2 and AC13 say all registered ones. Code, README row and `test_cap_counts_exited_and_reaps_exited` follow the ruling. Cost: 3 review rounds and 46 agent-min, the largest task, spent partly on a finding the ruling already answered.
4. `rulings.json` accepts (4):
   - wrapper-workspace-e2e 2026-10-24T00:23:52Z: process-only `tdd-skipped` on an e2e test over surfaces already landed. Cost if wrong: the test may not catch regressions; only the scrub-disabled mutation backs it.
   - wrapper-security-followups 00:39:51Z: parking gate false positive, README states the limits (AC5). Cost if wrong: an isolation limit undocumented.
   - kind-e2e-workspace 01:20:45Z: test-only task, kind run happens in PR CI. Cost if wrong: red PR CI (it was green).
   - deploy-pin 01:56:08Z: the two AC4 failures are chart-pull tests blocked by the container network policy; diff is exactly the pin. Cost if wrong: `mise run apply` (which depends on `test`) fails for the user.
5. Run 1 rulings on discovered items: uvicorn ERROR log after WebSocket denials dropped (third-party); anyio folded into wrapper-security-followups (now declared in pyproject.toml line 26); verifier flag misuse dropped (workflow tooling). Cost if wrong: noisy denial logs, covered under Discovered.
6. Tasks added during the run (4, beyond the 21 approved): wrapper-security-followups (security review: pid-reuse guard, secret-name env scrub, ws frame cap, attach cap, trust-model docs; commits 94cad3b, 354e669), fake-wrapper-workdir-regress (suite regression on the integration branch), fe-review-fixes and be-review-fixes (epic review findings). Cost: 10 + 9 + 6 + 1 = 26 agent-min.
7. Requirement amendments after approval: terminal-proxy-routes (README error codes for `session_not_active`, `invalid_size`, `invalid_request`), wrapper-sha-pin (wrapper PR merge sha 1ced7750483ee3eecdda5b6b26adc87405680ab1), deploy-pin (shas f1baa5b and 1ced775, verify command narrowed with `-k 'not release_chart_version_and_needs and not db_secret_matches_rendered_cnpg_cluster'`). Cost if wrong: the narrowed command hides the two chart tests; they run in `mise run apply`.
8. Epic review rulings: acted on origin refusal shown within two attempts, terminal list refresh on agent readiness with unavailable_agents notice, hook-failed mark and ready/replicas count in tabs, ws_max_size 65536, stale ribbon comment. Noted, not done: Host allowlist (DNS rebinding), Origin guard on pre-existing bodyless POSTs in messages.py.
9. `forwardMerged`: none (empty in the run return).

## Duplicates reconciled

None. The run return `duplicates` is empty and `misattributed` is empty for every task. The overlap between `terminal-proxy-routes` and `file-proxy-routes` on `workspace.py`, `schemas.py` and the fake wrapper was sequenced by `depends_on`, not built twice.

## Discovered and blocked

Cleared during the run:
- wrapper-sha-pin blocked on the wrapper merge sha; cleared by merging claude-code-wrapper#2 and amending the task (orchestrator). Cascaded to kind-e2e-workspace and deploy-pin `dependency-failed`; both finished after resume.
- Full orchestrator suite red on the integration branch (workdir reporting); cleared by fake-wrapper-workdir-regress.

Open, with who can clear:
- helmfile apply, LAN smoke, and the hairpin-NAT check (curl the UI host from an agent pod, expect 403): user.
- DNS-rebinding Host allowlist on port-forward access: not done; prod ingress host routing blocks it. Follow-up epic if wanted.
- Origin guard on pre-existing bodyless POST routes (messages.py): not done; outside this epic. Follow-up epic.
- uvicorn logs `ASGI callable returned without completing handshake` as ERROR after each WebSocket denial: third-party; log alerts may misread it. Upstream uvicorn or a log filter in a later task.
- Verifier tool glitch (unsupported `--timeout` flag, stderr discarded, produced false high findings on terminal-ws-relay and a script error): plan-execute maintainers.
- Wrapper container-only failures: `tests/test_manager.py::test_shutdown_stops_all` (PID 1 does not reap zombies) and `tests/test_container.py::test_example_config_validates_in_image` (Docker Hub 429); green in CI; nothing to fix in the repo.
- agents-helmfile `test_release_chart_version_and_needs`, `test_db_secret_matches_rendered_cnpg_cluster`: blocked by the container network policy; run by `mise run apply`.
- Real-wrapper contract cases (`-m integration`) for files and terminals were not run here (no image); covered by the CI integration and kind e2e jobs.
- Unverified by any agent (`cannotVerify`, none settled by a ruling): real-browser layout and pointer drag (fe-panel-workspace, fe-agents-strip, fe-top-bar); xterm FitAddon and ResizeObserver on a hidden host, reconnect replay against a live wrapper (fe-terminal-panel); live ingress behaviour for 1009 handling and ping keepalive (fe-terminal-socket); dev proxy `ws: true` at runtime (fe-deps-and-storage); live Write/Edit/Bash events refreshing the tree (fe-filesystem-panel); real uvicorn behaviour for refusals and close codes (terminal-websocket-api, terminal-ws-relay, origin-allowlist); nohup/setsid kill on close in a real container, `/proc`-less hosts, shutdown timing (terminal-registry); real-wrapper 401/403 relay (wrapper-proxy-seam); scrub-disabled mutation (wrapper-workspace-e2e). Clear by: user smoke after apply.
- `declined` items (none settled by a ruling beyond those under Deviations): autoCompactPct optionality, lockfile `yaml` removal, slot remount at the phone breakpoint, order of the 503 vs 409 checks, `timeout` argument on `forward`, empty-cluster list returns 200 not 409, explicit default ports in listed origins never match, symlinked-directory listing returns the resolved path, permission-denied reads answer `invalid_path`, `TERMINAL_ID_RE` re-exported from api/terminals.py, pass-through of 3000-3999 close codes, mypy on workspace.py (pre-existing, no mypy config), exited shells dropped on reload and `unavailable_agents` ignored in listTerminals (later added by fe-review-fixes), pid reuse and secret-looking names (later fixed by wrapper-security-followups). Owner: none required.

## Research that changed the plan

- `discovery/wrapper.md`: `require_auth` fails on WebSocket routes (typed to `Request`). Change: terminal-websocket-api retypes it to `HTTPConnection`; `tests/test_api_auth.py::test_websocket_requires_bearer` was the red test (api/auth.py:21).
- `research.md` section 4: inotify does not see writes from other CephFS clients. Change: D25, event-stream re-fetch of touched directories plus a manual refresh in fe-filesystem-panel.
- `research.md` section 5: separate workspace pod (B) and `pods/exec` (C) rejected. Change: wrapper-served shells proxied by the api (D18), no orchestrator RBAC.
- `research.md` section 2: secrets reachable from a shell. Change: env scrub (D21), widened by interrogate item 1.
- OWASP WebSocket cheat sheet (https://cheatsheetseries.owasp.org/cheatsheets/WebSocket_Security_Cheat_Sheet.html). Change: mandatory Origin allowlist (D5, D22), origin-allowlist task.
- `discovery/orchestrator-backend.md`: `test_api_never_imports_k8s_or_wrapper`. Change: exactly one module, `api/workspace.py`, may import the wrapper client (D27).
- `discovery/reuse.md` do-not-build: ingress WebSocket timeouts already 3600 in the helmfile values. Change: deploy-pin made no timeout change; the chart README gets a note only.
- `discovery/reuse.md`: httpx ASGITransport cannot test WebSocket. Change: terminal-ws-relay serves the api with uvicorn on loopback and connects with the `websockets` client; `websockets` declared in pyproject.toml and uv.lock.
- `discovery/frontend.md`: Vite dev proxy lacks `ws: true`. Change: fe-deps-and-storage sets it (grep check in the task verify).
- `discovery/wrapper.md`: no app lifespan. Change: terminals closed from manager shutdown (terminal-registry).
- Library checks (npm/PyPI 2026-10-23): react-resizable-panels 4 renamed components (`Group`, `Panel`, `Separator`); `@xterm/xterm` 6 has no canvas renderer; MUI X lazy loading is Pro. Change: hand-rolled lazy loading with a 2000-entry cap; mocks for jsdom.

## Cost

Agents by role, summed from `actual_roles` (agent-minutes): impl 110, verify 69, review 32, fix 41, land 23, false-finding 2, triage 1 = 278. The task `actual` fields total 262 (README `Actual: 262 min`); the 16-minute gap is per-task rounding in the files (for example kind-e2e-workspace roles sum to 18, actual 17).

Epic-level reviews not in task roles: interrogate panel (fable, opus, sonnet, one pass), whole-diff review (sonnet), scope audit (sonnet, 186 ACs resolved), security reviews (opus x2, wrapper and orchestrator). plan-execute `audit` was `off`. Run 1 triage: 23 calls, 46 input / 18052 output tokens.

Continuations: 6 `apply-run` commits (run 1 plus 5 resumes). Wall-clock from `move in-progress` (2026-10-23 22:12:23Z) to `move done` (2026-10-24 01:57:50Z): about 3 h 46 min.

Estimate vs actual (agent-minutes; all `estimate_by: formula`):

| Task | Estimate | Actual | Actual roles |
|---|---|---|---|
| pty-resize-and-raw-ring | 6 | 3 | impl 1, verify 1, review 1, land 1 |
| wrapper-file-api | 6 | 4 | impl 3, verify 1, review 1, land 1 |
| terminal-registry | 6 | 46 | impl 18, verify 11, review 5, fix 10, land 1, triage 1 |
| terminal-websocket-api | 6 | 14 | impl 12, verify 1, review 1, land 1 |
| wrapper-workspace-e2e | 5 | 5 | impl 2, verify 2, review 1, fix 1, land 1 |
| wrapper-security-followups | 6 | 10 | impl 4, verify 2, review 1, fix 2, false-finding 1 |
| origin-allowlist | 6 | 5 | impl 2, verify 1, review 1, fix 1, land 1 |
| wrapper-proxy-seam | 6 | 6 | impl 4, verify 1, review 1, land 1 |
| file-proxy-routes | 6 | 18 | impl 7, verify 5, review 2, fix 2, land 1 |
| terminal-proxy-routes | 6 | 13 | impl 8, verify 3, review 1, land 1 |
| terminal-ws-relay | 6 | 20 | impl 13, verify 3, review 2, fix 2, land 1 |
| fake-wrapper-workdir-regress | 6 | 9 | impl 2, verify 3, review 1, fix 2, land 1 |
| wrapper-sha-pin | 6 | 6 | impl 2, verify 2, review 1, fix 1, land 1 |
| kind-e2e-workspace | 5 | 17 | impl 1, verify 1, review 1, fix 14, land 1 |
| be-review-fixes | 5 | 1 | impl 1, verify 1, land 1 |
| fe-deps-and-storage | 6 | 5 | impl 1, verify 2, review 1, land 1 |
| fe-top-bar | 5 | 8 | impl 2, verify 4, review 1, fix 1, land 1 |
| fe-retire-ribbon | 6 | 11 | impl 3, verify 5, review 1, fix 1, land 1 |
| fe-agents-strip | 6 | 9 | impl 2, verify 4, review 1, fix 1, land 1 |
| fe-panel-workspace | 6 | 15 | impl 5, verify 5, review 2, fix 1, land 1 |
| fe-filesystem-panel | 6 | 10 | impl 6, verify 2, review 1, land 1 |
| fe-terminal-socket | 5 | 5 | impl 2, verify 2, review 1, land 1 |
| fe-terminal-panel | 6 | 12 | impl 4, verify 5, review 2, fix 1, land 1 |
| fe-review-fixes | 6 | 6 | impl 4, verify 1, review 1, land 1 |
| deploy-pin | 5 | 4 | impl 1, verify 1, review 1, fix 1, false-finding 1 |
| Total | 144 | 262 | README Time: Estimate 144, Critical path 47 min, Expected wall at P=1.5 3.2 h, Actual 262 min, Remaining 5 min |

Largest overruns: terminal-registry (+40, three review rounds and a rejected finding), kind-e2e-workspace (+12, 14 fix minutes on PTY CRLF matching), terminal-ws-relay (+14), file-proxy-routes (+12). Report only, not a budget.

## MRs and deploy

| Repo | PR | Merge | State |
|---|---|---|---|
| claude-code-wrapper | szymonrychu/claude-code-wrapper#2 | 1ced775 | merged; CI green; local full suite 1653 passed, 2 container-only failures (above) |
| agent-orchestrator | szymonrychu/agent-orchestrator#4 | f1baa5b | merged; PR CI all green including kind e2e; local backend 472 passed, frontend 164 passed, build and check:api clean |
| agents-helmfile | szymonrychu/agents-helmfile#6 | 78299cc | merged (feec968 deploy pin: chart 0.1.0-main.f1baa5b, orchestrator image f1baa5b, wrapper image 1ced775, ORCH_ALLOWED_ORIGINS); release tests pass except 2 chart-pull tests blocked by the container network policy, which `mise run apply` runs |

Superrepo pointers bumped in 7505377 (wrapper 1ced775, orchestrator f1baa5b, helmfile 78299cc) on branch claude/nifty-davinci-0z8a2v.

Deploy: not applied. `mise run apply`, the LAN smoke and the hairpin-NAT check are the user's steps; there is no deploy confirmation.

## Lessons routed to

Mechanical (add a check):
- A PTY-output matcher passed review and failed on CRLF in kind e2e (14 fix minutes in kind-e2e-workspace). Add a unit test for the `read_until` helper in `tests/e2e/test_e2e_kind.py` against CR, CRLF and escape-sequence fixtures, in a module the default (non-e2e) suite collects.
- Per-task verify uses targeted tests with `--no-suites`, so a full-suite regression (fake-wrapper-workdir-regress) surfaced only on the integration branch. Add a plan-execute gate that runs the repo's full suite once on the integration branch before the first dependent pin or e2e task starts.
- `merge.py` does not print `baseBefore`, so run-1 land results carry an empty or inferred base; and `filesChanged` in the return lists only the last round for many tasks (fe-top-bar shows one file). Add a test that merge.py prints `baseBefore` and compute `filesChanged` from `git diff base..head`.
- The `tdd-skipped` gate tells test-only tasks to revert non-test files to merge-base, which is the tdd-revert shape that fails trivially when the code came from dependencies (wrapper-workspace-e2e, kind-e2e-workspace). Change the gate message and add a lint rule so that, for test-only diffs, the accepted evidence is a mutation of the dependency code, not a base revert.
- The independent verifier ran a script with an unsupported flag and discarded stderr, producing false high findings (terminal-ws-relay, fe-top-bar). Add a test on the verifier invocation that asserts exact argv and that nonzero exit with stderr fails the verification entry loudly instead of becoming a finding.
- A requirement still said "live terminals" after ruling 2 changed the semantics (terminal-registry, 46 agent-min). Add a `ticket.py` lint that fails when a design ruling mentions a task id or AC and that task's requirement text was not amended after the ruling (compare ruling and task timestamps).

Judgement (edit a skill or rule):
- `start-development`: a task that needs a post-merge sha (wrapper-sha-pin, deploy-pin) should be planned as an explicit post-merge step with the PR merge as its dependency, not as a task that blocks and cascades `dependency-failed` to two others in run 1.
- `plan-execute` implementer role: reports must state a red run only when the test failed at the recorded head (the wrapper-sha-pin report claimed a red Dockerfile test that was green) and must say "mutation" or "module absent" when that is what the red was.
- `start-development` record step: record the final status of approvals after continuation runs in the run return, so the approvals table does not have to be rebuilt from task files for K, J and H.

## Contradictions between summaries and files

- wrapper-sha-pin: run-1 return shows `verified: true` and a passing tail at 504b870 while `stopped: blocked`; that head predates the pin. The frontmatter `verified_head` is 2edeb38.
- terminal-ws-relay: the `processGaps` entry says the independent verification failed and head was never collected, but the return carries `verification.head` 876c5be and the file `verified_head` 876c5be; the head is the landing tree, not an independent verifier run.
- kind-e2e-workspace: the ruling reads "red/green shown on a local real-wrapper stack"; red.txt is a test defect (CRLF regex), not a red before implementation.
- wrapper-workspace-e2e: `tests.red` is a base revert of dependency src, not admissible as TDD red.
- README Review block (written before the helmfile merge) says "agents-helmfile#6 pin open"; it merged as 78299cc.
- `filesChanged` in the return is last-round only for tasks with fix rounds (fe-top-bar, fe-panel-workspace, fe-retire-ribbon, fe-agents-strip, file-proxy-routes, origin-allowlist, terminal-registry, terminal-ws-relay); the Files column above comes from the task file lists and git.
