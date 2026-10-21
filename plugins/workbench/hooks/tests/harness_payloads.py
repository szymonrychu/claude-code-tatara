"""Example hook payloads per harness, as each harness documents them.

Sources are `docs/research/multi-harness.md` sections 1e (Copilot), 2e (Cursor),
3e (Codex), 4A e (Gemini CLI) and 4B e (Antigravity). Where a doc names the
top-level fields but not the tool-argument keys, the example uses the keys the
harness's own tool schema uses and says so; the adapter accepts every alias
listed in `lib/harness_io.py`, so a different spelling still normalizes.

Each harness module-level entry is a `Harness` with five builders:
`shell(command, cwd)`, `edit(path, cwd)`, `write(path, cwd)`,
`post_shell(command, cwd, failed)` and `stop(cwd)`. The `harness` field is the
`--harness` value the adapter is called with; `copilot-native` is the Copilot CLI
camelCase payload and runs as `--harness copilot` too.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

Payload = dict[str, Any]


@dataclass(frozen=True)
class Harness:
    name: str
    harness: str
    shell: Callable[[str, str], Payload]
    edit: Callable[[str, str], Payload]
    write: Callable[[str, str], Payload]
    post_shell: Callable[[str, str, bool], Payload]
    stop: Callable[[str], Payload]


# --- GitHub Copilot, PascalCase keys (VS Code-compatible payload) -----------
# 1e: PascalCase `PreToolUse` selects snake_case `tool_name`/`tool_input` with
# Claude tool names (`bash` as `Bash`, `create` as `Write`, `edit` as `Edit`).
# VS Code stdin: `timestamp`, `cwd`, `session_id`, `hook_event_name`,
# `transcript_path`, plus `tool_name`, `tool_input`, `tool_use_id`.


def _copilot_common(event: str, cwd: str) -> Payload:
    return {
        "timestamp": "2026-10-20T12:00:00.000Z",
        "cwd": cwd,
        "session_id": "sess-1",
        "hook_event_name": event,
        "transcript_path": "/tmp/copilot-transcript.json",
    }


COPILOT = Harness(
    name="copilot",
    harness="copilot",
    shell=lambda command, cwd: {
        **_copilot_common("PreToolUse", cwd),
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "tool_use_id": "tu-1",
    },
    edit=lambda path, cwd: {
        **_copilot_common("PreToolUse", cwd),
        "tool_name": "Edit",
        "tool_input": {"file_path": path, "old_string": "a", "new_string": "b"},
        "tool_use_id": "tu-2",
    },
    write=lambda path, cwd: {
        **_copilot_common("PreToolUse", cwd),
        "tool_name": "Write",
        "tool_input": {"file_path": path, "content": "x"},
        "tool_use_id": "tu-3",
    },
    post_shell=lambda command, cwd, failed: {
        **_copilot_common("PostToolUseFailure" if failed else "PostToolUse", cwd),
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "tool_use_id": "tu-4",
    },
    stop=lambda cwd: {**_copilot_common("SubagentStop", cwd), "stop_hook_active": False},
)


# --- GitHub Copilot CLI, native camelCase events ------------------------------
# 1e: camelCase `preToolUse` / `postToolUse` / `postToolUseFailure` /
# `subagentStop`. The CLI payload carries `timestamp`, `cwd`, `toolName` (the
# native names `bash`, `edit`, `create`, `view`) and `toolArgs`, a JSON string;
# post-tool adds `toolResult.resultType`. Edit/create take `path`.


def _copilot_native(tool: str, args: Payload, cwd: str) -> Payload:
    return {
        "timestamp": 1792497600000,
        "cwd": cwd,
        "toolName": tool,
        "toolArgs": json.dumps(args),
    }


COPILOT_NATIVE = Harness(
    name="copilot-native",
    harness="copilot",
    shell=lambda command, cwd: _copilot_native("bash", {"command": command}, cwd),
    edit=lambda path, cwd: _copilot_native(
        "edit", {"path": path, "old_str": "a", "new_str": "b"}, cwd
    ),
    write=lambda path, cwd: _copilot_native("create", {"path": path, "file_text": "x"}, cwd),
    post_shell=lambda command, cwd, failed: {
        **_copilot_native("bash", {"command": command}, cwd),
        "toolResult": {
            "resultType": "failure" if failed else "success",
            "textResultForLlm": "",
        },
    },
    stop=lambda cwd: {"timestamp": 1792497600000, "cwd": cwd, "stopHookActive": False},
)


# --- Cursor, native `.cursor/hooks.json` --------------------------------------
# 2e: preToolUse stdin `tool_name` (`Shell`, `Read`, `Write`, ...), `tool_input`
# (Shell: `command`, `working_directory`); common fields `conversation_id`,
# `generation_id`, `hook_event_name`, `workspace_roots`; stop/subagentStop carry
# `status` and `loop_count` and no tool fields. Write takes `file_path` (assumed:
# the docs name the tool, not its argument keys). Cursor maps Claude `Edit` to
# `Write`, so an edit arrives as `Write` too.


def _cursor_common(event: str, cwd: str) -> Payload:
    return {
        "conversation_id": "conv-1",
        "generation_id": "gen-1",
        "hook_event_name": event,
        "workspace_roots": [cwd],
        "cursor_version": "2.6.11",
    }


CURSOR = Harness(
    name="cursor",
    harness="cursor",
    shell=lambda command, cwd: {
        **_cursor_common("preToolUse", cwd),
        "tool_name": "Shell",
        "tool_input": {"command": command, "working_directory": cwd},
        "tool_use_id": "tu-1",
    },
    edit=lambda path, cwd: {
        **_cursor_common("preToolUse", cwd),
        "tool_name": "Write",
        "tool_input": {"file_path": path, "old_string": "a", "new_string": "b"},
        "tool_use_id": "tu-2",
    },
    write=lambda path, cwd: {
        **_cursor_common("preToolUse", cwd),
        "tool_name": "Write",
        "tool_input": {"file_path": path, "content": "x"},
        "tool_use_id": "tu-3",
    },
    post_shell=lambda command, cwd, failed: {
        **_cursor_common("postToolUseFailure" if failed else "postToolUse", cwd),
        "tool_name": "Shell",
        "tool_input": {"command": command, "working_directory": cwd},
        "tool_output": "",
    },
    stop=lambda cwd: {
        **_cursor_common("subagentStop", cwd),
        "status": "completed",
        "loop_count": 0,
    },
)


# --- OpenAI Codex CLI, `.codex/hooks.json` -------------------------------------
# 3e: stdin `session_id`, `transcript_path`, `cwd`, `hook_event_name`, `model`,
# `turn_id`, `tool_name`, `tool_use_id`, `tool_input`; shell is `Bash` with
# `tool_input.command`; Edit and Write arrive as `apply_patch` with the patch text
# in `tool_input.command` and no `file_path`.


def _codex_common(event: str, cwd: str) -> Payload:
    return {
        "session_id": "sess-1",
        "transcript_path": "/tmp/codex-rollout.jsonl",
        "cwd": cwd,
        "hook_event_name": event,
        "model": "gpt-5-codex",
        "turn_id": "turn-1",
    }


def codex_patch(*body: str) -> str:
    """A Codex `apply_patch` envelope around `body` lines."""
    return "\n".join(["*** Begin Patch", *body, "*** End Patch"]) + "\n"


def codex_apply_patch(patch: str, cwd: str) -> Payload:
    return {
        **_codex_common("PreToolUse", cwd),
        "tool_name": "apply_patch",
        "tool_use_id": "tu-p",
        "tool_input": {"command": patch},
    }


CODEX = Harness(
    name="codex",
    harness="codex",
    shell=lambda command, cwd: {
        **_codex_common("PreToolUse", cwd),
        "tool_name": "Bash",
        "tool_use_id": "tu-1",
        "tool_input": {"command": command},
    },
    edit=lambda path, cwd: codex_apply_patch(
        codex_patch(f"*** Update File: {path}", "@@", "-a", "+b"), cwd
    ),
    write=lambda path, cwd: codex_apply_patch(codex_patch(f"*** Add File: {path}", "+x"), cwd),
    post_shell=lambda command, cwd, failed: {
        **_codex_common("PostToolUse", cwd),
        "tool_name": "Bash",
        "tool_use_id": "tu-4",
        "tool_input": {"command": command},
        "tool_response": {"exit_code": 1 if failed else 0, "output": ""},
    },
    stop=lambda cwd: {
        **_codex_common("SubagentStop", cwd),
        "stop_hook_active": False,
        "last_assistant_message": "done",
    },
)


# --- Gemini CLI, `.gemini/settings.json` ---------------------------------------
# 4A e: stdin `session_id`, `transcript_path`, `cwd`, `hook_event_name`,
# `timestamp`; BeforeTool adds `tool_name`, `tool_input`, `mcp_context`; tool
# names `run_shell_command`, `write_file`, `replace`; AfterAgent is the Stop
# fallback. `file_path` is the write_file/replace argument key.


def _gemini_common(event: str, cwd: str) -> Payload:
    return {
        "session_id": "sess-1",
        "transcript_path": "/tmp/gemini-chat.json",
        "cwd": cwd,
        "hook_event_name": event,
        "timestamp": "2026-10-20T12:00:00.000Z",
    }


GEMINI = Harness(
    name="gemini",
    harness="gemini",
    shell=lambda command, cwd: {
        **_gemini_common("BeforeTool", cwd),
        "tool_name": "run_shell_command",
        "tool_input": {"command": command, "description": "run it"},
        "mcp_context": None,
    },
    edit=lambda path, cwd: {
        **_gemini_common("BeforeTool", cwd),
        "tool_name": "replace",
        "tool_input": {"file_path": path, "old_string": "a", "new_string": "b"},
        "mcp_context": None,
    },
    write=lambda path, cwd: {
        **_gemini_common("BeforeTool", cwd),
        "tool_name": "write_file",
        "tool_input": {"file_path": path, "content": "x"},
        "mcp_context": None,
    },
    post_shell=lambda command, cwd, failed: {
        **_gemini_common("AfterTool", cwd),
        "tool_name": "run_shell_command",
        "tool_input": {"command": command},
        "tool_response": {
            "llmContent": "",
            "returnDisplay": "",
            **({"error": {"message": "exit code 1"}} if failed else {}),
        },
    },
    stop=lambda cwd: {
        **_gemini_common("AfterAgent", cwd),
        "prompt": "do it",
        "prompt_response": "done",
        "stop_hook_active": False,
    },
)


# --- Antigravity, `.agents/hooks.json` -----------------------------------------
# 4B e: camelCase stdin (`conversationId`, `workspacePaths`, `transcriptPath`,
# `artifactDirectoryPath`, `modelName`); tool names `run_command`,
# `write_to_file`, `replace_file_content`, `multi_replace_file_content`. The
# tool-argument keys (`CommandLine`, `Cwd`, `TargetFile`) are the Antigravity
# tool schema's own; the hooks page does not list them.


def _antigravity_common(event: str, cwd: str) -> Payload:
    return {
        "hookEventName": event,
        "conversationId": "conv-1",
        "workspacePaths": [cwd],
        "transcriptPath": "/tmp/agy-transcript.jsonl",
        "artifactDirectoryPath": "/tmp/agy-artifacts",
        "modelName": "gemini-3-pro",
    }


ANTIGRAVITY = Harness(
    name="antigravity",
    harness="antigravity",
    shell=lambda command, cwd: {
        **_antigravity_common("PreToolUse", cwd),
        "toolName": "run_command",
        "toolInput": {"CommandLine": command, "Cwd": cwd},
    },
    edit=lambda path, cwd: {
        **_antigravity_common("PreToolUse", cwd),
        "toolName": "replace_file_content",
        "toolInput": {"TargetFile": path, "ReplacementContent": "b"},
    },
    write=lambda path, cwd: {
        **_antigravity_common("PreToolUse", cwd),
        "toolName": "write_to_file",
        "toolInput": {"TargetFile": path, "CodeContent": "x"},
    },
    post_shell=lambda command, cwd, failed: {
        **_antigravity_common("PostToolUse", cwd),
        "toolName": "run_command",
        "toolInput": {"CommandLine": command, "Cwd": cwd},
        "toolResponse": {"exitCode": 1 if failed else 0},
    },
    stop=lambda cwd: _antigravity_common("Stop", cwd),
)


ALL = (COPILOT, COPILOT_NATIVE, CURSOR, CODEX, GEMINI, ANTIGRAVITY)
