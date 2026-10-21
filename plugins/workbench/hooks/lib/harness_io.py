"""Harness payloads in, harness output out, for the non-Claude harnesses.

`normalize(harness, event, payload)` turns the stdin JSON of Copilot, Cursor,
Codex, Gemini CLI or Antigravity into a `NormalizedEvent` for `core.decide`;
`render(harness, event, decision)` turns the `Decision` back into the JSON that
harness reads. Shapes come from docs/research/multi-harness.md sections 1e, 2e,
3e, 4A e, 4B e and the table in section 6.

Normalization is deliberately tolerant: tool names and field spellings from every
harness map through one table, because the same harness can hand over different
shapes (Copilot's camelCase CLI payload versus its PascalCase VS Code-compatible
one, Cursor's native payload versus a Claude-format hook it imported). A tool the
table does not know is kind `other`, which every guard allows.

Guards deny, never ask: no rendered output carries `ask`.
Stdlib only, Python 3.9+.
"""

from __future__ import annotations

import json
from typing import Any

from .apply_patch import patch_paths
from .core import Decision, NormalizedEvent

HARNESSES = ("copilot", "cursor", "codex", "gemini", "antigravity")

# Tool name -> kind. One table for every harness; names never collide in meaning.
TOOL_KINDS = {
    # shell
    "Bash": "shell",  # Claude names: Copilot PascalCase, Codex, Cursor third-party
    "bash": "shell",  # Copilot CLI native
    "Shell": "shell",  # Cursor
    "run_shell_command": "shell",  # Gemini CLI
    "run_command": "shell",  # Antigravity
    "run_in_terminal": "shell",  # VS Code Local (undocumented)
    # edit
    "Edit": "edit",
    "MultiEdit": "edit",
    "NotebookEdit": "edit",
    "edit": "edit",  # Copilot CLI native
    "apply_patch": "edit",  # Codex (patch text in tool_input.command)
    "replace": "edit",  # Gemini CLI
    "replace_file_content": "edit",  # Antigravity
    "multi_replace_file_content": "edit",  # Antigravity
    "replace_string_in_file": "edit",  # VS Code Local (undocumented)
    "multi_replace_string_in_file": "edit",  # VS Code Local (undocumented)
    "insert_edit_into_file": "edit",  # VS Code Local (undocumented)
    # write
    "Write": "write",  # Claude, Cursor (Cursor maps Edit to Write too)
    "create": "write",  # Copilot CLI native
    "write_file": "write",  # Gemini CLI
    "write_to_file": "write",  # Antigravity
    "create_file": "write",  # VS Code Local (undocumented)
    # read
    "Read": "read",
    "view": "read",
    "read_file": "read",
    "view_file": "read",
}

_TOOL_NAME_KEYS = ("tool_name", "toolName")
_TOOL_INPUT_KEYS = ("tool_input", "toolInput", "toolArgs", "tool_args", "arguments", "input")
_COMMAND_KEYS = ("command", "CommandLine", "commandLine", "command_line", "cmd")
_PATH_KEYS = (
    "file_path",
    "filePath",
    "path",
    "TargetFile",
    "targetFile",
    "target_file",
    "AbsolutePath",
    "absolute_path",
    "notebook_path",
)
_PATH_LIST_KEYS = ("paths", "filePaths", "file_paths", "files")
# Strings that may carry an apply_patch envelope (Codex puts it in `command`).
_PATCH_KEYS = ("command", "input", "patch")
_TOOL_CWD_KEYS = ("working_directory", "Cwd", "cwd", "dir_path", "directory")
_WORKSPACE_KEYS = ("workspace_roots", "workspacePaths", "workspace_paths")
_EVENT_NAME_KEYS = ("hook_event_name", "hookEventName")
_STOP_ACTIVE_KEYS = ("stop_hook_active", "stopHookActive")
_TRANSCRIPT_KEYS = ("agent_transcript_path", "agentTranscriptPath")
_RESULT_KEYS = ("tool_response", "toolResponse", "toolResult", "tool_result", "tool_output")
_SHELLS = ("bash", "sh", "zsh", "/bin/bash", "/bin/sh", "/bin/zsh", "/usr/bin/env")

# The Claude event name `core` keys verify-recorder off, per normalized event.
_CLAUDE_EVENT = {"pre-tool": "PreToolUse", "post-tool": "PostToolUse", "stop": "Stop"}


class UsageError(ValueError):
    """An unknown harness or event."""


def _first(data: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return None


def _str(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _tool_input(data: dict[str, Any]) -> dict[str, Any]:
    raw = _first(data, _TOOL_INPUT_KEYS)
    if isinstance(raw, str):
        # Copilot CLI sends `toolArgs` as a JSON string.
        try:
            raw = json.loads(raw)
        except ValueError:
            return {"command": raw}
    return raw if isinstance(raw, dict) else {}


def _command(tool_input: dict[str, Any]) -> str:
    value = _first(tool_input, _COMMAND_KEYS)
    if isinstance(value, list) and all(isinstance(part, str) for part in value):
        # argv form: `["bash", "-lc", "<script>"]` runs the script; else join.
        if len(value) >= 3 and value[0] in _SHELLS and value[1] in ("-c", "-lc", "-ic"):
            return value[2]
        return " ".join(value)
    return _str(value)


def _paths(tool_input: dict[str, Any]) -> list[str]:
    found: list[str] = []

    def add(path: Any) -> None:
        if isinstance(path, str) and path and path not in found:
            found.append(path)

    for key in _PATH_KEYS:
        add(tool_input.get(key))
    for key in _PATH_LIST_KEYS:
        value = tool_input.get(key)
        if isinstance(value, list):
            for path in value:
                add(path)
    for key in _PATCH_KEYS:
        text = tool_input.get(key)
        if isinstance(text, str) and "*** Begin Patch" in text:
            for path in patch_paths(text):
                add(path)
    return found


def _cwd(data: dict[str, Any], tool_input: dict[str, Any]) -> str:
    base = _str(data.get("cwd"))
    if not base:
        roots = _first(data, _WORKSPACE_KEYS)
        if isinstance(roots, list) and roots and isinstance(roots[0], str):
            base = roots[0]
    tool_cwd = _str(_first(tool_input, _TOOL_CWD_KEYS))
    if tool_cwd and not tool_cwd.startswith("/") and base:
        return base.rstrip("/") + "/" + tool_cwd
    return tool_cwd or base


def _succeeded(data: dict[str, Any]) -> bool:
    name = _str(_first(data, _EVENT_NAME_KEYS))
    if "failure" in name.lower():
        return False
    result = _first(data, _RESULT_KEYS)
    if not isinstance(result, dict):
        return True
    code = _first(result, ("exit_code", "exitCode", "returncode"))
    if isinstance(code, int) and not isinstance(code, bool) and code != 0:
        return False
    if result.get("success") is False or result.get("error"):
        return False
    result_type = result.get("resultType")
    return not (isinstance(result_type, str) and result_type != "success")


def _stop_hook_active(data: dict[str, Any]) -> bool:
    if any(data.get(key) is True for key in _STOP_ACTIVE_KEYS):
        return True
    # Cursor reports how many stop loops it already ran instead.
    loop_count = data.get("loop_count")
    return isinstance(loop_count, int) and not isinstance(loop_count, bool) and loop_count > 0


def normalize(harness: str, event: str, payload: Any) -> NormalizedEvent:
    """A harness's hook stdin as a `NormalizedEvent` for `core.decide`."""
    if harness not in HARNESSES:
        raise UsageError(f"unknown harness {harness!r}; expected one of {HARNESSES}")
    if event not in _CLAUDE_EVENT:
        raise UsageError(f"unknown event {event!r}; expected one of {tuple(_CLAUDE_EVENT)}")
    data = payload if isinstance(payload, dict) else {}
    tool_name = _str(_first(data, _TOOL_NAME_KEYS))
    tool_kind = TOOL_KINDS.get(tool_name, "other") if tool_name else "other"
    tool_input = _tool_input(data)
    succeeded = _succeeded(data)

    # `core` reads Claude-named keys out of `raw`; give it those, keep the rest.
    raw = dict(data)
    raw["harness"] = harness
    raw["harness_event_name"] = _str(_first(data, _EVENT_NAME_KEYS))
    claude_event = _CLAUDE_EVENT[event]
    raw["hook_event_name"] = (
        "PostToolUseFailure" if event == "post-tool" and not succeeded else claude_event
    )
    raw["stop_hook_active"] = _stop_hook_active(data)
    transcript = _first(data, _TRANSCRIPT_KEYS)
    if isinstance(transcript, str):
        raw["agent_transcript_path"] = transcript

    return NormalizedEvent(
        event=event,
        tool_kind=tool_kind,
        command=_command(tool_input) if tool_kind == "shell" else "",
        paths=_paths(tool_input) if tool_kind in ("edit", "write", "read") else [],
        cwd=_cwd(data, tool_input),
        succeeded=succeeded,
        raw=raw,
    )


def _deny(harness: str, reason: str) -> dict[str, Any]:
    nested = {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }
    if harness == "copilot":
        # The docs list the flat fields; whether PascalCase payloads also read
        # Claude's nested shape is undocumented, so emit both.
        return {
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
            "hookSpecificOutput": nested,
        }
    if harness == "cursor":
        return {"permission": "deny", "user_message": reason, "agent_message": reason}
    if harness == "codex":
        return {"hookSpecificOutput": nested}
    return {"decision": "deny", "reason": reason}  # gemini, antigravity


def _block(harness: str, reason: str) -> dict[str, Any]:
    if harness == "cursor":
        return {"followup_message": reason}
    if harness == "gemini":
        return {"decision": "deny", "reason": reason}  # AfterAgent deny forces a retry
    if harness == "antigravity":
        return {"decision": "continue", "reason": reason}  # Stop: keep the agent going
    return {"decision": "block", "reason": reason}  # copilot, codex


def render(harness: str, event: str, decision: Decision) -> dict[str, Any]:
    """The JSON `harness` reads for `decision` on `event`.

    An allow carries no decision, so the harness's own permission flow still
    applies (an explicit allow would auto-approve in some harnesses), except
    Antigravity PreToolUse, which requires the `decision` field.
    """
    if harness not in HARNESSES:
        raise UsageError(f"unknown harness {harness!r}; expected one of {HARNESSES}")
    if decision.action == "allow":
        if harness == "antigravity" and event == "pre-tool":
            return {"decision": "allow"}
        return {}
    if event == "stop":
        return _block(harness, decision.reason)
    return _deny(harness, decision.reason)
