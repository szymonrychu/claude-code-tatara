# Superpowers-based plan flow replaces the workbench flow retro

## Review

- Final verify: `mise run test && mise run lint` exit 0 at 53cf94cc; `[test:superpowers] 309 passed`, `[test:scripts] 463 passed, 62 skipped, 2 deselected`, every plugin family PASS.
- Fix rounds run: 0. Findings: none, undelivered and over-delivered empty.

## What went well

- All 21 steps landed as one commit each, test-first, in plan order.
- The retargeted tests (test_release, test_templates, test_ticket_flow_docs) kept equivalent or stricter pins.
- The SessionStart hook only reads a local file and prints JSON; no network, no writes.

## What went wrong or could improve

- Chunk 4 touched S18's area early (skills emit fix in S14), so S18 became a pin-only step; plan the emit gap into S14.
- Upstream tests needed fixes outside the step lists (S11 scratch-dir pin, S8 sdd-workspace home path); steps should list suites a vendored file can trip.
- S5 said "root constants only" but test_release changed far more; the sizing note was inaccurate.

## Recommendations

- Discovered and not built:
  - Subagent briefs in cache-loaded repos need the absolute ticket.py path; a relative or plugin-root path does not resolve there.
  - A drift test between the UPSTREAM.md VENDORED list and the skills directory.
- Out-of-scope ideas: none.
- Impossible at planning time: how many upstream tests and scratch-dir or home-path pins a vendored file trips; ask the plan-writer to run the suites against a dry-copy of the vendored files.
