---
title: any-mcp
blockers: []
stage: build
owner: ""
repos: [any-mcp]
created: 2026-10-22
---

# any-mcp

## Project brief

What: any-mcp, a Python MCP server that exposes any API, or groups of APIs, as MCP tools through plugins; it does nothing on its own.
How: plugins subclass one ABC (load_tools required, other hooks defaulted); the core owns validation, errors, naming, reload, response budgets and both transports on FastMCP 4.x behind one adapter; shipped as a pip-installable package and git tag v0.1.0.
Why: users write only the business logic of an API instead of a whole MCP server, and the agent-orchestrator agent image preinstalls any-mcp in every session.

## Description

any-mcp: an MCP server that does nothing on its own and exposes any API, or groups of APIs, as MCP tools through a plugin system. A plugin subclasses an abstract base class and overrides hook methods (tool load/reload, call, response shaping, errors). Runs over stdio by default and over streamable HTTP. Very well documented, with small and big plugin examples; plugins must be trivial to write. An MCP-to-API proxy that owns the common work so users provide only business logic.

## Goals

- A plugin ABC whose only required hook returns the tool list; optional hooks have working defaults.
- Plugin discovery via entry points and config module:Class entries.
- stdio and streamable HTTP from one entrypoint, current MCP spec plus legacy clients.
- A built-in OpenAPI plugin as the big example, a one-method hello-world plugin as the small one.
- Docs: concepts, plugin authoring guide, both examples, configuration and transport reference.
- Published as a pinned git tag installable with pip.

## Non-goals

- No business-logic plugins beyond the examples.
- No auth gateway; client tokens are never forwarded downstream.

## Time

Estimate: 122 agent-min | Critical path: 75 min | Expected wall at P=2.3: 2.5 h (k=2.0) | Actual: 0 min | Remaining estimate: 122 min

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
