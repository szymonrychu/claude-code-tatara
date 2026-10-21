"""Gemini CLI target (design D3-D6): .gemini/settings.json plus .gemini/agents/<name>.md.

Skills come from the shared `.agents/skills/` output (Gemini prefers it over `.gemini/skills`);
the path-rules block of AGENTS.md is written by harness-setup for this target.
"""

from __future__ import annotations

import json
import os
import re

from harness.emit import Emitter
from harness.models import model_for
from harness.skills_emit import _rewrite

# hook name -> (Gemini event, matcher, adapter event, timeout in milliseconds). Only the guards
# with a Gemini equivalent are registered; verify-recorder, bash-output-filter and format-file
# are Claude-only.
EVENT = {"PreToolUse": "BeforeTool", "SubagentStop": "AfterAgent"}
ADAPTER_EVENT = {"PreToolUse": "pre-tool", "SubagentStop": "stop"}
MATCHER = {"Bash": "run_shell_command", "Edit|MultiEdit|NotebookEdit|Write": "write_file|replace"}
TIMEOUT_MS = {"guard-bash": 10000, "protect-files": 10000, "subagent-commit-guard": 15000}
_UNRESOLVED = re.compile(r"\$\{?CLAUDE_\w+\}?")


def _json(data: dict) -> str:
    return json.dumps(data, indent=2) + "\n"


def _adapter(sources) -> str:
    core = next((p for p in sources.plugins if p.name == "workbench"), None)
    plugin = core or next((p for p in sources.plugins if p.hooks), None)
    root = os.path.relpath(plugin.root, sources.root).replace(os.sep, "/") if plugin else ""
    return f"{root}/hooks/adapter.py" if root and root != "." else "hooks/adapter.py"


def _hooks(sources) -> dict:
    adapter = _adapter(sources)
    hooks: dict[str, list] = {}
    seen: set[tuple] = set()
    for plugin in sources.plugins:
        for reg in plugin.hooks:
            if reg.hook not in TIMEOUT_MS or reg.event not in EVENT:
                continue
            matcher = MATCHER.get(reg.matcher, reg.matcher) if reg.matcher else ""
            if (reg.event, matcher, reg.hook) in seen:
                continue
            seen.add((reg.event, matcher, reg.hook))
            command = (
                f"python3 {adapter} --harness gemini --event {ADAPTER_EVENT[reg.event]}"
                f" --hook {reg.hook}"
            )
            entry = {
                "name": reg.hook,
                "type": "command",
                "command": command,
                "timeout": TIMEOUT_MS[reg.hook],
            }
            groups = hooks.setdefault(EVENT[reg.event], [])
            group = next((g for g in groups if g.get("matcher", "") == matcher), None)
            if group is None:
                group = {"matcher": matcher, "hooks": []} if matcher else {"hooks": []}
                groups.append(group)
            group["hooks"].append(entry)
    return hooks


def _server(spec: dict) -> dict:
    """Claude .mcp.json server -> Gemini mcpServers entry (httpUrl for streamable HTTP)."""
    if "url" not in spec:
        return {k: v for k, v in spec.items() if k != "type"}
    out = {"httpUrl" if spec.get("type", "http") == "http" else "url": spec["url"]}
    out.update({k: v for k, v in spec.items() if k in ("headers", "timeout")})
    return out


def _agent(sources, plugin, agent) -> str:
    prefix = os.path.relpath(plugin.root, sources.root).replace(os.sep, "/")
    names = ["workbench", *(p.name for p in sources.plugins)]
    body = _rewrite(agent.body, prefix, names)
    left = _UNRESOLVED.search(body)
    if left:
        raise ValueError(
            f"agent {agent.name!r} in plugin {plugin.name}: unresolved variable {left.group(0)}"
        )
    head = [f"name: {agent.name}", f"description: {json.dumps(agent.description.strip())}"]
    model = model_for("gemini", agent.model, sources.harness.models)
    if model:
        head.append(f"model: {model}")
    return "---\n" + "\n".join(head) + "\n---\n" + body


class GeminiEmitter(Emitter):
    target = "gemini"

    def render(self, sources) -> dict[str, str]:
        settings: dict = {"context": {"fileName": ["AGENTS.md", "GEMINI.md"]}}
        hooks = _hooks(sources)
        if hooks:
            settings["hooks"] = hooks
        if sources.mcp is not None:
            settings["mcpServers"] = {
                n: _server(s) for n, s in sources.mcp.get("mcpServers", {}).items()
            }
        out = {".gemini/settings.json": _json(settings)}
        for plugin in sources.plugins:
            for agent in plugin.agents:
                path = f".gemini/agents/{agent.name}.md"
                if path in out:
                    raise ValueError(f"duplicate agent {agent.name!r} (plugin {plugin.name})")
                out[path] = _agent(sources, plugin, agent)
        return out
