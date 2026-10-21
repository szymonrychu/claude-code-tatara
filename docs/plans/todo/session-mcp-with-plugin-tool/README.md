---
title: Session MCP with plugin tools
blockers: []
stage: build
owner: ""
repos: [workbench]
created: 2026-10-21
---

# Session MCP with plugin tools

## Project brief

What: An internal MCP server: a single session tool that routes a message into the same session as user input, plus a plugin system exposing API endpoints and logic as MCP tools
How: research the harness injection surfaces and prior art, then design a plugin-based MCP server with the session tool as its first plugin
Why: self-compact and self-reload need a human today; API integrations need hand-written MCP servers

## Description

User idea, 2026-10-21:
1. An internal MCP tool that can make the session self-compact or self-reload plugins. When called, the MCP server routes a message back into the same session, and that message runs exactly as if the user had typed it (for example `/compact` or `/reload-plugins`). Trace other tools that do this, and ideally expose a single tool for it.
2. The MCP server also lets people write plugins. Each plugin exposes one or more API endpoints, together with its own logic, as tools inside the MCP server.
3. The internal session tool reuses that same plugin mechanism.

## Goals

- A single MCP tool that injects a message into the calling session as user input, covering slash commands such as /compact and /reload-plugins, if the harness allows it. If it does not, the brief says so and gives the closest supported mechanism.
- A plugin mechanism where each plugin declares API endpoints and logic that the MCP server exposes as tools.
- The internal session tool is implemented as a plugin of that mechanism.

## Non-goals

- Bypassing the harness's permission prompts or trust model.

## Time

Derived by `ticket.py tasks` and `apply-run` from the task `estimate` and `actual` fields; never edit by hand. Report only, never a budget.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
