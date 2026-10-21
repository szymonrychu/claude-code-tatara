"""Cursor target: rules (.mdc), agents, hooks.json and mcp.json (design D4, multi-harness.md 2).

AGENTS.md is read natively and skills come from `.agents/skills/`, so neither is written here.
"""

from __future__ import annotations

import json
import os
import re

from ..emit import Emitter
from ..models import model_for
from ..skills_emit import _rewrite

# Hooks registered on non-Claude targets (design: builder check B1); the rest are Claude-only.
_PRE_TOOL = {"guard-bash": "Shell", "protect-files": "Write|Delete"}
_STOP = "subagent-commit-guard"
_ENV = re.compile(r"\$\{(?!env:|workspaceFolder\b)([A-Za-z_]\w*)(?::-[^}]*)?\}")


def _json(data) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def _description(name: str, body: str) -> str:
    m = re.search(r"^#\s+(.+)$", body, re.M)
    return (m.group(1) if m else name).strip()


def _rule(rule) -> str:
    head = f"description: {_description(rule.name, rule.body)}\n"
    if rule.paths:
        head += f"globs: {','.join(rule.paths)}\nalwaysApply: false\n"
    else:
        head += "alwaysApply: true\n"
    return f"---\n{head}---\n{rule.body.lstrip()}"


def _agent(agent, sources, prefix: str, names: list[str]) -> str:
    desc = " ".join(_rewrite(agent.description, prefix, names).split())
    head = f"name: {agent.name}\ndescription: {json.dumps(desc, ensure_ascii=False)}\n"
    model = model_for("cursor", agent.model, sources.harness.models)
    if model:
        head += f"model: {model}\n"
    if agent.tools and not {"Edit", "Write"} & set(agent.tools):
        head += "readonly: true\n"
    body = _rewrite(agent.body, prefix, names)
    if "${CLAUDE_PLUGIN_ROOT}" in body:
        raise ValueError(f"agent {agent.name}: unresolved ${{CLAUDE_PLUGIN_ROOT}} in body")
    return f"---\n{head}---\n{body.lstrip()}"


def _hooks(sources) -> dict:
    pre: list[dict] = []
    stop: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for plugin in sources.plugins:
        prefix = os.path.relpath(plugin.root, sources.root).replace(os.sep, "/")
        for reg in plugin.hooks:
            hook = reg.hook.replace("_", "-")
            if (hook, reg.event) in seen:
                continue
            base = f"python3 {prefix}/hooks/adapter.py --harness cursor"
            if reg.event == "PreToolUse" and hook in _PRE_TOOL:
                seen.add((hook, reg.event))
                pre.append(
                    {
                        "command": f"{base} --event pre-tool --hook {hook}",
                        "type": "command",
                        "timeout": 10,
                        "matcher": _PRE_TOOL[hook],
                        "failClosed": True,
                    }
                )
            elif reg.event == "SubagentStop" and hook == _STOP:
                seen.add((hook, reg.event))
                cmd = f"{base} --event stop --hook {hook}"
                stop.append({"command": cmd, "type": "command", "timeout": 15})
    hooks = {k: v for k, v in (("preToolUse", pre), ("subagentStop", stop)) if v}
    return {"version": 1, "hooks": hooks} if hooks else {}


def _env(node):
    if isinstance(node, str):
        return _ENV.sub(r"${env:\1}", node.replace("${CLAUDE_PROJECT_DIR}", "${workspaceFolder}"))
    if isinstance(node, list):
        return [_env(x) for x in node]
    if isinstance(node, dict):
        return {k: _env(v) for k, v in node.items()}
    return node


class CursorEmitter(Emitter):
    target = "cursor"

    def render(self, sources) -> dict[str, str]:
        out: dict[str, str] = {}
        for rule in sources.rules:
            out[f".cursor/rules/{rule.name}.mdc"] = _rule(rule)
        names = ["workbench", *(p.name for p in sources.plugins)]
        for plugin in sources.plugins:
            prefix = os.path.relpath(plugin.root, sources.root).replace(os.sep, "/")
            for agent in plugin.agents:
                out[f".cursor/agents/{agent.name}.md"] = _agent(agent, sources, prefix, names)
        hooks = _hooks(sources)
        if hooks:
            out[".cursor/hooks.json"] = _json(hooks)
        if sources.mcp is not None:
            out[".cursor/mcp.json"] = _json(_env(sources.mcp))
        return out
