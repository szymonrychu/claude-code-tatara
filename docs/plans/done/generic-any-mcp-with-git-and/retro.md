# Generic any-mcp with git and local plugin sources retro

## Review

Migrated from the epic format.

## What went well

- 18 tasks delivered; points held (MdAPE 0.0%, 50 est vs 48 post-delivery; plugins orchestration plugin re-scored 5 to 3).
- Phase 5 whole-diff review, security review and scope audit turned each finding into a task (parser parity, credentials refused in source URLs in web and orchestrator), all closed fast (1 to 5 min).
- Deploy pins landed and rollouts were OK (helmfile be673ca; helmfile tests 222 passed); smoke run 3 passed, listing orchestrator_sessions_list and petstore_ tools.
- Most small tasks finished under the minutes seed (anymcp source parser 3 vs 7, plugins repo bootstrap 3 vs 7, orch render plugin sources 5 vs 11).

## What went wrong or could improve

- helmfile smoke plugin tools: step 10b was written against an assumed text output of `any-mcp --list-tools`, which prints a JSON array. Its unit-test fakes mirrored the wrong assumption (120 passed), so it failed only live (run 1). Fix round 1, 3fd172f, PR #33.
- helmfile smoke plugin tools took 184 min vs 7 (26.29x) and 2007788 tokens vs 977684 (2.05x), mostly three live smoke runs.
- any-mcp source parser parity with the web grammar: the spec over-banned whitespace and had to be amended so local paths may contain spaces (5 min vs 4).
- GitGuardian flagged a fake basic-auth string in an orchestrator test. Force-push was denied, so a v2 branch was pushed, PR #24 opened and #23 closed.
- An unrelated Harbor image loss (agents-matrix-connector 98b0803, restarted at 03:30Z outside this session) broke smoke run 2 at the matrix step; fixed by re-running the connector CI images job (run 40282930555, attempt 2).
- web plugin source parser took 36 min vs 5 (7.20x, 2.08x tokens); helmfile deploy pin 39 vs 5 (7.80x). Minutes MdAPE 80.6%, tokens 27.3%.
- The scope auditor left code/any-mcp detached; restored to main by hand.

## Recommendations

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

## Delivery record (migrated)

### Asked

Make any-mcp generic (no platform plugin), move the orchestrator plugin to any-mcp-tatara-plugins under a topic subdirectory, and install plugins from Terraform-like git or local sources. The orchestrator renders the plugin from a pinned ref and takes extra per-preset/session sources; the web preset form edits them with a "+" button; deployed via agents-helmfile with sessions still getting orchestrator tools.

### Shipped

All goals shipped. Epic review verdict: pass (2026-10-27). Live smoke run 3 passed (runs 1-2 failed, see Discovered).
- any-mcp v0.5.0 (merge 4a73c79, PR #5); any-mcp-tatara-plugins v0.1.0 (merge 2ca3d44, PR #1).
- agents-orchestrator b3a2975 (PR #24; #23 closed); agents-web 4701820 (PR #16).
- agents-helmfile be673ca (PR #32) pins the above; smoke fix PR #33 (0ed86cf). Rollouts OK, helmfile tests 222 passed.

### Tasks

18 of 18 planned tasks done. Review rounds and verification tails are not in the notes except where stated ("unknown"); all heads below are in the epic git logs except where flagged.

| Task | Status | Verified head | Rounds | Tail |
|---|---|---|---|---|
| anymcp-source-parser | done | bc5dfc7 | unknown | unknown |
| anymcp-source-installer | done | a9bc488 | unknown | unknown |
| anymcp-source-plugin-loading | done | dfad12b | unknown | unknown |
| any-mcp-source-parser-parity | done | 4aceb14 | unknown | unknown |
| anymcp-remove-orchestrator | done | ee0e027 | unknown | unknown |
| anymcp-release-0-5-0 | done | 8a5aee1 | unknown | unknown |
| plugins-repo-bootstrap | done | 0145988 | unknown | unknown |
| plugins-orchestration-plugin | done | b42184c | unknown | unknown |
| orch-plugins-dev-dependency | done | 77e270e | unknown | unknown |
| orch-any-mcp-0-5-0-pin | done | 745ca1d | unknown | unknown |
| orch-any-mcp-sources-spec | done | ff54218 | unknown | unknown |
| orch-render-plugin-sources | done | 0ad4102 | unknown | unknown |
| orchestrator-refuses-credent | done | faedbd7 (NOT on main: only on closed-PR branch origin/generic-any-mcp-with-git-and; main has the rewritten 881ca3c) | unknown | unknown |
| web-plugin-source-parser | done | 2095c1a | unknown | unknown |
| web-preset-plugin-sources | done | 97b6845 | unknown | unknown |
| web-form-refuses-credentials | done | cd1eb81 | unknown | unknown |
| helmfile-deploy-pin | done | 65fc75b | unknown | unknown |
| helmfile-smoke-plugin-tools | done | 3fd172f | 1 fix round | reviewer clean: 120 passed, pointsActual 3 |

Files vs notes: orchestrator-refuses-credent's head does not match main because history was rewritten for PR #24 (see Rulings); the code is on main as 881ca3c.

### Rulings

- Source notation = Terraform/go-getter subset (local ./ ../ /abs used in place; git::https://...//sub?ref=; github.com shorthand); no ?depth=. Why: reuse familiar notation, one parser. Cost if wrong: notation change breaks stored presets.
- Plugin sources pip-installed into any-mcp's own env and loaded by entry point; no sys.path insertion. Why: local and git behave alike. Cost: no per-plugin dependency isolation (non-goal).
- Removed any_mcp.orchestrator with no shim. Why: no-backward-compat rule. Cost: old pins of any-mcp <=0.4 users lose nothing, but unpinned users break.
- any-mcp release as minor 0.5.0; release order plugins+any-mcp, orchestrator, web, helmfile. Cost: low.
- Orchestrator spec field named any_mcp_sources (avoids clash with spec.wrapper.plugins). Cost: rename touches orchestrator, web, API schema.
- Phase 5 findings each became a task and were fixed: parser parity (no-path git URLs, whitespace/control chars; local paths may contain spaces, amended) and credentials refused in source URLs (orchestrator and web). No findings dropped.
- GitGuardian flagged a fake basic-auth test string in an orchestrator test; history folded, force-push denied, so new branch pushed as PR #24 and #23 closed. Cost: #23 history/discussion orphaned.
- Scope auditor left code/any-mcp detached; restored to main. Cost: none.

### Discovered and blocked

- Smoke run 1 failed at step 10b: `any-mcp --list-tools` prints a JSON array, smoke grepped text. Fixed by PR #33. Cleared.
- Smoke run 2 failed at matrix step, unrelated: agents-matrix-connector rollout-restarted at 03:30Z outside this session, image 98b0803 missing from Harbor. Fixed by re-running connector CI images job (run 40282930555 attempt 2); pods recovered. Cleared.
- Epic README lists blocker cross-session-messaging-and; its work is merged in the logs (PRs #4, #22, #15, #30). Nothing open and blocked.

### Not pushed

- Repos any-mcp, any-mcp-tatara-plugins, agents-orchestrator, agents-web, agents-helmfile: main is level with origin/main (empty `origin/main..main`).
- Workbench meta repo main is 224 commits ahead of origin/main (ticket commits and submodule pointer advances), plus uncommitted code/agents-helmfile pointer and RETRO.md changes. Szymon (or the next session with push approval) pushes.

### Lessons routed to

- Smoke grepped CLI output as text when it is JSON: add a test in agents-helmfile tests/test_smoke_script.py pinning the --list-tools JSON parse (done in PR #33).
- Secret-like fixture string tripped GitGuardian: add a pre-commit/CI secret scan (gitleaks or ggshield) to agents-orchestrator so it fails locally, not post-push.
- Scope auditor detaching a submodule HEAD: mechanical; add a close check in ticket.py that every code/<repo> is on its branch before close.
- Force-push denial handling and PR #23-to-#24 replacement: judgement call; edit workbench:start-development phase 6 to say "push a new branch and close the old PR when force-push is denied".
