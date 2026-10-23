---
title: cluster presets
blockers: [web-ui-cluster-tabs-with-fil]
stage: build
owner: ""
repos: [agent-orchestrator, agents-helmfile]
created: 2026-10-23
---

# cluster presets

## Project brief

What: Named ClusterSpec presets (create, copy, edit, delete) with a seeded 1-pod default; scheduling a cluster takes only a preset; live cluster edit is removed; Presets is the first settings category in the hamburger menu
How: A presets table written only by the api, CRUD routes, POST /clusters accepting a preset id and snapshotting its spec at create, the ClusterForm reused as the preset editor, PATCH /clusters retired with retirement tests
Why: Scheduling becomes one choice instead of a long form, repeatable setups are kept, and running clusters never restart under a live spec edit

## Description

User request (2026-10-23), verbatim:

"Live session edit is not needed. Third epic- instead of during scheduling editing, allow to prepare presets, so during scheduling only preset is required. Provide default preset (1 pod). Presets should be copiable, editable, removable, creatable. Hamburger menu on the top left side show all sessions tabs (from top) and all settings from bottom (atm "presets" is the only real setting category showing there)"

Coordinator scope (2026-10-23): a preset is a stored, named ClusterSpec template with create, copy, edit and delete; a seeded default preset has 1 pod; scheduling a cluster takes a preset and nothing else; the ClusterForm becomes the preset editor; live cluster edit (PATCH of a running cluster's spec and the UI edit mode) is removed; a running cluster keeps the spec snapshotted at create when its preset is edited or deleted.

"Session" is an orchestrator cluster, as in web-ui-cluster-tabs-with-fil. Research findings with citations are in research.md next to this README.

## Goals

- Presets: named, stored ClusterSpec templates with create, copy, edit and delete through /api/v1 and the UI.
- A seeded default preset with 1 pod (replicas 1) always exists.
- Scheduling a cluster from the UI takes a preset and nothing else (the slug is generated, overridable); the cluster stores a snapshot of the preset's spec taken at create, plus which preset it came from.
- Editing or deleting a preset never changes a running cluster.
- The ClusterForm becomes the preset editor, prefilled from /meta defaults for a new preset and from the source preset for a copy.
- Live cluster edit is removed: PATCH /api/v1/clusters/{id}, its schema, repository function, client call and the form's edit mode go, pinned by retirement tests.
- The hamburger menu built by web-ui-cluster-tabs-with-fil gets its first settings category, Presets, at the bottom.
- Deployed: image and chart bumped in agents-helmfile, applied, smoke OK.

## Non-goals

- No preset versioning or history beyond the snapshot each cluster keeps.
- No per-user presets (the UI has no users).
- No settings categories other than Presets.
- No change to how a created cluster is reconciled, dispatched or discarded.

## Time

Derived by `ticket.py estimate`, `tasks` and `apply-run` from the task `estimate` and `actual` fields into one line (`Estimate | Critical path | Expected wall at P= | Actual | Remaining estimate`); never edit by hand. Report only, never a budget.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
