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

What: 
How: 
Why: 

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

Derived by `ticket.py estimate`, `tasks` and `apply-run` from the task `estimate` and `actual` fields into one line (`Estimate | Critical path | Expected wall at P= | Actual | Remaining estimate`); never edit by hand. Report only, never a budget.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
