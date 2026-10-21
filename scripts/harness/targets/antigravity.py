"""Antigravity target: `.agents/rules`, `.agents/agents`, `.agents/hooks.json`, MCP config.

AGENTS.md is read natively and `.agents/skills/` is written by the shared skills emitter, so
this target writes neither (design D4, multi-harness.md 4B).
"""

from __future__ import annotations

import json
import os
import re

from harness.agents_md import sync_text
from harness.emit import Emitter
from harness.models import model_for
from harness.skills_emit import _rewrite

_LEFTOVER_ROOT = re.compile(r"\$\{?CLAUDE_PLUGIN_ROOT\}?")  # any remaining plugin-root reference
AGENTS_MD_CAP = 24_000
TRIGGERS = frozenset({"always_on", "glob", "manual", "model_decision"})
# Claude hook registrations that exist for Antigravity: (hook, event, adapter event, matcher).
PRE_MATCHERS = {
    "guard-bash": "run_command",
    "protect-files": "write_to_file|replace_file_content|multi_replace_file_content",
}
STOP_HOOK = "subagent-commit-guard"
TIMEOUTS = {"guard-bash": 10, "protect-files": 10, STOP_HOOK: 15}  # seconds


class AntigravityError(ValueError):
    """Generation cannot produce a file Antigravity would accept."""


def check_trigger(rule: str, trigger: str) -> str:
    """A rule without a valid trigger is silently dropped by Antigravity, so fail instead."""
    if trigger not in TRIGGERS:
        raise AntigravityError(
            f"rule {rule!r}: unknown trigger {trigger!r} (valid: {', '.join(sorted(TRIGGERS))})"
        )
    return trigger


def check_agents_md(text: str) -> None:
    """Fail when AGENTS.md, as it will be on disk after the rules block is synced, is too big."""
    size = len(text.encode("utf-8"))
    if size > AGENTS_MD_CAP:
        raise AntigravityError(
            f"AGENTS.md is {size:,} bytes; Antigravity reads at most {AGENTS_MD_CAP:,} bytes"
        )


def _q(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _rule(rule) -> str:
    if rule.paths:
        head = f"trigger: {check_trigger(rule.name, 'glob')}\nglobs: {_q(', '.join(rule.paths))}\n"
    else:
        head = f"trigger: {check_trigger(rule.name, 'always_on')}\n"
    return f"---\n{head}---\n{rule.body.lstrip(chr(10))}"


def _command(prefix: str, event: str, hook: str) -> str:
    return f"python3 {prefix}/hooks/adapter.py --harness antigravity --event {event} --hook {hook}"


def _hooks(sources) -> dict | None:
    pre: dict[str, list] = {m: [] for m in PRE_MATCHERS.values()}
    stop: list = []
    for plugin in sources.plugins:
        prefix = os.path.relpath(plugin.root, sources.root).replace(os.sep, "/")
        for reg in plugin.hooks:
            hook = reg.hook.replace("_", "-")
            if hook in PRE_MATCHERS and reg.event == "PreToolUse":
                event, bucket = "pre-tool", pre[PRE_MATCHERS[hook]]
            elif hook == STOP_HOOK and reg.event in ("SubagentStop", "Stop"):
                event, bucket = "stop", stop
            else:
                continue
            entry = {"type": "command", "command": _command(prefix, event, hook)}
            bucket.append({**entry, "timeout": TIMEOUTS[hook]})
    hooks: dict[str, list] = {}
    groups = [{"matcher": m, "hooks": h} for m, h in pre.items() if h]
    if groups:
        hooks["PreToolUse"] = groups
    if stop:
        hooks["Stop"] = [{"hooks": stop}]
    return {"hooks": hooks} if hooks else None


def _mcp(mcp: dict) -> dict:
    servers = {}
    for name, cfg in mcp.get("mcpServers", {}).items():
        cfg = dict(cfg)
        cfg.pop("type", None)
        for key in ("url", "httpUrl"):
            if key in cfg:
                cfg["serverUrl"] = cfg.pop(key)
        servers[name] = cfg
    return {"mcpServers": servers}


class AntigravityEmitter(Emitter):
    target = "antigravity"

    def render(self, sources) -> dict[str, str]:
        check_agents_md(sync_text(sources.root, sources.agents_md, False))
        out: dict[str, str] = {}
        for rule in sources.rules:
            out[f".agents/rules/{rule.name}.md"] = _rule(rule)
        names = ["workbench", *(p.name for p in sources.plugins)]
        owner: dict[str, str] = {}
        for plugin in sources.plugins:
            prefix = os.path.relpath(plugin.root, sources.root).replace(os.sep, "/")
            for agent in plugin.agents:
                if agent.name in owner:
                    raise AntigravityError(
                        f"duplicate agent {agent.name!r} in plugins {owner[agent.name]} "
                        f"and {plugin.name}"
                    )
                owner[agent.name] = plugin.name
                model = model_for("antigravity", agent.model, sources.harness.models)
                head = f"name: {agent.name}\ndescription: {_q(agent.description.strip())}\n"
                if model:
                    head += f"model: {model}\n"
                body = _rewrite(agent.body, prefix, names)
                if _LEFTOVER_ROOT.search(body):
                    raise AntigravityError(f"agent {agent.name!r}: unresolved CLAUDE_PLUGIN_ROOT")
                out[f".agents/agents/{agent.name}.md"] = f"---\n{head}---\n{body}"
        hooks = _hooks(sources)
        if hooks:
            out[".agents/hooks.json"] = json.dumps(hooks, indent=2) + "\n"
        if sources.mcp is not None:
            out[".agents/mcp_config.json"] = json.dumps(_mcp(sources.mcp), indent=2) + "\n"
        return out
