---
name: handoff
description: >
  Write a handoff file so multi-day work resumes in a fresh session: state, what
  is done, next steps in order, gotchas and suggested skills, as references, with
  secrets redacted. Use when the user says "handoff", "hand this off", "I'm
  stopping for today" or the context is about to run out.
---

# handoff

A handoff lives at `docs/handoffs/<YYYY-MM-DD>-<slug>.md` in the workbench root. The
directory is gitignored and survives reboots (the OS temp dir does not).

```sh
python3 "${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/handoff.py" new --slug <slug>
python3 "${CLAUDE_PLUGIN_ROOT}/skills/handoff/scripts/handoff.py" redact <path>
```

1. `new --slug <short-kebab-topic>` creates the file and prints its path. It refuses to
   overwrite an existing file: pick another slug, or edit the existing handoff.
2. Fill every section, in this order: **State** (where things stand now, branch, worktree),
   **Done**, **Next** (numbered, in the order to do them), **Gotchas** (traps, failed
   approaches, open questions), **Suggested skills** (the skills the next session should
   load).
3. Use references, not copies: file paths, commit SHAs, PR URLs, ticket ids. Never paste
   code, logs or document content that already lives somewhere.
4. Never write secrets. Run `redact <path>` before finishing anyway: it replaces the value
   of `NAME=value` / `NAME: value` lines whose name contains TOKEN, SECRET, PASSWORD,
   API_KEY or PRIVATE, bearer tokens and PEM private-key blocks with `<redacted>`.
5. Print the path as the last line of your answer. The next session resumes with
   `continue from <path>`.
