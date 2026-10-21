"""Render every skill of every enabled plugin as `.agents/skills/<name>/SKILL.md` (design D4).

Only SKILL.md is emitted: scripts, references and templates stay in `plugins/<plugin>/` and the
body is rewritten to point there, so one copy of the code exists.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .sources import parse_frontmatter

CLAUDE_ONLY = frozenset({"heartbeat", "hook-probe"})
_NAME = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
_PLUGIN_ROOT = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/|\$CLAUDE_PLUGIN_ROOT/")
_REL = re.compile(r"(?<![\w./${}-])((?:scripts|references|templates)/[\w./-]*)")

RETURN_FILE = "<scratchpad dir>/<epic>-return.json"
MAXIMUM = "a stated maximum (10 minutes unless a tool sets a shorter one)"
BOUNDED_WAIT = (
    f"a bounded wait with {MAXIMUM}, after which you re-check and report what resolved and "
    "what did not"
)
QUESTIONS = "numbered prose questions (each with its options and a recommended answer)"


def _cased(text: str):
    """A replacement capitalised when the match starts a line or sentence, else lower case."""

    def repl(m: re.Match) -> str:
        before = m.string[: m.start()].rstrip(" ")
        start = not before or before.endswith(("\n", ".", ":", "!", "?"))
        return text[0].upper() + text[1:] if start else text

    return repl


# Claude Code constructs a harness without its runtime cannot use, and what it does instead.
# Specific sentences first, then the generic token rules that catch any other wording.
CLAUDE_CONSTRUCTS: tuple[tuple[re.Pattern, object], ...] = (
    (
        re.compile(r"through a named copy \(`meta\.name` must be a literal\)"),
        "over the args JSON that `ticket.py args` writes",
    ),
    (
        re.compile(r"Workflow\(\{.*?\}\)", re.S),
        "# no workflow runtime in this harness: run the `plan-execute` skill over\n"
        f"# <scratchpad dir>/<epic>-args.json; it writes its return to {RETURN_FILE}",
    ),
    (re.compile(r"`?Workflow\([^)]*\)`?"), "the `plan-execute` skill"),
    (
        re.compile(r"On return, `ticket\.py apply-run <epic> <return\.json>`"),
        f"When the `plan-execute` skill finishes, `ticket.py apply-run <epic> {RETURN_FILE}` "
        "(the return file that skill writes)",
    ),
    (re.compile(r"<return\.json>"), RETURN_FILE),
    (
        re.compile(r"(ticket\.py continue <epic> --out-dir <dir>)(?! --return)"),
        rf"\1 --return {RETURN_FILE}",
    ),
    (
        re.compile(r"[Tt]o wait on the run, arm `heartbeat\.py[^`]*`(?: \([^)]*\))?"),
        "The `plan-execute` skill runs in this session, so there is no run to wait on; "
        f"every wait inside it is {BOUNDED_WAIT}",
    ),
    (re.compile(r"on END read the return"), "when it finishes, read its return file"),
    (
        re.compile(r"\b[Aa]rm (?:`heartbeat\.py[^`]*`|(?:an?|one|the) Monitor\b)"),
        _cased(f"wait with {MAXIMUM}"),
    ),
    (re.compile(r"`heartbeat\.py[^`]*`|\b(?:an?|one|the) Monitor\b"), _cased(BOUNDED_WAIT)),
    (re.compile(r"\bMonitor\b"), f"bounded wait with {MAXIMUM}"),
    (re.compile(r"`AskUserQuestion`(?: tool)?|\bAskUserQuestion\b"), _cased(QUESTIONS)),
)


def rewrite_claude_constructs(text: str) -> str:
    """Replace every Claude-only construct (CLAUDE_CONSTRUCTS) with its portable equivalent."""
    for pattern, repl in CLAUDE_CONSTRUCTS:
        text = pattern.sub(repl, text)
    return text


class SkillError(ValueError):
    """An invalid or colliding skill name."""


def _value(v) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, list):
        return "[" + ", ".join(_value(x) for x in v) + "]"
    return json.dumps(str(v), ensure_ascii=False)


def _frontmatter(fm: dict, name: str) -> str:
    rest = "".join(f"{k}: {_value(v)}\n" for k, v in fm.items() if k != "name")
    return f"---\nname: {name}\n{rest}---\n"


def _rewrite(
    text: str,
    prefix: str,
    plugin_names: list[str],
    skill_dir: Path | None = None,
    plugin_root: Path | None = None,
) -> str:
    text = _PLUGIN_ROOT.sub(prefix + "/", rewrite_claude_constructs(text))
    if skill_dir is not None and plugin_root is not None:
        text = _REL.sub(lambda m: _relative(m, prefix, skill_dir, plugin_root), text)
    names = "|".join(re.escape(n) for n in sorted(plugin_names, key=len, reverse=True))
    return re.sub(rf"(?<![\w-])(?:{names}):(?=[a-z0-9])", "", text)


def _relative(m: re.Match, prefix: str, skill_dir: Path, plugin_root: Path) -> str:
    """A skill-relative path points into the skill dir, else (when only there) the plugin root."""
    token = m.group(1)
    probe = token.rstrip(".-")
    if not (skill_dir / probe).exists() and (plugin_root / probe).exists():
        return f"{prefix}/{token}"
    return f"{prefix}/skills/{skill_dir.name}/{token}"


def _check_name(name: str, plugin: str, dirname: str) -> None:
    if len(name) > 64 or not _NAME.fullmatch(name):
        raise SkillError(
            f"{plugin}: skill name {name!r} is invalid (1-64 chars, lowercase letters, digits "
            "and single hyphens, no leading or trailing hyphen)"
        )
    if name != dirname:
        raise SkillError(f"{plugin}: skill name {name!r} must equal its directory {dirname!r}")


def render_skills(sources) -> dict[str, str]:
    """Repo-relative path -> text for every emitted skill; raises SkillError on bad names."""
    out: dict[str, str] = {}
    owner: dict[str, str] = {}
    plugin_names = ["workbench", *(p.name for p in sources.plugins)]
    for plugin in sources.plugins:
        prefix = os.path.relpath(plugin.root, sources.root).replace(os.sep, "/")
        for skill in plugin.skills:
            if skill.dir.name in CLAUDE_ONLY:
                continue
            _check_name(skill.name, plugin.name, skill.dir.name)
            if skill.name in owner:
                raise SkillError(
                    f"duplicate skill name {skill.name!r} in plugins "
                    f"{owner[skill.name]} and {plugin.name}"
                )
            owner[skill.name] = plugin.name
            fm = {
                k: _rewrite(v, prefix, plugin_names) if k == "description" else v
                for k, v in skill.frontmatter.items()
            }
            body = _rewrite(skill.body, prefix, plugin_names, skill.dir, plugin.root)
            out[f".agents/skills/{skill.name}/SKILL.md"] = _frontmatter(fm, skill.name) + body
    _fallbacks(sources, plugin_names, out, owner)
    return out


def _fallbacks(sources, plugin_names: list[str], out: dict, owner: dict) -> None:
    """Skills for workflows with no runtime outside Claude Code, shipped under
    scripts/harness/fallbacks/<name>/SKILL.md and emitted for every target like plugin skills."""
    core = next((p for p in sources.plugins if p.name == "workbench"), None)
    prefix = "plugins/workbench"
    if core:
        prefix = os.path.relpath(core.root, sources.root).replace(os.sep, "/")
    for f in sorted((sources.root / "scripts" / "harness" / "fallbacks").glob("*/SKILL.md")):
        fm, raw = parse_frontmatter(f.read_text(), str(f))
        name = fm.get("name", f.parent.name)
        _check_name(name, "fallbacks", f.parent.name)
        if name in owner:
            raise SkillError(
                f"duplicate skill name {name!r} in plugins {owner[name]} and fallbacks"
            )
        owner[name] = "fallbacks"
        fm = {
            k: _rewrite(v, prefix, plugin_names) if k == "description" else v for k, v in fm.items()
        }
        body = _rewrite(raw, prefix, plugin_names)
        out[f".agents/skills/{name}/SKILL.md"] = _frontmatter(fm, name) + body
