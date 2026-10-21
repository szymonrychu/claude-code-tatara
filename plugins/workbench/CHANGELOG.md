# Changelog

## v1.0.0 - 2026-10-20

First release of the template's plugin. Copied from the workbench plugin v2.1.0, split into a core plugin and optional packs, and depersonalized.

### Features

- Development flow with one approval gate, an approval ledger, file-based epic tickets and research skills
- Tiered review with a script+haiku verifier, gated review and debugging flows
- Verification hooks that tie every test run to the committed HEAD
- Per-subagent worktree isolation and deterministic plan execution
- Read-only diagnostic subagents and destructive-command guardrails
- Optional packs (infra, observability, secrets) enabled through the root marketplace
