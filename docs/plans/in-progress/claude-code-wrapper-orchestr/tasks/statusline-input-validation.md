---
title: statusline input validation
status: done
repo: claude-code-wrapper
value: "malformed statusline input is a 400, never a 500"
files: [src/claude_code_wrapper/internal_api.py, README.md, tests/test_internal_api.py]
verify: "uv run pytest tests/test_internal_api.py tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [idle-since-in-snapshot, user-message-event, history-before-seq-and-types, peer-mesh-view-route, statusline-relay, context-in-snapshot-and-sse, on-start-instance-hook]
owns: []
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/claude-code-wrapper-orchestr-statusline-input-validation/claude-code-wrapper
branch: claude-code-wrapper-orchestr-statusline-input-validation
verified_head: 195bfaced052cb7ef199dc40e34ccbfc6cafe1c7
run: claude-code-wrapper-orchestr
provides: []
acs_for_audit: []
process_gaps: []
---

# statusline input validation

## Requirement

Review + security finding (medium/low): parse_statusline (internal_api.py:43-60) only checks current_usage is a dict, so _derive_context's int(usage.get(key) or 0) raises ValueError/TypeError/OverflowError on non-numeric values and the route returns 500. Validate the token fields of current_usage and context_window as finite non-negative numbers in parse_statusline and return 400 otherwise; enforce a server-side request body cap on POST /internal/statusline (matching the client's MAX_STDIN 4096 bytes) with 413. Also add to README 'Trust model' that user_message events carry prompt text and file names into the event log, SSE and history (redacted by the configured redactor only).

## Acceptance conditions

- AC1: non-numeric or non-finite token values return 400, not 500 [evidence: test:tests/test_internal_api.py::test_statusline_rejects_non_numeric_usage]
- AC2: a body over the cap returns 413 [evidence: test:tests/test_internal_api.py::test_statusline_body_cap]
- AC3: README Trust model documents user_message content in history [evidence: test:tests/test_readme_api.py]

## Files

- `src/claude_code_wrapper/internal_api.py`
- `README.md`
- `tests/test_internal_api.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The requirement above holds, pinned by the acceptance tests.

What is true and observable when the task is done.

## Steps

- Write the failing acceptance tests; run red.
- Implement; run green with the verify command.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
