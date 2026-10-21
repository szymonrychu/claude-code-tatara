"""OpenAI Codex target: `.codex/agents/*.toml`, `.codex/hooks.json`, `.codex/config.toml`.

AGENTS.md is read natively (walked from the git root). Codex has no path-scoped rules, so the
`workbench:path-rules` block is added to AGENTS.md by `harness.agents_md` (setup runs it for
codex). Hooks are on by default in Codex, so no feature flag is written.
"""

from __future__ import annotations

import json
import os
import re

from harness.emit import Emitter
from harness.models import model_for
from harness.skills_emit import _rewrite

# Only the guards that exist in the adapter and make sense before a tool or at a subagent stop.
# verify-recorder, bash-output-filter and format-file are Claude-only and are not emitted.
_EVENTS = {"PreToolUse": "pre-tool", "SubagentStop": "stop"}
_HOOKS = {"guard-bash", "protect-files", "subagent-commit-guard"}
_LEFTOVER_ROOT = re.compile(r"\$\{?CLAUDE_PLUGIN_ROOT\}?")
_MATCHERS = {
    "Bash": "Bash",
    "Edit|MultiEdit|NotebookEdit|Write": "apply_patch|Edit|MultiEdit|NotebookEdit|Write",
}
_BARE_KEY = re.compile(r"[A-Za-z0-9_-]+")
_ESCAPES = {
    '"': '\\"',
    "\\": "\\\\",
    "\n": "\\n",
    "\t": "\\t",
    "\r": "\\r",
    "\b": "\\b",
    "\f": "\\f",
}


def toml_str(s: str) -> str:
    """A TOML basic string with every special and control character escaped."""
    out = []
    for ch in s:
        if ch in _ESCAPES:
            out.append(_ESCAPES[ch])
        elif ord(ch) < 0x20 or ord(ch) == 0x7F:
            out.append(f"\\u{ord(ch):04X}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def toml_multiline(s: str) -> str:
    """A multi-line literal string when the text allows it, else a multi-line basic string."""
    literal_ok = (
        "'''" not in s
        and not s.endswith("'")
        and not any((ord(c) < 0x20 and c not in "\n\t") or ord(c) == 0x7F for c in s)
    )
    if literal_ok:
        return "'''\n" + s + "'''"
    body = "\n".join(toml_str(line)[1:-1] for line in s.split("\n"))
    return '"""\n' + body + '"""'


def toml_key(k: str) -> str:
    return k if _BARE_KEY.fullmatch(k) else toml_str(k)


def toml_value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(toml_value(x) for x in v) + "]"
    return toml_str(str(v))


def _mcp_tables(servers: dict) -> str:
    out = []
    for name, spec in servers.items():
        head = f"[mcp_servers.{toml_key(name)}]"
        lines = [head]
        headers = dict(spec.get("headers") or {})
        if spec.get("url"):
            lines.append(f"url = {toml_value(spec['url'])}")
            auth = headers.get("Authorization", "")
            m = re.fullmatch(r"Bearer \$\{(\w+)\}", auth)
            if m:
                lines.append(f"bearer_token_env_var = {toml_value(m.group(1))}")
                del headers["Authorization"]
        else:
            lines.append(f"command = {toml_value(spec.get('command', ''))}")
            if spec.get("args"):
                lines.append(f"args = {toml_value(spec['args'])}")
        out.append("\n".join(lines))
        for sub, table in (("http_headers", headers), ("env", spec.get("env") or {})):
            if table:
                rows = [f"{toml_key(k)} = {toml_value(v)}" for k, v in table.items()]
                out.append("\n".join([f"[mcp_servers.{toml_key(name)}.{sub}]", *rows]))
    return "\n\n".join(out) + "\n"


class CodexEmitter(Emitter):
    target = "codex"

    def render(self, sources) -> dict[str, str]:
        out: dict[str, str] = {}
        plugin_names = ["workbench", *(p.name for p in sources.plugins)]
        groups: dict[tuple[str, str], list[str]] = {}
        for plugin in sources.plugins:
            prefix = os.path.relpath(plugin.root, sources.root).replace(os.sep, "/")
            for agent in plugin.agents:
                body = _rewrite(agent.body, prefix, plugin_names).strip("\n") + "\n"
                if _LEFTOVER_ROOT.search(body):
                    raise ValueError(f"agent {agent.name}: unresolved CLAUDE_PLUGIN_ROOT")
                desc = _rewrite(agent.description, prefix, plugin_names)
                lines = [
                    f"name = {toml_str(agent.name)}",
                    f"description = {toml_str(desc)}",
                ]
                model = model_for("codex", agent.model, sources.harness.models)
                if model:
                    lines.append(f"model = {toml_str(model)}")
                lines.append(f"developer_instructions = {toml_multiline(body)}")
                out[f".codex/agents/{agent.name}.toml"] = "\n".join(lines) + "\n"
            adapter = f"{prefix}/hooks/adapter.py"
            for reg in plugin.hooks:
                if reg.event not in _EVENTS or reg.hook.replace("_", "-") not in _HOOKS:
                    continue
                hook = reg.hook.replace("_", "-")
                matcher = _MATCHERS.get(reg.matcher, reg.matcher)
                cmd = (
                    f"python3 {adapter} --harness codex --event {_EVENTS[reg.event]} --hook {hook}"
                )
                cmds = groups.setdefault((reg.event, matcher), [])
                if cmd not in cmds:
                    cmds.append(cmd)
        if groups:
            hooks: dict[str, list] = {}
            for (event, matcher), cmds in groups.items():
                entry: dict = {"hooks": [{"type": "command", "command": c} for c in cmds]}
                if matcher:
                    entry = {"matcher": matcher, **entry}
                hooks.setdefault(event, []).append(entry)
            out[".codex/hooks.json"] = json.dumps({"hooks": hooks}, indent=2) + "\n"
        servers = (sources.mcp or {}).get("mcpServers")
        if servers:
            out[".codex/config.toml"] = _mcp_tables(servers)
        return out
