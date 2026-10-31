---
title: Session MCP with plugin tools
repos: [workbench]
created: 2026-10-21
owner: ""
rung: ""
---

# Session MCP with plugin tools

## What and why

What: An internal MCP server: a single session tool that routes a message into the same session as user input, plus a plugin system exposing API endpoints and logic as MCP tools
How: research the harness injection surfaces and prior art, then design a plugin-based MCP server with the session tool as its first plugin
Why: self-compact and self-reload need a human today; API integrations need hand-written MCP servers

User idea, 2026-10-21:
An MCP server that lets people write plugins: each plugin exposes one or more API endpoints, together with its own logic, as tools inside the MCP server.

Scope change by the user, 2026-10-21: "Just plugins, no self messages". The internal self-compact/self-reload session tool is dropped.

## Scope ladder

### Rung 1: agreed scope (migrated)

- 1.1: A plugin mechanism where each plugin declares API endpoints and logic that the MCP server exposes as tools.

## Agreed scope

not agreed yet

## Non-goals

- Any tool that sends messages into its own session (self-compact, self-reload): dropped by the user.
- Bypassing the harness's permission prompts or trust model.

## Design

none recorded in the epic format

## Decisions

none recorded in the epic format

## Open questions

none

## Research

none recorded in the epic format

## Irreversible operations

none

## Migrated notes

### README.md: Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
