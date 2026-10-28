---
title: Semver image tags at the end of main builds
blockers: []
stage: build
owner: ""
repos: [agents-orchestrator, agents-web, agents-webhook, agents-schedule, agents-matrix-connector, agents-helmfile]
created: 2026-10-28
---

# Semver image tags at the end of main builds

## Project brief

What: A release job at the end of every green main build tags the image X.Y.Z, X.Y and X and pushes git tag vX.Y.Z; helmfile pins X.Y.Z.
How: Tested in-repo next-version script over conventional commits, regctl image copy for manifest-only retags, contents: write and a concurrency group on the release job.
Why: Harbor retention prunes sha7 tags within hours and broke deployed pods (incident 2026-10-28); semver tags survive it.

## Description

Incident 2026-10-28: Harbor retention pruned the sha7 image tags pinned in agents-helmfile (agents-orchestrator 96e46f3, agents-web 01e971c, agents-webhook 838ba1f, agents-schedule 6cfa955, agents-matrix-connector 98b0803), so new pods hit ImagePullBackOff and only node-cached pods kept running. Semver tags survive retention (claude-code-wrapper keeps 0.2.0..0.3.1 for days while every sha7 tag of the other repos was pruned within hours).

Each image-building repo gets a release step at the end of a green main build: a tested in-repo script computes the next version from conventional commits since the last vX.Y.Z git tag, the job pushes git tag vX.Y.Z and retags the already-pushed sha7 image as X.Y.Z, X.Y and X with regctl image copy (manifest only). agents-helmfile then pins every component to its X.Y.Z image and the cluster is applied.

## Goals

- Every green push to main in agents-orchestrator, agents-web, agents-webhook, agents-schedule and agents-matrix-connector ends with a release job that needs every other job of the run and computes the next version with a tested in-repo script: BREAKING (`!` or `BREAKING CHANGE` footer) bumps major, `feat` bumps minor, anything else bumps patch, from the last vX.Y.Z tag.
- The release job pushes git tag vX.Y.Z and image tags X.Y.Z, X.Y and X of the run's sha7 image to harbor.szymonrichert.pl/containers/<repo>, without re-uploading layers.
- Release jobs never race: one concurrency group per repo, full history and tags fetched.
- Tests that pin the CI layout are updated to the new layout, and each repo's lint and tests pass.
- agents-helmfile pins every one of the five components to an X.Y.Z image tag released by this epic, and the agents namespace is applied and healthy with every pod pulling a semver tag.

## Non-goals

- Changing Harbor's retention policy (no admin access; semver tags already survive it).
- claude-code-wrapper, any-mcp, agents-common, any-mcp-tatara-plugins release flows.
- A shared reusable workflow or shared CI repo; each repo stays independent.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
