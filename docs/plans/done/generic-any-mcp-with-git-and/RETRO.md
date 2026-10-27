# Generic any-mcp with git and local plugin sources retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| anymcp source parser | 3 | 3 | 7 | 3 | 977684 | 489670 |
| plugins repo bootstrap | 3 | 3 | 7 | 3 | 977684 | 675620 |
| anymcp source installer | 5 | 5 | 11 | 14 | 1694306 | 1858483 |
| anymcp source plugin loading | 5 | 5 | 11 | 9 | 1694306 | 2262595 |
| any-mcp source parser parity with the web grammar | 1 | 1 | 4 | 5 | 658840 | 482917 |
| anymcp remove orchestrator | 2 | 2 | 5 | 3 | 546295 | 307643 |
| anymcp release 0.5.0 | 2 | 2 | 5 | 4 | 546295 | 452097 |
| web plugin source parser | 2 | 2 | 5 | 36 | 546295 | 1136702 |
| plugins orchestration plugin | 5 | 3 | 11 | 4 | 1694306 | 1618762 |
| orch plugins dev dependency | 2 | 2 | 5 | 3 | 546295 | 569303 |
| orch any-mcp 0.5.0 pin | 2 | 2 | 5 | 3 | 546295 | 603753 |
| orch any-mcp sources spec | 3 | 3 | 7 | 4 | 977684 | 1098120 |
| web preset plugin sources | 3 | 3 | 7 | 4 | 977684 | 754804 |
| orch render plugin sources | 5 | 5 | 11 | 5 | 1694306 | 2176262 |
| Web form refuses credentials in plugin source URLs | 1 | 1 | 4 | 1 | 656478 | 255191 |
| Orchestrator refuses credentials in plugin source URLs | 1 | 1 | 4 | 2 | 656478 | 469386 |
| helmfile deploy pin | 2 | 2 | 5 | 39 | 546295 | 692184 |
| helmfile smoke plugin tools | 3 | 3 | 7 | 184 | 977684 | 2007788 |
| Total | 50 | 48 | 121 | 326 | 16915210 | 17911280 |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| anymcp source parser | 0 | 0.43 | 0.50 |
| plugins repo bootstrap | 0 | 0.43 | 0.69 |
| anymcp source installer | 0 | 1.27 | 1.10 |
| anymcp source plugin loading | 0 | 0.82 | 1.34 |
| any-mcp source parser parity with the web grammar | 0 | 1.25 | 0.73 |
| anymcp remove orchestrator | 0 | 0.60 | 0.56 |
| anymcp release 0.5.0 | 0 | 0.80 | 0.83 |
| web plugin source parser | 0 | 7.20 | 2.08 |
| plugins orchestration plugin | -2 | 0.36 | 0.96 |
| orch plugins dev dependency | 0 | 0.60 | 1.04 |
| orch any-mcp 0.5.0 pin | 0 | 0.60 | 1.11 |
| orch any-mcp sources spec | 0 | 0.57 | 1.12 |
| web preset plugin sources | 0 | 0.57 | 0.77 |
| orch render plugin sources | 0 | 0.45 | 1.28 |
| Web form refuses credentials in plugin source URLs | 0 | 0.25 | 0.39 |
| Orchestrator refuses credentials in plugin source URLs | 0 | 0.50 | 0.72 |
| helmfile deploy pin | 0 | 7.80 | 1.27 |
| helmfile smoke plugin tools | 0 | 26.29 | 2.05 |

- MdAPE points: 0.0%
- MdAPE minutes: 80.6%
- MdAPE tokens: 27.3%
<!-- retro:generated:end -->

## Retro

| Went well | Went bad / could be improved |
|---|---|
| 18 tasks delivered; points held (MdAPE 0.0%, 50 est vs 48 post-delivery; plugins orchestration plugin re-scored 5 to 3). | helmfile smoke plugin tools: step 10b was written against an assumed text output of `any-mcp --list-tools`, which prints a JSON array. Its unit-test fakes mirrored the wrong assumption (120 passed), so it failed only live (run 1). Fix round 1, 3fd172f, PR #33. |
| Phase 5 whole-diff review, security review and scope audit turned each finding into a task (parser parity, credentials refused in source URLs in web and orchestrator), all closed fast (1 to 5 min). | helmfile smoke plugin tools took 184 min vs 7 (26.29x) and 2007788 tokens vs 977684 (2.05x), mostly three live smoke runs. |
| Deploy pins landed and rollouts were OK (helmfile be673ca; helmfile tests 222 passed); smoke run 3 passed, listing orchestrator_sessions_list and petstore_ tools. | any-mcp source parser parity with the web grammar: the spec over-banned whitespace and had to be amended so local paths may contain spaces (5 min vs 4). |
| Most small tasks finished under the minutes seed (anymcp source parser 3 vs 7, plugins repo bootstrap 3 vs 7, orch render plugin sources 5 vs 11). | GitGuardian flagged a fake basic-auth string in an orchestrator test. Force-push was denied, so a v2 branch was pushed, PR #24 opened and #23 closed. |
| | An unrelated Harbor image loss (agents-matrix-connector 98b0803, restarted at 03:30Z outside this session) broke smoke run 2 at the matrix step; fixed by re-running the connector CI images job (run 40282930555, attempt 2). |
| | web plugin source parser took 36 min vs 5 (7.20x, 2.08x tokens); helmfile deploy pin 39 vs 5 (7.80x). Minutes MdAPE 80.6%, tokens 27.3%. |
| | The scope auditor left code/any-mcp detached; restored to main by hand. |

## Improvements

- Code:
  - agents-helmfile smoke script (plugin tools step 10b): parse `any-mcp --list-tools` as JSON; keep a unit test whose fake emits the real JSON array, not text.
  - agents-orchestrator credentials test: the fake basic-auth literal tripped GitGuardian; build the string at runtime or use an allowlisted placeholder.
  - any-mcp and agents-web source parsers: keep one shared parity test table so the two grammars cannot drift again.
- Delivered differently:
  - Parser parity spec banned whitespace in local paths; amended to allow spaces, because local paths legitimately contain them.
  - Added beyond the plan, from review: parity task and the two credential-refusal tasks (web and orchestrator).
  - Smoke step 10b was reworked after run 1 (text grep replaced by JSON parsing), because the real output is JSON.
- Tech debt:
  - PR #23 closed and PR #24 opened from a v2 branch to clear a secret-scan false positive; no code debt, but history on #23 is orphaned.
  - Smoke depends on the live Harbor registry holding every deployed image tag: a missing tag fails unrelated steps; a pre-smoke image-existence check would remove it.
- Workflow:
  - recurring (cross-session-messaging-and, matrix-read-receipts, agents-matrix-connector-depl): live apply/smoke tasks run far over the minutes seed (184 vs 7 here, 39 vs 5 for the deploy pin; 35 vs 12 and 17 vs 6 before; 90 vs 4; 26 vs 5). Change: seed live apply/smoke tasks at 15-25 min (more when several runs are likely) in planning, calibrated from earlier actuals.
  - recurring (cross-session-messaging-and, paste-env-contents-into-the): a defect found only late (live run here) that per-task verify missed, because test fakes encoded the same wrong assumption. Change: any task that shells out to an external tool must have its AC cite a captured real output sample, and the reviewer checks fakes against it.
  - Secret-scan false positives (GitGuardian) with force-push denied: add a pre-push secret scan note to the implementer brief (one-off, Retro table only).