"""GitHub Copilot target: instructions, custom agents, hooks and VS Code MCP (design D4-D6).

AGENTS.md, skills (.agents/skills) and the root .mcp.json (Copilot CLI) are read natively, so
they are not written here. The cloud agent's MCP servers are a manual Settings step.
"""

from __future__ import annotations

import json
import os
import re

from ..emit import Emitter
from ..models import model_for
from ..skills_emit import _rewrite

PROMPT_CAP = 30_000
ADAPTER = "plugins/workbench/hooks/adapter.py"
# Claude tool name (lowercase) -> Copilot alias. LSP and ToolSearch have no alias and are dropped.
ALIASES = {
    "bash": "execute",
    "read": "read",
    "edit": "edit",
    "write": "edit",
    "multiedit": "edit",
    "notebookedit": "edit",
    "grep": "search",
    "glob": "search",
    "webfetch": "web",
    "websearch": "web",
    "task": "agent",
    "agent": "agent",
}
DROPPED = frozenset({"lsp", "toolsearch"})
# (Copilot event, matcher, adapter event, hook, timeoutSec): the Claude-only hooks are not emitted.
HOOKS = (
    ("PreToolUse", "Bash", "pre-tool", "guard-bash", 10),
    ("PreToolUse", "Edit|MultiEdit|NotebookEdit|Write", "pre-tool", "protect-files", 10),
    ("SubagentStop", "", "stop", "subagent-commit-guard", 10),
)


def _q(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _tools(tools: tuple[str, ...]) -> list[str]:
    out: list[str] = []
    for t in tools:
        key = t.lower()
        if key in DROPPED:
            continue
        alias = ALIASES.get(key, t)
        if alias not in out:
            out.append(alias)
    return out


class CopilotEmitter(Emitter):
    target = "copilot"

    def render(self, sources) -> dict[str, str]:
        out: dict[str, str] = {}
        for rule in sources.rules:
            apply_to = ",".join(rule.paths) or "**"
            out[f".github/instructions/{rule.name}.instructions.md"] = (
                f"---\napplyTo: {_q(apply_to)}\n---\n{rule.body}"
            )
        out.update(self._agents(sources))
        out[".github/hooks/workbench.json"] = self._hooks()
        if sources.mcp is not None:
            servers = sources.mcp.get("mcpServers", {})
            out[".vscode/mcp.json"] = json.dumps({"servers": servers}, indent=2) + "\n"
        return out

    def _agents(self, sources) -> dict[str, str]:
        out: dict[str, str] = {}
        names = ["workbench", *(p.name for p in sources.plugins)]
        for plugin in sources.plugins:
            prefix = os.path.relpath(plugin.root, sources.root).replace(os.sep, "/")
            for agent in plugin.agents:
                path = f".github/agents/{agent.name}.agent.md"
                if path in out:
                    raise ValueError(f"duplicate agent name {agent.name!r} (plugin {plugin.name})")
                body = _rewrite(agent.body, prefix, names)
                unresolved = re.search(r"\$\{?CLAUDE_\w+\}?", body)
                if unresolved:
                    raise ValueError(
                        f"agent {agent.name!r}: unresolved variable {unresolved.group(0)}"
                    )
                if len(body) > PROMPT_CAP:
                    raise ValueError(
                        f"agent {agent.name!r}: prompt is {len(body)} characters, over the "
                        f"Copilot cap of 30,000"
                    )
                head = [f"name: {_q(agent.name)}", f"description: {_q(agent.description.strip())}"]
                tools = _tools(agent.tools)
                if tools:
                    head.append(f"tools: {json.dumps(tools)}")
                model = model_for(self.target, agent.model, sources.harness.models)
                if model:
                    head.append(f"model: {_q(model)}")
                out[path] = "---\n" + "\n".join(head) + "\n---\n" + body
        return out

    @staticmethod
    def _hooks() -> str:
        hooks: dict[str, list] = {}
        for event, matcher, adapter_event, hook, timeout in HOOKS:
            entry = {"type": "command"}
            if matcher:
                entry["matcher"] = matcher
            entry["bash"] = (
                f"python3 {ADAPTER} --harness copilot --event {adapter_event} --hook {hook}"
            )
            entry["timeoutSec"] = timeout
            hooks.setdefault(event, []).append(entry)
        return json.dumps({"version": 1, "hooks": hooks}, indent=2) + "\n"
