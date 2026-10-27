---
title: Generic any-mcp with git and local plugin sources
blockers: [cross-session-messaging-and]
stage: review
owner: Szymon Richert
repos: [any-mcp, any-mcp-tatara-plugins, agents-orchestrator, agents-web, agents-helmfile]
created: 2026-10-26
---

# Generic any-mcp with git and local plugin sources

## Project brief

What: any-mcp becomes generic; platform plugins move to any-mcp-tatara-plugins by topic; plugins install from Terraform-module-like git or local sources
How: Source parser and installer in any-mcp, orchestration topic in the plugins repo, orchestrator renders sources and a per-session sources list, preset form + button, helmfile deploy
Why: Keep any-mcp reusable outside this platform and let sessions pull platform tools from a versioned plugin bucket

## Description

Make any-mcp a generic MCP server with no platform-specific tools, and move those tools to the new repo any-mcp-tatara-plugins, grouped into topic subdirectories. any-mcp gains plugin installation from Terraform-module-like sources: a git repo with an optional subdirectory and ref, or a local directory (for pip-installed any-mcp). The orchestrator renders its reserved orchestrator plugin from the plugins repo and lets presets and sessions list extra plugin sources, which the web preset form edits with a "+" button adding one pasteable line per source.

## Goals

- any-mcp contains no platform-specific plugin; the orchestrator plugin lives in any-mcp-tatara-plugins under a topic subdirectory, with the same tools and behaviour.
- any-mcp installs and loads plugins from Terraform-module-like sources: git repo with optional //subdir and ?ref=, and local directory paths.
- any-mcp-tatara-plugins is a working repo: topic subdirectories, per-plugin packages, tests and lint in CI, documented source notation.
- agents-orchestrator renders the orchestrator plugin from the plugins repo at a pinned ref and accepts a list of extra plugin sources per preset and session, installed in agent pods.
- The agents-web preset form edits the plugin sources: a "+" button adds a one-line text box per source, several sources allowed.
- Deployed through agents-helmfile; agent sessions still get the orchestrator tools.

## Non-goals

- No backward-compatibility alias for the removed any_mcp.orchestrator module.
- No plugin registry or marketplace beyond git and local sources; no `?depth=` or archive (http tarball) sources.
- No per-plugin dependency isolation (separate venvs or processes).

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-27)

# generic-any-mcp-with-git-and - review and close notes (2026-10-27)

Phase 5: whole-diff review, security review and scope audit ran across any-mcp, any-mcp-tatara-plugins, agents-orchestrator, agents-web and agents-helmfile. Each finding became a task and was fixed:
- web/any-mcp parser parity: no-path git URLs, whitespace/control characters; local paths may contain spaces (amended).
- orchestrator refuses credentials in source URLs.

Notable events:
- GitGuardian flagged a fake basic-auth string in an orchestrator test. I folded the fix into history, but force-push was denied, so I pushed a new branch, opened PR #24 and closed #23.
- The scope auditor left code/any-mcp detached; restored to main.

Deploy:
- Pins: helmfile be673ca (orchestrator b3a2975, web 4701820, any-mcp v0.5.0, plugins v0.1.0). Rollouts OK; helmfile tests 222 passed.

Live smoke:
- Run 1: failed at step 10b. `any-mcp --list-tools` prints a JSON array, and the smoke grepped `^petstore_` as text.
- Fix: task helmfile-smoke-plugin-tools, fix round 1, 3fd172f.
  - The reviewer found it clean: 120 passed, pointsActual 3.
  - Merged as agents-helmfile PR #33 (0ed86cf).
- Run 2: failed at the matrix step, unrelated to this epic.
  - Cause: agents-matrix-connector was rollout-restarted at 03:30Z outside this session, and image 98b0803 was missing from Harbor.
  - Fix: re-ran the connector CI images job (run 40282930555, attempt 2) to re-push the tag; the pods recovered.
- Run 3: passed. Log: .logs/plugins-smoke-rerun2.log.
  - "orchestrator plugin installed from any-mcp-tatara-plugins//orchestration/orchestrator?ref=v0.1.0; --list-tools lists orchestrator_sessions_list"
  - "extra source git::https://github.com/szymonrychu/any-mcp//examples/petstore?ref=v0.5.0 installed ...; --list-tools lists petstore_ tools"
