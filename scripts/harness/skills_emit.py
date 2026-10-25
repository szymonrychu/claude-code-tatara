"""Render every skill of every enabled plugin as `.agents/skills/<name>/SKILL.md` (design D4).

Only SKILL.md is emitted: scripts, references and templates stay in `plugins/<plugin>/` and the
body is rewritten to point there, so one copy of the code exists.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

_NAME = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
_PLUGIN_ROOT = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/|\$CLAUDE_PLUGIN_ROOT/")
_REL = re.compile(r"(?<![\w./${}-])((?:scripts|references|templates)/[\w./-]*)")

QUESTIONS = "numbered prose questions (each with its options and a recommended answer)"


def _cased(text: str):
    """A replacement capitalised when the match starts a line or sentence, else lower case."""

    def repl(m: re.Match) -> str:
        before = m.string[: m.start()].rstrip(" ")
        start = not before or before.endswith(("\n", ".", ":", "!", "?"))
        return text[0].upper() + text[1:] if start else text

    return repl


# Claude Code constructs a harness without its runtime cannot use, and what it does instead.
CLAUDE_CONSTRUCTS: tuple[tuple[re.Pattern, object], ...] = (
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
    return out

