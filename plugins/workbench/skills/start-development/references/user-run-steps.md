# User-run steps

Use when a command must be run by the user because the auto-mode classifier or a safety rule keeps it from the
agent: kernel upgrades, firmware flashes, anything that reboots or rewrites a device. The orchestrator checks the
state before and after and parses the result, so the user only pastes one line.

## Spec

JSON, written by the orchestrator:

```json
{"name": "kernel-upgrade", "command": "sudo apt install linux-image-6.1", "pre": ["test -f /boot/vmlinuz"],
 "post": ["uname -r"], "expect": "6\\.1"}
```

`pre` and `post` are lists of shell checks run with `bash -c`. They are read-only: a check containing a `>` or `>>` write
(only `>/dev/null`, `2>/dev/null`, `&>/dev/null` and `2>&1` are allowed), `sudo`, `rm `, `tee ` or `dd ` is rejected before anything runs (exit 2). The mutating work belongs in `command`.

## Flow

1. Write the spec.
2. `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/user-run-step.py prepare <spec>` prints `PRE ok <cmd>` or
   `PRE FAIL <cmd> exit <n>` per check. Any failure exits 1: fix the cause, do not hand over the command.
   When all pass it prints `! <command>`.
3. Hand that `! <command>` line to the user to paste, and wait for them to say it ran.
4. `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/user-run-step.py check <spec>` runs each `post` check and matches
   `expect` (a regex) against their combined output. It prints `RESULT pass` or `RESULT fail: <reason>`, then the
   last 20 lines of output; exit 0 or 1.
5. Record the RESULT line in the run notes. On fail, show the user the tail and agree the next step.
