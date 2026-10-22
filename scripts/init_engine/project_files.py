"""project_files: what init writes into the workbench's own docs and tasks (design D9).

`write_all` is called at the end of `new` and `adopt` and re-run by `component add` and
`component remove`. Every write is idempotent: it regenerates its own section from
`.gitmodules` and keeps what the user or agent already filled in. The components themselves
are never touched.
"""

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from gitops import Refusal, git

UNINIT_RE = re.compile(
    r"<!-- workbench:uninitialised:begin -->.*?<!-- workbench:uninitialised:end -->\n*", re.S
)


def is_initialised(root: Path) -> bool:
    """True when `root` has an AGENTS.md without the template's uninitialised block."""
    agents = Path(root) / "AGENTS.md"
    return agents.is_file() and not UNINIT_RE.search(agents.read_text())


PROJECT_RE = re.compile(
    r"(<!-- workbench:project:begin -->\n)(.*?)(<!-- workbench:project:end -->)", re.S
)
TEMPLATE_MAINT_RE = re.compile(r"\n*^## Template maintenance\n.*?(?=^## |\Z)", re.S | re.M)
CODE_TASKS_BEGIN = "# workbench:code-tasks:begin"
CODE_TASKS_END = "# workbench:code-tasks:end"
PLACEHOLDER_STARTS = ("_Filled by init", "_Ask the user")
BUILD_TASKS = ("test", "lint", "fmt")
MEMORY_HEADER = (
    "# MEMORY\n\nDated entries, newest last. Supersede an entry rather than deleting it. "
    "One line per non-obvious decision.\n"
)
ROADMAP_BODY = (
    "# ROADMAP\n\nThis file holds the human-owned goals and requirements for the project. "
    "The agent asks the user for them and never invents them. Entries are added only at the "
    "user's direction.\n\nNo requirements are recorded yet: the agent asks the user for them.\n"
)
ASK = {
    "What this project is building": (
        "_Ask the user: what the product is and who it is for, then replace this line._"
    ),
    "Component hard rules": (
        "_Ask the user: the rules every component must obey, one per line, then replace this line._"
    ),
    "Highest-risk surface": (
        "_Ask the user: the surface where a mistake costs the most and what must never "
        "break there, then replace this line._"
    ),
}


@dataclass
class Answers:
    """What the user told init; empty values keep what the docs already say."""

    purpose: list[str] = field(default_factory=list)
    hard_rules: list[str] = field(default_factory=list)
    risk: str | None = None
    roles: dict[str, str] = field(default_factory=dict)
    langs: dict[str, str] = field(default_factory=dict)


def parse_roles(specs: list[str]) -> dict[str, str]:
    roles = {}
    for spec in specs:
        name, sep, text = spec.partition("=")
        if not sep or not name.strip() or not text.strip():
            raise Refusal(f"invalid --role {spec!r}: use <component>=<text>")
        roles[name.strip()] = text.strip()
    return roles


def components(root: Path) -> list[tuple[str, str]]:
    """(name, url) of every code/ submodule in .gitmodules, in file order."""
    if not (root / ".gitmodules").is_file():
        return []
    proc = git(
        "config",
        "-f",
        ".gitmodules",
        "--get-regexp",
        r"^submodule\..+\.path$",
        cwd=root,
        check=False,
    )
    out = []
    for line in proc.stdout.splitlines():
        match = re.match(r"^submodule\.(.+)\.path (.+)$", line.strip())
        if match and match.group(2).startswith("code/"):
            url = git(
                "config",
                "-f",
                ".gitmodules",
                f"submodule.{match.group(1)}.url",
                cwd=root,
                check=False,
            ).stdout.strip()
            out.append((match.group(1), url))
    return out


def detect_lang(repo: Path) -> str:
    if (repo / "go.mod").exists():
        return "go"
    if any((repo / f).exists() for f in ("pyproject.toml", "setup.py", "requirements.txt")):
        return "python"
    if (repo / "package.json").exists():
        return "typescript"
    return "generic"


def forge_of(url: str) -> str:
    host = re.search(r"(?:://(?:[^@/]+@)?|^[^@/:]+@)([^/:]+)", url)
    name = host.group(1).lower() if host else ""
    if "gitlab" in name:
        return "gitlab"
    if "github" in name:
        return "github"
    return "local"


def forge_section(comps: list[tuple[str, str]]) -> str:
    kinds = {forge_of(url) for _, url in comps}
    lines = ["## Forge", ""]
    if not comps:
        lines.append("No components yet, so no forge: it is set by the first component's origin.")
    elif kinds == {"github"}:
        lines.append("Origins are on GitHub: changes land through pull requests (PRs), via `gh`.")
    elif kinds == {"gitlab"}:
        lines.append(
            "Origins are on GitLab: changes land through merge requests (MRs), via `glab`."
        )
    elif kinds <= {"github", "gitlab"}:
        by = ", ".join(f"{n}: {'PR' if forge_of(u) == 'github' else 'MR'}" for n, u in comps)
        lines.append(
            f"Origins are on GitHub and GitLab: pull requests (PR) or merge requests (MR) "
            f"per component ({by})."
        )
    else:
        lines.append(
            "At least one origin is not on a known forge (a local bare repo or an unrecognised "
            "host): there it has no PRs or MRs, so changes land by merging the branch into the "
            "component's default branch and pushing it."
        )
    return "\n".join(lines)


def split_sections(block: str) -> dict[str, str]:
    parts = re.split(r"^## (.+)$", block, flags=re.M)
    return {parts[i].strip(): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}


def is_placeholder(body: str) -> bool:
    return not body or body.startswith(PLACEHOLDER_STARTS)


def old_rows(section: str) -> dict[str, tuple[str, str]]:
    rows = {}
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and not set(cells[0]) <= set("-: ") and cells[0] != "Submodule":
            rows[cells[0]] = (cells[1], cells[2])
    return rows


def one_line(text: str) -> str:
    return " ".join(text.replace("|", "/").split())


def resolve_langs(root: Path, comps, answers: Answers, old: dict) -> dict[str, str]:
    return {
        n: answers.langs.get(n) or (old[n][0] if n in old else detect_lang(root / "code" / n))
        for n, _ in comps
    }


def resolve_roles(comps, answers: Answers, old: dict) -> dict[str, str]:
    names = {n for n, _ in comps}
    unknown = sorted(set(answers.roles) - names)
    if unknown:
        raise Refusal(f"--role names no component: {', '.join(unknown)}")
    placeholder = "ask the user"
    return {
        n: one_line(answers.roles.get(n) or (old[n][1] if n in old else placeholder))
        for n, _ in comps
    }


def agents_md(root: Path, comps, answers: Answers) -> tuple[dict, dict]:
    path = root / "AGENTS.md"
    text = path.read_text()
    match = PROJECT_RE.search(text)
    if not match:
        raise Refusal("AGENTS.md has no workbench:project block")
    old = split_sections(match.group(2))
    rows = old_rows(old.get("Components (code/)", ""))
    langs = resolve_langs(root, comps, answers, rows)
    roles = resolve_roles(comps, answers, rows)

    def pick(title: str, given: str) -> str:
        if given:
            return given
        return old[title] if title in old and not is_placeholder(old[title]) else ASK[title]

    table = ["| Submodule | Lang | Role | Build |", "|-----------|------|------|-------|"]
    table += [
        f"| {n} | {langs[n]} | {roles[n]} | `mise run --cd code/{n} test` |" for n, _ in comps
    ]
    sections = [
        (
            "What this project is building",
            pick("What this project is building", "\n\n".join(answers.purpose)),
        ),
        ("Components (code/)", "\n".join(table)),
        (
            "Component hard rules",
            pick("Component hard rules", "\n".join(f"- {r}" for r in answers.hard_rules)),
        ),
        ("Highest-risk surface", pick("Highest-risk surface", answers.risk or "")),
    ]
    body = "\n\n".join(f"## {t}\n\n{b}" for t, b in sections)
    body += "\n\n" + forge_section(comps) + "\n"
    text = text[: match.start()] + match.group(1) + body + match.group(3) + text[match.end() :]
    text = UNINIT_RE.sub("", text)
    text = TEMPLATE_MAINT_RE.sub("", text)
    path.write_text(text.rstrip("\n") + "\n")
    return langs, roles


def mise_toml(root: Path, comps) -> None:
    path = root / ".mise.toml"
    text = path.read_text()
    head, sep1, rest = text.partition(CODE_TASKS_BEGIN + "\n")
    _, sep2, tail = rest.partition(CODE_TASKS_END)
    if not (sep1 and sep2):
        raise Refusal(".mise.toml has no workbench:code-tasks markers")
    blocks = []
    for task in BUILD_TASKS:
        calls = [f'  "mise run --cd code/{n} {task}",' for n, _ in comps]
        run = "[\n" + "\n".join(calls) + "\n]" if calls else "\"echo 'no components yet'\""
        blocks.append(
            f'[tasks."code:{task}"]\ndescription = "Run {task} in every component"\nrun = {run}\n'
        )
    path.write_text(head + sep1 + "\n".join(blocks) + CODE_TASKS_END + tail)


def architecture_md(root: Path, comps, langs: dict, roles: dict) -> None:
    path = root / "docs" / "architecture.md"
    text = path.read_text() if path.is_file() else "# Architecture\n"
    lines = ["## Components", "", "```", f"{root.name}/", "  code/"]
    lines += [f"    {n}/  ({langs[n]})" for n, _ in comps]
    lines.append("```")
    lines.append("")
    lines += [f"- `code/{n}` ({langs[n]}): {roles[n]}" for n, _ in comps]
    if not comps:
        lines.append("No components yet.")
    section = "\n".join(lines) + "\n"
    existing = re.search(r"^## Components\n.*?(?=^## |\Z)", text, re.S | re.M)
    if existing:
        tail = text[existing.end() :]
        text = text[: existing.start()] + section + ("\n" + tail if tail else "")
    else:
        text = text.rstrip("\n") + "\n\n" + section
    path.parent.mkdir(exist_ok=True)
    path.write_text(text)


def memory_and_roadmap(root: Path, comps, method: str, event: str | None, today: str) -> None:
    mem = root / "MEMORY.md"
    current = mem.read_text() if mem.is_file() else ""
    names = ", ".join(n for n, _ in comps) or "none"
    if "project initialised" not in current:
        entry = f"{today}: project initialised; components: {names}; adoption method: {method}.\n"
        mem.write_text(MEMORY_HEADER + "\n" + entry)
        (root / "ROADMAP.md").write_text(ROADMAP_BODY)
        return
    entry = f"{today}: {event or f'components now: {names}; via {method}'}.\n"
    if entry not in current:
        mem.write_text(current.rstrip("\n") + "\n" + entry)


def write_all(
    root: Path,
    answers: Answers | None = None,
    method: str = "unspecified",
    event: str | None = None,
    today: str | None = None,
) -> None:
    root = root.resolve()
    answers = answers or Answers()
    comps = components(root)
    today = today or date.today().isoformat()
    langs, roles = agents_md(root, comps, answers)
    mise_toml(root, comps)
    architecture_md(root, comps, langs, roles)
    memory_and_roadmap(root, comps, method, event, today)
    print("wrote AGENTS.md, .mise.toml code tasks, docs/architecture.md, MEMORY.md, ROADMAP.md")
