---
title: Kubernetes Secret backed preset env
blockers: []
stage: build
owner: ""
repos: [agents-orchestrator, agents-web]
created: 2026-10-29
---

# Kubernetes Secret backed preset env

## Project brief

What: Presets can carry secret env values that are stored in a Kubernetes Secret and reach the agent container through secretKeyRef, instead of plain text in the preset spec.
How: Unqueued: planned only when the user queues it (a separate secrets field, secretKeyRef in the StatefulSet, per paste-.env debug findings Q3).
Why: User decision 2026-10-29 02:36Z via mx-34 #324 on paste-.env Q3 ('all recommended, go'): Kubernetes-Secret-backed env is its own epic, not part of the paste-.env fix; today preset env values are stored and rendered in plain text (agents-orchestrator k8s/render.py).

## Description



## Goals



## Non-goals



## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
