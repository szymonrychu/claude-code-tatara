"""The typed input model every harness emitter reads (design D4).

Stdlib only. Reads AGENTS.md, .claude/rules, .mcp.json, the `harness` config key and every
plugin of the root marketplace that .claude/settings.json enables.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shlex
from dataclasses import dataclass, field
from pathlib import Path

_CORE = Path(__file__).resolve().parents[2] / "plugins/workbench/scripts/lib/workbench.py"


class FrontmatterError(ValueError):
    """Unsupported or malformed frontmatter; the message starts `<file>:<line>:`."""


@dataclass(frozen=True)
class Rule:
    name: str
    paths: tuple[str, ...]
    body: str


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    frontmatter: dict
    body: str
    dir: Path


@dataclass(frozen=True)
class Agent:
    name: str
    description: str
    model: str | None
    tools: tuple[str, ...]
    body: str


@dataclass(frozen=True)
class HookReg:
    event: str
    matcher: str
    hook: str


@dataclass(frozen=True)
class PluginSource:
    name: str
    root: Path
    skills: tuple[Skill, ...] = ()
    agents: tuple[Agent, ...] = ()
    hooks: tuple[HookReg, ...] = ()


@dataclass(frozen=True)
class HarnessConfig:
    targets: tuple[str, ...] = ()
    models: dict = field(default_factory=dict)
    active: str = ""


@dataclass(frozen=True)
class Sources:
    root: Path
    agents_md: str
    agents_blocks: dict[str, str]
    rules: tuple[Rule, ...]
    mcp: dict | None
    harness: HarnessConfig
    plugins: tuple[PluginSource, ...]


# ---- frontmatter ----------------------------------------------------------------------------

_KEY = re.compile(r"^([A-Za-z_][\w-]*):(?:\s+(.*)|\s*)$")


def _scalar(raw: str, where) -> object:
    raw = raw.strip()
    if not raw:
        raise where("empty list item")
    if raw[0] in "\"'":
        q = raw[0]
        if len(raw) < 2 or raw[-1] != q:
            raise where("unterminated quoted string")
        inner = raw[1:-1]
        if q == '"':
            try:
                return json.loads(raw)
            except ValueError:
                return inner.replace('\\"', '"')
        return inner.replace("''", "'")
    if raw[:1] in "{&*!|>%@`" or raw.startswith("- "):
        raise where(f"unsupported value {raw!r}")
    if raw in ("true", "false"):
        return raw == "true"
    return raw


def _inline_list(raw: str, where) -> list:
    if not raw.endswith("]"):
        raise where("unterminated inline list")
    inner = raw[1:-1].strip()
    if not inner:
        return []
    out, cur, quote = [], [], ""
    for ch in [*inner, ","]:
        if quote:
            quote = "" if ch == quote else quote
        elif ch in "\"'" and not "".join(cur).strip():
            quote = ch
        elif ch == ",":
            item = "".join(cur).strip()
            if not item:
                raise where("empty list item")
            out.append(_scalar(item, where))
            cur = []
            continue
        cur.append(ch)
    if quote:
        raise where("unterminated quoted string in inline list")
    return out


def parse_frontmatter(text: str, path: str) -> tuple[dict, str]:
    """Parse the restricted frontmatter; return (mapping, body). No frontmatter gives ({}, text)."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        return {}, text
    fm: dict = {}
    i = 1
    n = len(lines)

    def err(no: int):
        return lambda msg: FrontmatterError(f"{path}:{no}: {msg}")

    while True:
        if i >= n:
            raise FrontmatterError(f"{path}:1: frontmatter is not closed with ---")
        line = lines[i].rstrip("\r\n")
        no = i + 1
        if line == "---":
            i += 1
            break
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        m = _KEY.match(line)
        if not m:
            raise FrontmatterError(f"{path}:{no}: expected `key: value`, got {line!r}")
        key, val = m.group(1), (m.group(2) or "").strip()
        i += 1
        if val[:1] in ("|", ">"):
            style, chomp = val[0], val[1:]
            if chomp not in ("", "-", "+"):
                raise FrontmatterError(f"{path}:{no}: unsupported block scalar header {val!r}")
            block: list[str] = []
            while i < n and (not lines[i].strip() or lines[i][:1] in " \t"):
                block.append(lines[i].rstrip("\r\n"))
                i += 1
            while block and not block[-1].strip():
                block.pop()
            ind = min((len(b) - len(b.lstrip()) for b in block if b.strip()), default=0)
            body = [b[ind:] if b.strip() else "" for b in block]
            if style == "|":
                s = "\n".join(body)
            else:
                paras, cur = [], []
                for b in body:
                    if b:
                        cur.append(b)
                    elif cur:
                        paras.append(" ".join(cur))
                        cur = []
                if cur:
                    paras.append(" ".join(cur))
                s = "\n".join(paras)
            fm[key] = s + ("\n" if chomp == "+" else "")
        elif val == "":
            items = []
            while i < n and re.match(r"^\s+-(\s|$)", lines[i]):
                items.append(_scalar(lines[i].strip()[1:].strip(), err(i + 1)))
                i += 1
            if items:
                fm[key] = items
            elif i < n and lines[i][:1] in " \t" and lines[i].strip():
                raise FrontmatterError(f"{path}:{i + 1}: unsupported nested value under {key!r}")
            else:
                fm[key] = ""
        elif val.startswith("["):
            fm[key] = _inline_list(val, err(no))
        else:
            fm[key] = _scalar(val, err(no))
    return fm, "".join(lines[i:])


# ---- readers --------------------------------------------------------------------------------


def _core():
    spec = importlib.util.spec_from_file_location("_workbench_core", _CORE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _tuple(v) -> tuple[str, ...]:
    if isinstance(v, list):
        return tuple(str(x) for x in v)
    return tuple(x.strip() for x in v.split(",") if x.strip()) if v else ()


def _read_fm(f: Path) -> tuple[dict, str]:
    return parse_frontmatter(f.read_text(), str(f))


def _rules(root: Path) -> tuple[Rule, ...]:
    out = []
    for f in sorted((root / ".claude" / "rules").glob("*.md")):
        fm, body = _read_fm(f)
        out.append(Rule(f.stem, _tuple(fm.get("paths")), body))
    return tuple(out)


def _skills(plugin: Path) -> tuple[Skill, ...]:
    out = []
    for f in sorted((plugin / "skills").glob("*/SKILL.md")):
        fm, body = _read_fm(f)
        out.append(
            Skill(fm.get("name", f.parent.name), fm.get("description", ""), fm, body, f.parent)
        )
    return tuple(out)


def _agents(plugin: Path) -> tuple[Agent, ...]:
    out = []
    for f in sorted((plugin / "agents").glob("*.md")):
        fm, body = _read_fm(f)
        out.append(
            Agent(
                fm.get("name", f.stem),
                fm.get("description", ""),
                fm.get("model") or None,
                _tuple(fm.get("tools")),
                body,
            )
        )
    return tuple(out)


def _hooks(plugin: Path) -> tuple[HookReg, ...]:
    manifest = plugin / ".claude-plugin" / "plugin.json"
    if not manifest.is_file():
        return ()
    out = []
    for event, groups in json.loads(manifest.read_text()).get("hooks", {}).items():
        for g in groups:
            for h in g.get("hooks", []):
                cmd = h.get("command", "")
                script = next((t for t in reversed(shlex.split(cmd)) if "/" in t or "." in t), "")
                if h.get("type", "command") == "command" and script:
                    out.append(HookReg(event, g.get("matcher", ""), Path(script).stem))
    return tuple(out)


def _plugins(root: Path) -> tuple[PluginSource, ...]:
    market, settings = (
        root / ".claude-plugin" / "marketplace.json",
        root / ".claude" / "settings.json",
    )
    if not (market.is_file() and settings.is_file()):
        return ()
    m = json.loads(market.read_text())
    enabled = json.loads(settings.read_text()).get("enabledPlugins", {})
    out = []
    for p in m.get("plugins", []):
        if enabled.get(f"{p['name']}@{m['name']}") is True:
            r = Path(os.path.normpath(root / p["source"])) if "source" in p else root
            out.append(PluginSource(p["name"], r, _skills(r), _agents(r), _hooks(r)))
    return tuple(out)


def load_sources(root: Path) -> Sources:
    root = Path(root)
    agents_md = (root / "AGENTS.md").read_text()
    blocks = {
        m.group(1): m.group(2)
        for m in re.finditer(
            r"<!-- workbench:([\w-]+):begin -->(.*?)<!-- workbench:\1:end -->", agents_md, re.S
        )
    }
    mcp_file = root / ".mcp.json"
    cfg = _core().load_config(root)["harness"]
    return Sources(
        root=root,
        agents_md=agents_md,
        agents_blocks=blocks,
        rules=_rules(root),
        mcp=json.loads(mcp_file.read_text()) if mcp_file.is_file() else None,
        harness=HarnessConfig(
            tuple(cfg.get("targets", ())), dict(cfg.get("models", {})), cfg.get("active", "")
        ),
        plugins=_plugins(root),
    )
