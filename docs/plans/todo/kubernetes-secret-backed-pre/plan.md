---
title: Kubernetes Secret backed preset env
repos: [agents-orchestrator, agents-web]
created: 2026-10-29
owner: ""
rung: ""
---

# Kubernetes Secret backed preset env

## What and why

What: Presets can carry secret env values that are stored in a Kubernetes Secret and reach the agent container through secretKeyRef, instead of plain text in the preset spec.
How: Unqueued: planned only when the user queues it (a separate secrets field, secretKeyRef in the StatefulSet, per paste-.env debug findings Q3).
Why: User decision 2026-10-29 02:36Z via mx-34 #324 on paste-.env Q3 ('all recommended, go'): Kubernetes-Secret-backed env is its own epic, not part of the paste-.env fix; today preset env values are stored and rendered in plain text (agents-orchestrator k8s/render.py).

## Scope ladder

### Rung 1: agreed scope (migrated)

none recorded in the epic format

## Agreed scope

not agreed yet

## Non-goals

none recorded in the epic format

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
