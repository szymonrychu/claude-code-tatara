---
title: Em dash commit guard
status: todo
repo: workbench
value: No agent can commit a message containing an em dash
files: [plugins/workbench/hooks/lib/core.py, plugins/workbench/hooks/tests/test_guard_bash.py, plugins/workbench/skills/start-development/references/hooks.md]
verify: "bash plugins/workbench/scripts/run-tests.sh --only hooks && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint"
depends_on: [em-dash-edit-guard]
model: sonnet
review: ""
verified_head: ""
---

# Em dash commit guard

## Requirement

User requirement (U1, verbatim): "no em dash characters in any code, comment, commit, message, or content of any kind".

Design D5: guard-bash denies a `git commit` whose message carries U+2014. When any normalised segment of the command (after `_normalize`, so `git -C <dir> commit` counts) matches `^git\s+commit\b` and the whole command contains U+2014, deny; this covers `-m`, a heredoc and `$(cat <<EOF ... EOF)` because heredoc lines are segments of the same command. For `-F <file>`, `-F<file>`, `--file <file>` and `--file=<file>`, the guard reads the file (relative to the event cwd) when it exists and denies when it contains U+2014; a missing or unreadable file is not a deny. The reason names U+2014 and tells the agent to use a plain hyphen.

## Acceptance conditions

- AC1: `git commit -m "<text with U+2014>"` is denied, and `git -C repo commit -m ...` too [evidence: test:plugins/workbench/hooks/tests/test_guard_bash.py::test_commit_message_em_dash_denied]
- AC2: a heredoc message and a `$(cat <<'EOF' ... EOF)` message holding U+2014 are denied [evidence: test:plugins/workbench/hooks/tests/test_guard_bash.py::test_commit_heredoc_em_dash_denied]
- AC3: `git commit -F msg.txt` and `--file=msg.txt` are denied when the file holds U+2014, allowed when it does not, and allowed when the file is missing [evidence: test:plugins/workbench/hooks/tests/test_guard_bash.py::test_commit_message_file_em_dash]
- AC4: a commit with a plain-hyphen message and a non-commit command are not denied by this rule [evidence: test:plugins/workbench/hooks/tests/test_guard_bash.py::test_commit_without_em_dash_allowed]
- AC5: references/hooks.md documents the commit check under guard-bash [evidence: command:grep -n "git commit" plugins/workbench/skills/start-development/references/hooks.md]
- AC6: hooks and start-development suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only hooks && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

## Files

- `plugins/workbench/hooks/lib/core.py`
- `plugins/workbench/hooks/tests/test_guard_bash.py`
- `plugins/workbench/skills/start-development/references/hooks.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
