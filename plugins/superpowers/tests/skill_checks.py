"""Shared structure checks for the vendored skills under plugins/superpowers/skills/.

Every per-skill test calls problems(<skill>) and asserts it returns nothing: frontmatter
`name` equals the directory, `description` is present, every `superpowers:<x>` names a
vendored skill, every relative file a skill file names exists, and no file holds an em dash.
"""

import re
from pathlib import Path

from harness.sources import parse_frontmatter

PLUGIN = Path(__file__).resolve().parents[1]
SKILLS = PLUGIN / "skills"
EM_DASH = chr(0x2014)
# The skills this fork vendors (plan.md items 1.1, 2.1, 2.2);
# a `superpowers:<x>` reference must name one.
VENDORED = frozenset(
    {
        "brainstorming",
        "writing-plans",
        "subagent-driven-development",
        "using-git-worktrees",
        "requesting-code-review",
        "finishing-a-development-branch",
        "systematic-debugging",
        "test-driven-development",
        "verification-before-completion",
        "receiving-code-review",
        "dispatching-parallel-agents",
        "using-superpowers",
    }
)
SKILL_REF = re.compile(r"superpowers:([a-z][a-z0-9-]*)")
MD_LINK = re.compile(r"\]\(([^)\s]+)\)")
PLUGIN_ROOT_PATH = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([\w./-]+)")
DOT_PATH = re.compile(r"`(\.\.?/[\w./-]+)`")


def skill_files(name: str) -> list[Path]:
    """Return every file of the skill, sorted.

    Args:
        name (str): skill directory name.

    Returns:
        list[Path]: the files under skills/<name>/.
    """
    return sorted(
        p for p in (SKILLS / name).rglob("*") if p.is_file() and "__pycache__" not in p.parts
    )


def skill_text(name: str) -> str:
    """Return the concatenated text of every markdown file of the skill.

    Args:
        name (str): skill directory name.

    Returns:
        str: all `.md` files joined by newlines.
    """
    return "\n".join(p.read_text() for p in skill_files(name) if p.suffix == ".md")


def flat(text: str) -> str:
    """Return the text with every whitespace run collapsed to one space, so wrapped phrases match.

    Args:
        text (str): any text.

    Returns:
        str: the collapsed text.
    """
    return " ".join(text.split())


def missing_paths(md: Path) -> list[str]:
    """Return the relative files a markdown file names that do not exist.

    Markdown link targets and backticked `./` or `../` paths resolve against the file's
    directory; `${CLAUDE_PLUGIN_ROOT}/<path>` resolves against the plugin root. Paths holding
    a placeholder (`<`), URLs and anchors are skipped.

    Args:
        md (Path): the markdown file.

    Returns:
        list[str]: one entry per missing path.
    """
    text = md.read_text()
    missing = []
    for target in MD_LINK.findall(text) + DOT_PATH.findall(text):
        target = target.split("#")[0]
        if not target or "://" in target or "<" in target:
            continue
        if not (md.parent / target).exists():
            missing.append(f"{md.name}: {target}")
    for target in PLUGIN_ROOT_PATH.findall(text):
        target = target.rstrip(".")
        if not (PLUGIN / target).exists():
            missing.append(f"{md.name}: ${{CLAUDE_PLUGIN_ROOT}}/{target}")
    return missing


def problems(name: str) -> list[str]:
    """Return every structure problem of one vendored skill; empty when it is sound.

    Args:
        name (str): skill directory name.

    Returns:
        list[str]: one line per problem.
    """
    skill = SKILLS / name / "SKILL.md"
    if not skill.is_file():
        return [f"{name}: no SKILL.md"]
    found = []
    meta, _ = parse_frontmatter(skill.read_text(), str(skill))
    if meta.get("name") != name:
        found.append(f"{name}: frontmatter name is {meta.get('name')!r}")
    if not str(meta.get("description") or "").strip():
        found.append(f"{name}: no description")
    for path in skill_files(name):
        text = path.read_text()
        if EM_DASH in text:
            found.append(f"{path.name}: em dash")
        if path.suffix != ".md":
            continue
        for ref in SKILL_REF.findall(text):
            if ref not in VENDORED:
                found.append(f"{path.name}: superpowers:{ref} is not vendored")
        found.extend(missing_paths(path))
    return found
