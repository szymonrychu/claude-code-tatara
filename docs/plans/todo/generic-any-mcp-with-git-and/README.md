---
title: Generic any-mcp with git and local plugin sources
blockers: []
stage: build
owner: ""
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
