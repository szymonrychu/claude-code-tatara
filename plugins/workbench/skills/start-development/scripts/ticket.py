#!/usr/bin/env python3
"""ticket.py: file-based plans under docs/plans/{todo,in-progress,done}/<plan>/.

A plan dir holds plan.md (what and why, scope ladder, agreed scope), implementation-plan.md (the
agreed rung's chunks and steps), retro.md (written by the reviewer when the review passes) and
close.json (written by close). A plan's slug is its branch and worktree name.
Subcommands: slug, new, check, path, rename, move, worktrees, reap, plus ticket_cmds/ modules.
Every mutating subcommand calls require_main_checkout() first and commit_ticket_change() last.
Worktree cleanup removes only merged, clean trees, through worktree-merge's cleanup().
"""

from __future__ import annotations

import argparse
import datetime
import difflib
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_lib"))

from common import slugify  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "lib"))

import workbench  # noqa: E402

PHASES = ("todo", "in-progress", "done")
SLUG_MAX = 28
NEAR_DUP = 0.6
EXIT_NEAR_DUPLICATE = 3  # new stopped on a live near-duplicate plan; --force overrides
TEMPLATES = Path(__file__).resolve().parents[1] / "templates"
PLAN_FILE = "plan.md"
OLD_FORMAT_FILE = "README.md"
PATH_KINDS = {
    "plan": PLAN_FILE,
    "implementation": "implementation-plan.md",
    "retro": "retro.md",
    "close": "close.json",
}


class TicketError(Exception):
    pass


def slug(title: str) -> str:
    return slugify(title, SLUG_MAX)


# ---------------------------------------------------------------- frontmatter


class Doc(NamedTuple):
    meta: dict
    body: str


_BARE = re.compile(r"[A-Za-z0-9_./][A-Za-z0-9_./ -]*")
_KEY = re.compile(r"([A-Za-z_][A-Za-z0-9_-]*):(?: (.*))?$")


def _scalar(s: str) -> str:
    if _BARE.fullmatch(s) and not s.endswith(" ") and not s.startswith("- "):
        return s
    esc = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{esc}"'


def _parse_quoted(s: str, i: int) -> tuple[str, int]:
    """Parse a quoted string starting at s[i]; return (value, index after the closing quote)."""
    q, out, i = s[i], [], i + 1
    while i < len(s):
        c = s[i]
        if q == "'" and c == "'":
            if s[i + 1 : i + 2] == "'":
                out.append("'")
                i += 2
                continue
            return "".join(out), i + 1
        if q == '"' and c == "\\" and i + 1 < len(s):
            out.append({"n": "\n"}.get(s[i + 1], s[i + 1]))
            i += 2
            continue
        if q == '"' and c == '"':
            return "".join(out), i + 1
        out.append(c)
        i += 1
    raise ValueError("unterminated quote")


def _parse_value(raw: str):
    raw = raw.strip()
    if raw.startswith("["):
        if not raw.endswith("]"):
            raise ValueError("unterminated list")
        inner, items, i = raw[1:-1], [], 0
        while True:
            while i < len(inner) and inner[i] == " ":
                i += 1
            if i >= len(inner):
                break
            if inner[i] in "'\"":
                val, i = _parse_quoted(inner, i)
            else:
                j = inner.find(",", i)
                j = len(inner) if j < 0 else j
                val, i = inner[i:j].strip(), j
                if re.search(r"[\[\]{}\"']", val):
                    raise ValueError("bad list item")
            items.append(val)
            while i < len(inner) and inner[i] == " ":
                i += 1
            if i < len(inner):
                if inner[i] != ",":
                    raise ValueError("bad list")
                i += 1
        return items
    if raw.startswith("{") or raw.startswith("|") or raw.startswith(">"):
        raise ValueError("unsupported value")
    if raw[:1] in "'\"":
        val, end = _parse_quoted(raw, 0)
        if raw[end:].strip():
            raise ValueError("trailing text")
        return val
    return raw


def load(text: str, path) -> Doc:
    """Parse '---' delimited frontmatter (scalars, quoted strings, inline lists) plus body."""
    lines = text.split("\n")
    if lines[0] != "---":
        raise TicketError(f"{path}:1: unsupported frontmatter")
    meta: dict = {}
    for n, line in enumerate(lines[1:], start=2):
        if line == "---":
            return Doc(meta, "\n".join(lines[n:]))
        m = _KEY.match(line)
        if not m or m.group(1) in meta:
            raise TicketError(f"{path}:{n}: unsupported frontmatter")
        nxt = lines[n] if n < len(lines) else ""
        if not m.group(2) and (nxt.startswith((" ", "\t")) or nxt.startswith("- ")):
            raise TicketError(f"{path}:{n}: unsupported frontmatter")
        try:
            meta[m.group(1)] = _parse_value(m.group(2) or "")
        except ValueError:
            raise TicketError(f"{path}:{n}: unsupported frontmatter") from None
    raise TicketError(f"{path}:{len(lines)}: unsupported frontmatter")


def dump(doc: Doc) -> str:
    out = ["---"]
    for k, v in doc.meta.items():
        val = "[" + ", ".join(_scalar(x) for x in v) + "]" if isinstance(v, list) else _scalar(v)
        out.append(f"{k}: {val}")
    out.append("---")
    return "\n".join(out) + "\n" + doc.body


def read_doc(path: Path) -> Doc:
    return load(path.read_text(), path)


# ---------------------------------------------------------------- layout


class Plan(NamedTuple):
    slug: str
    phase: str
    dir: Path
    meta: dict
    body: str


def default_root() -> Path:
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    top = Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else Path.cwd()
    return top / "docs" / "plans"


def plan_dirs(root: Path) -> list[Path]:
    """Every plan dir under root, phase then slug order; an old epic dir (README.md and no
    plan.md) or a dir without plan.md is refused, so no command reads a half-migrated tree."""
    out = []
    for phase in PHASES:
        base = Path(root) / phase
        for d in sorted(p for p in base.iterdir() if p.is_dir()) if base.is_dir() else []:
            if not (d / PLAN_FILE).is_file():
                if (d / OLD_FORMAT_FILE).exists():
                    raise TicketError(
                        f"old epic format under {d.resolve()}; run ticket.py migrate --all"
                    )
                raise TicketError(f"no {PLAN_FILE} under {d.resolve()}")
            out.append(d)
    return out


def read_plan(plan_dir: Path) -> Plan:
    doc = read_doc(plan_dir / PLAN_FILE)
    return Plan(plan_dir.name, plan_dir.parent.name, plan_dir, doc.meta, doc.body)


def scan(root: Path) -> list[Plan]:
    """Every plan under root, all phases."""
    return [read_plan(d) for d in plan_dirs(root)]


def find_plan(slug_: str, root: Path) -> Path | None:
    for phase in PHASES:
        d = Path(root) / phase / slug_
        if d.is_dir():
            return d
    return None


def resolve_plan(arg: str, root: Path) -> Path:
    """A plan slug or a plan directory path, to the plan directory. Every plan dir under root
    is validated first (see plan_dirs)."""
    plan_dirs(root)
    p = Path(arg)
    if (p.parent != Path(".") or arg.startswith(".")) and p.is_dir():
        resolved = p.resolve()
        if not resolved.is_relative_to(Path(root).resolve()):
            raise TicketError(f"plan path {arg!r} is outside the plans root {root}")
        return resolved
    found = find_plan(arg, root)
    if found is None:
        raise TicketError(f"unknown plan {arg!r} under {root}")
    return found.resolve()


def phase_of(plan_dir: Path) -> str:
    return plan_dir.parent.name


def update_plan_meta(plan_dir: Path, **updates) -> Path:
    """Rewrite plan.md's frontmatter with `updates`; the body is untouched."""
    p = plan_dir / PLAN_FILE
    doc = read_doc(p)
    meta = dict(doc.meta)
    meta.update(updates)
    text = dump(Doc(meta, doc.body))
    if text != p.read_text():
        p.write_text(text)
    return p


# ---------------------------------------------------------------- git guard and commit


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def _existing(p: Path) -> Path:
    p = p.resolve()
    while not p.exists():
        p = p.parent
    return p


def _in_git(root: Path) -> bool:
    return _git(_existing(Path(root)), "rev-parse", "--git-dir").returncode == 0


def require_main_checkout(root: Path) -> None:
    cwd = _existing(Path(root))
    g = _git(cwd, "rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir")
    if g.returncode != 0:
        return
    git_dir, common = g.stdout.split("\n")[:2]
    if Path(git_dir).resolve() != Path(common).resolve():
        raise TicketError("run in the main checkout, not a linked worktree")


def commit_ticket_change(plan: str, event: str, paths: list[Path], root: Path) -> None:
    """Commit exactly `paths` (under root) as 'chore(ticket): <plan> <event>'; no-op outside git."""
    cwd = _existing(Path(root))
    if not _in_git(root):
        return
    rel = [str(Path(p).resolve()) for p in paths]
    root_r = Path(root).resolve()
    for p in rel:
        if root_r not in Path(p).parents:
            raise TicketError(f"refusing to commit {p}: outside {root_r}")
    # A path that a `git mv` moved away no longer exists; the commit pathspec still records it.
    present = [p for p in rel if Path(p).exists()]
    add = _git(cwd, "add", "--", *present) if present else None
    if add is not None and add.returncode != 0:
        raise TicketError(f"git add failed: {add.stderr.strip()}")
    done = _git(cwd, "commit", "-m", f"chore(ticket): {plan} {event}", "--", *rel)
    if done.returncode != 0:
        raise TicketError(f"git commit failed: {(done.stderr or done.stdout).strip()}")


def _git_mv(plan_dir: Path, phase: str, root: Path, name: str | None = None) -> Path:
    """Move a plan directory to <root>/<phase>/<name> with `git mv` (plain rename outside git)."""
    dest = Path(root).resolve() / phase / (name or plan_dir.name)
    if dest.exists():
        raise TicketError(f"{dest} already exists")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not _in_git(root):
        plan_dir.rename(dest)
        return dest
    r = _git(_existing(Path(root)), "mv", str(plan_dir), str(dest))
    if r.returncode != 0:
        raise TicketError(f"git mv failed: {r.stderr.strip()}")
    return dest


# ---------------------------------------------------------------- names and duplicates


def _wt_module():
    """worktree-create's module: the one implementation of worktree creation."""
    p = Path(__file__).resolve().parents[2] / "worktree-create" / "scripts" / "create.py"
    spec = importlib.util.spec_from_file_location("worktree_create", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_WT = None


def _mod():
    global _WT
    if _WT is None:
        _WT = _wt_module()
    return _WT


def _workbench(root: Path) -> Path:
    return _mod().workbench_root(_existing(Path(root)))


def disk_names(root: Path) -> dict[str, str]:
    """Names taken on disk -> what holds them: local branches of the source checkouts (the
    superrepo and every code/<repo>) and directories under <configdir>/worktrees/. Empty
    outside a git checkout."""
    if not _in_git(root):
        return {}
    wb = _workbench(root)
    found: dict[str, str] = {}
    code = wb / "code"
    srcs = [wb] + (sorted(p for p in code.iterdir() if p.is_dir()) if code.is_dir() else [])
    for src in srcs:
        r = _git(src, "for-each-ref", "--format=%(refname:short)", "refs/heads")
        for b in r.stdout.split() if r.returncode == 0 else []:
            found.setdefault(b, f"branch {b}")
    wt_dir = workbench.worktrees_dir(wb)
    for d in sorted(p for p in wt_dir.iterdir() if p.is_dir()) if wt_dir.is_dir() else []:
        found.setdefault(d.name, f"tree {d.name}")
    return found


def name_clashes(root: Path, name: str, plans: list[Plan], own: str | None = None) -> list[str]:
    """Failure lines for a plan slug that is taken: by another plan in any phase, or by a
    branch or worktree on disk (the plan's branch and tree are named after its slug)."""
    for p in plans:
        if p.slug == name and p.slug != own:
            return [f"plan slug {name!r} already exists in {p.phase}"]
    holder = disk_names(root).get(name)
    return [f"plan slug {name} collides with existing {holder}"] if holder else []


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _norm(title: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", title.lower()))


def what_and_why(body: str) -> str:
    m = re.search(r"^## What and why\s*\n(.*?)(?=^## |\Z)", body, re.M | re.S)
    return m.group(1) if m else ""


def similarity(title_a: str, text_a: str, title_b: str, text_b: str) -> float:
    """The larger of the title ratio and the word Jaccard over title plus text."""
    ratio = difflib.SequenceMatcher(None, _norm(title_a), _norm(title_b)).ratio()
    wa, wb = _words(title_a + " " + text_a), _words(title_b + " " + text_b)
    jac = len(wa & wb) / len(wa | wb) if wa | wb else 0.0
    return max(ratio, jac)


def _live_worktrees(root: Path) -> list[str]:
    r = _git(_existing(Path(root)), "worktree", "list", "--porcelain")
    if r.returncode != 0:
        return []
    return [Path(line[9:]).name for line in r.stdout.splitlines() if line.startswith("worktree ")]


class CheckResult(NamedTuple):
    failures: list[str]
    warnings: list[str]
    notes: list[str]
    near: list[tuple[str, str, float]]  # (slug, phase, score)


def run_check(root: Path, title: str) -> CheckResult:
    """Dedup rules for a new plan titled `title`: a taken slug fails; a plan whose title plus
    What and why is similar (>= NEAR_DUP) is listed; a live tree of a plan that is not
    in-progress is warned."""
    root = Path(root)
    plans = scan(root)
    new = slug(title)
    fails = name_clashes(root, new, plans)
    notes: list[str] = []
    near: list[tuple[str, str, float]] = []
    for p in plans:
        if p.slug == new:
            continue
        other = str(p.meta.get("title", p.slug))
        score = similarity(title, "", other, what_and_why(p.body))
        if score >= NEAR_DUP:
            near.append((p.slug, p.phase, score))
            notes.append(f"near-duplicate plan {p.slug} ({p.phase}): {other!r}")
    by_slug = {p.slug: p for p in plans}
    warns = [
        f"warning: live worktree {n!r} belongs to plan {n!r} which is in "
        f"{by_slug[n].phase}, not in-progress"
        for n in _live_worktrees(root)
        if n in by_slug and by_slug[n].phase != "in-progress"
    ]
    return CheckResult(fails, warns, notes, near)


def report(res: CheckResult) -> int:
    for n in res.notes:
        print(n)
    for w in res.warnings:
        print(w, file=sys.stderr)
    for f in res.failures:
        print(f"ticket.py: {f}", file=sys.stderr)
    return 1 if res.failures else 0


# ---------------------------------------------------------------- new, check, path, rename


def _csv(value: str | None) -> list[str]:
    return [x.strip() for x in (value or "").split(",") if x.strip()]


def cmd_new(a: argparse.Namespace) -> int:
    root = Path(a.root)
    require_main_checkout(root)
    plan = slug(a.title)
    if not plan:
        raise TicketError("title has no usable characters")
    res = run_check(root, a.title)
    if report(res):
        return 1
    if not a.force:
        for twin, phase, score in res.near:
            if phase != "done":
                print(
                    f"new: near duplicate {twin} ({score:.2f}); pass --force to create anyway",
                    file=sys.stderr,
                )
                return EXIT_NEAR_DUPLICATE
    template = TEMPLATES / PLAN_FILE
    doc = load(template.read_text(), template)
    doc.meta.update(
        title=a.title,
        repos=_csv(a.repos),
        created=datetime.date.today().isoformat(),
        owner="",
        rung="",
    )
    path = root / "todo" / plan / PLAN_FILE
    path.parent.mkdir(parents=True)
    path.write_text(dump(Doc(doc.meta, doc.body.replace("# <title>", f"# {a.title}", 1))))
    commit_ticket_change(plan, "new", [path], root)
    print(path)
    return 0


def cmd_check(a: argparse.Namespace) -> int:
    return report(run_check(Path(a.root), a.title))


def cmd_path(a: argparse.Namespace) -> int:
    print(resolve_plan(a.plan, Path(a.root)) / PATH_KINDS[a.kind])
    return 0


def cmd_slug(a: argparse.Namespace) -> int:
    print(slug(a.title))
    return 0


def cmd_rename(a: argparse.Namespace) -> int:
    root = Path(a.root)
    require_main_checkout(root)
    plan_dir = resolve_plan(a.plan, root)
    name, phase = plan_dir.name, phase_of(plan_dir)
    if phase != "todo":
        raise TicketError(f"plan {name!r} is in {phase}; its slug froze when it left todo")
    new = slug(a.title)
    if not new:
        raise TicketError("title has no usable characters")
    if new != name:
        clashes = name_clashes(root, new, scan(root), own=name)
        if clashes:
            raise TicketError("; ".join(clashes))
    plan = read_plan(plan_dir)
    old_title = str(plan.meta.get("title", name))
    if new == name and old_title == a.title:
        print(plan_dir)
        return 0
    dest = _git_mv(plan_dir, "todo", root, new) if new != name else plan_dir
    p = update_plan_meta(dest, title=a.title)
    heading = re.compile(rf"^# {re.escape(old_title)}$", re.M)
    p.write_text(heading.sub(lambda _: f"# {a.title}", p.read_text(), count=1))
    commit_ticket_change(new, "rename", [plan_dir, dest], root)
    print(dest)
    return 0


# ---------------------------------------------------------------- retired task machinery (S5)
import agent_usage  # noqa: E402
import calibration  # noqa: E402

TASK_STATUSES = ("todo", "in-progress", "done", "blocked", "escalated")
EPIC_STAGES = ("build", "review")
WORKTREE_MAX = SLUG_MAX + 1 + SLUG_MAX
LEGACY_SEP = "--"
AC_KINDS = ("test", "symbol", "command", "doc-section", "judgement")
AC_LINE = re.compile(r"^- (\S+?): (.+?) \[evidence: ([a-z-]+)(?::\s*(.*?))?\]$")
REQUIRED_SECTIONS = ("Requirement", "Acceptance conditions", "Files", "Steps")
POINT_KEYS = ("points", "points_actual")
COUNT_KEYS = ("expected_minutes", "expected_tokens", "actual_minutes", "actual_tokens")
ROLE_KEYS = ("actual_roles", "actual_role_tokens")
ROLES = ("impl", "review")
ROLE_PAIR = re.compile(r"(impl|review) ([0-9]+)")
Ticket = Plan
_read_doc = read_doc
resolve_epic = resolve_plan
find_epic = find_plan
_phase_of = phase_of


def worktree_name(epic: str, task: str) -> str:
    return f"{epic}-{task}"


def ticket_names(root: Path) -> dict:
    return {p.slug: (p.slug, None) for p in scan(root)}


def _read(path: str | None) -> str:
    return Path(path).read_text().strip() if path else ""


def _render(body: str, values: dict[str, str]) -> str:
    for k, v in values.items():
        body = body.replace("{{" + k + "}}", v)
    return body


def _template(name: str) -> Doc:
    p = TEMPLATES / name
    return load(p.read_text(), p)


def _count(value, task: str, field: str) -> int | None:
    """A whole non-negative number field (frontmatter values load as strings); unset is None."""
    if value in (None, ""):
        return None
    if not re.fullmatch(r"[0-9]+", str(value)):
        raise TicketError(f"task {task!r}: {field} must be a whole number >= 0: {value!r}")
    return int(value)


def _points(value, task: str, field: str) -> int | None:
    """A storypoints field, one of calibration.POINTS; unset is None."""
    if value in (None, ""):
        return None
    if re.fullmatch(r"[0-9]+", str(value)) and int(value) in calibration.POINTS:
        return int(value)
    allowed = ", ".join(map(str, calibration.POINTS))
    raise TicketError(f"task {task!r}: {field} must be one of {allowed}: {value!r}")


def _parse_roles(value, task: str, field: str) -> dict[str, int] | None:
    """`impl N, review N` (each role at most once) to {role: N}; unset is None."""
    if value in (None, ""):
        return None
    out: dict[str, int] = {}
    for part in str(value).split(","):
        m = ROLE_PAIR.fullmatch(part.strip())
        if not m or m.group(1) in out:
            raise TicketError(
                f"task {task!r}: {field} must look like 'impl N, review N': {value!r}"
            )
        out[m.group(1)] = int(m.group(2))
    return out


def _format_roles(roles: dict[str, int]) -> str:
    return ", ".join(f"{r} {roles[r]}" for r in ROLES if r in roles)


def record_actuals(records: list[dict]) -> dict:
    """A task's measured frontmatter from its agents' records (agent_usage.aggregate):
    actual_tokens, actual_minutes when an agent is timed, and actual_roles and
    actual_role_tokens when any record names a role."""
    sums = agent_usage.aggregate(records)
    out = {"actual_tokens": str(sums["tokens"])}
    if sums["minutes"] is not None:
        out["actual_minutes"] = str(sums["minutes"])
    if sums["roles"]:
        out["actual_roles"] = _format_roles({r: m for r, (m, _) in sums["roles"].items()})
        out["actual_role_tokens"] = _format_roles({r: n for r, (_, n) in sums["roles"].items()})
    return out


def _number_problems(meta: dict, task: str) -> list[str]:
    """Every points, count and roles field of a task that is set but malformed."""
    checks = [(k, _points) for k in POINT_KEYS] + [(k, _count) for k in COUNT_KEYS]
    out = []
    for key, check in checks + [(k, _parse_roles) for k in ROLE_KEYS]:
        try:
            check(meta.get(key), task, key)
        except TicketError as e:
            out.append(str(e))
    return out


def calibration_rows(root: Path) -> list[dict]:
    """calibration rows: every done task with integer points and both actuals, plus its
    expected minutes and tokens and points_actual when they are well formed."""
    rows = []
    for t in scan(root):
        if t.kind != "task" or t.meta.get("status") != "done":
            continue
        if _number_problems(t.meta, t.slug):
            continue
        row = {k: _points(t.meta.get(k), t.slug, k) for k in POINT_KEYS}
        row.update({k: _count(t.meta.get(k), t.slug, k) for k in COUNT_KEYS})
        if None in (row["points"], row["actual_minutes"], row["actual_tokens"]):
            continue
        rows.append({k: v for k, v in row.items() if v is not None})
    return rows


def _point_fields(root: Path, points: int, task: str) -> dict:
    """`points` plus expected minutes and tokens from calibration."""
    n = _points(points, task, "points")
    minutes, tokens = calibration.expected(n, calibration_rows(root))
    return {"points": str(n), "expected_minutes": str(minutes), "expected_tokens": str(tokens)}


def cmd_new_task(a: argparse.Namespace) -> int:
    root = Path(a.root)
    require_main_checkout(root)
    epic_dir = resolve_epic(a.epic, root)
    if _phase_of(epic_dir) == "done":
        raise TicketError(f"epic {epic_dir.name!r} is in done; its tasks are closed")
    task = slug(a.title)
    if not task:
        raise TicketError("title has no usable characters")
    path = epic_dir / "tasks" / f"{task}.md"
    if path.exists():
        raise TicketError(f"task {task!r} already exists in epic {epic_dir.name!r}")
    worktree_name(epic_dir.name, task)
    numbers = _point_fields(root, a.points, task)
    files = _csv(a.files)
    if report(run_check(root, a.title, epic_dir.name, files)):
        return 1
    doc = _template("task.md")
    doc.meta.update(
        title=a.title,
        status="todo",
        repo=a.repo,
        value=a.value,
        files=files,
        verify=a.verify,
        depends_on=_csv(a.depends_on),
        model=a.model or "",
        review=a.review or "",
        **numbers,
    )
    body = _render(
        doc.body,
        {
            "title": a.title,
            "requirement": _read(a.requirement_file),
            "ac": _read(a.ac_file),
            "files": "\n".join(f"- `{f}`" for f in files),
        },
    )
    path.parent.mkdir(exist_ok=True)
    path.write_text(dump(Doc(doc.meta, body)))
    commit_ticket_change(epic_dir.name, f"new-task {task}", [path], root)
    print(path)
    return 0


def _counting_overlaps(root: Path, other: Ticket, shared: list[str]) -> list[str]:
    """Shared files that still count against `other`: none when it is done or merged into the
    base branch, and never a file matching the overlapIgnore globs of its repo."""
    if other.meta.get("status") == "done":
        return []
    try:
        globs = workbench.config_for_repo(root, other.meta.get("repo", ""))["overlapIgnore"]
    except workbench.ConfigError as e:
        raise TicketError(str(e)) from e
    left = [f for f in shared if not workbench.overlap_ignored(f, globs)]
    if not left:
        return []
    try:
        if _task_merged(_task_src(root, other.meta), other.meta.get("verified_head", ""), "main"):
            return []
    except (OSError, _mod().WorktreeError):
        pass  # no git checkout to ask (e.g. a bare plans dir): not merged
    return left


def cmd_index(a: argparse.Namespace) -> int:
    root = Path(a.root)
    rows = []
    for t in scan(root):
        m = t.meta
        rows.append(
            {
                "kind": t.kind,
                "slug": t.slug,
                "epic": t.epic,
                "title": m.get("title", ""),
                "phase": t.phase,
                "stage": m.get("stage", "") if t.kind == "epic" else "",
                "status": m.get("status", "") if t.kind == "task" else "",
                "files": m.get("files", []),
            }
        )
    out = root / "index.json"
    out.write_text(json.dumps(rows, indent=2) + "\n")
    print(out)
    return 0


def cmd_existing(a: argparse.Namespace) -> int:
    """Every file a done task built, with the first task that names it: what to reuse."""
    root = Path(a.root)
    seen: dict[str, str] = {}
    for t in scan(root):
        if t.kind != "task" or t.phase != "done":
            continue
        where = str(t.path.relative_to(root))
        for name in t.meta.get("files", []):
            seen.setdefault(name, where)
    print(json.dumps([{"name": n, "where": w} for n, w in seen.items()], indent=2))
    return 0


# ---------------------------------------------------------------- run: tasks, worktrees


def _sections(body: str) -> dict[str, str]:
    """'## Heading' sections of a task body, text stripped of surrounding blank lines."""
    parts = re.split(r"^## (.+?)\s*$", body, flags=re.M)
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}


def _template_sections() -> dict[str, str]:
    return _sections(_template("task.md").body)


def _parse_ac(text: str, task: str) -> list[dict]:
    out = []
    for line in filter(None, (ln.strip() for ln in text.splitlines())):
        m = AC_LINE.match(line)
        if not m or m.group(3) not in AC_KINDS:
            raise TicketError(
                f"task {task!r}: Acceptance conditions line is not "
                f"'- <id>: <text> [evidence: <kind>:<ref>]' with kind in "
                f"{', '.join(AC_KINDS)}: {line!r}"
            )
        out.append(
            {
                "id": m.group(1),
                "text": m.group(2),
                "evidence": {"kind": m.group(3), "ref": m.group(4) or ""},
            }
        )
    return out


def _task_files(epic_dir: Path) -> list[Path]:
    return sorted((epic_dir / "tasks").glob("*.md"))


def dependency_order(deps: dict[str, list[str]]) -> list[str]:
    """Task slugs with every dependency before its dependents, ties in slug order. A dependency
    outside `deps` does not constrain the order; a cycle is an error naming its tasks."""
    left = {k: {d for d in v if d in deps and d != k} for k, v in deps.items()}
    selfloops = sorted(k for k, v in deps.items() if k in v)
    out: list[str] = []
    while left and not selfloops:
        ready = sorted(k for k, v in left.items() if not v)
        if not ready:
            break
        for k in ready:
            out.append(k)
            del left[k]
        for v in left.values():
            v.difference_update(ready)
    if selfloops or left:
        raise TicketError(f"dependency cycle among tasks: {', '.join(selfloops or sorted(left))}")
    return out


def derive_tasks(epic_dir: Path, only: list[str] | None = None) -> list[dict]:
    """The epic's task list in dependency order, one entry per task file (or per `only` slug)."""
    placeholder = _template_sections()
    out = []
    files = _task_files(epic_dir)
    missing = sorted(set(only or []) - {p.stem for p in files})
    if missing:
        raise TicketError(f"no such task in {epic_dir.name!r}: {', '.join(missing)}")
    for path in files:
        if only and path.stem not in only:
            continue
        doc = _read_doc(path)
        sec = _sections(doc.body)
        for name in REQUIRED_SECTIONS:
            text = sec.get(name, "")
            if not text or text == placeholder.get(name):
                raise TicketError(f"task {path.stem!r} has an empty {name} section")
        m = doc.meta
        out.append(
            {
                "id": path.stem,
                "short": path.stem,
                "title": m.get("title", ""),
                "repo": m.get("repo", ""),
                "requirement": sec["Requirement"],
                "ac": _parse_ac(sec["Acceptance conditions"], path.stem),
                "value": m.get("value", ""),
                "files": m.get("files", []),
                "verify": m.get("verify", ""),
                "notes": sec.get("Notes", ""),
                "dependsOn": m.get("depends_on", []),
                "model": m.get("model", ""),
                "review": m.get("review", ""),
                "status": m.get("status", ""),
                "verifiedHead": m.get("verified_head", ""),
                "points": _points(m.get("points"), path.stem, "points"),
                **{k: _count(m.get(k), path.stem, k) for k in COUNT_KEYS[:2]},
            }
        )
    by_id = {x["id"]: x for x in out}
    graph = {p.stem: list(_read_doc(p).meta.get("depends_on", [])) for p in files}
    return [by_id[k] for k in dependency_order(graph) if k in by_id]


def cmd_tasks(a: argparse.Namespace) -> int:
    epic_dir = resolve_epic(a.epic, Path(a.root))
    text = json.dumps(derive_tasks(epic_dir, _csv(a.only)), indent=2)
    if a.out:
        Path(a.out).write_text(text + "\n")
    else:
        print(text)
    return 0


def _task_repo(root: Path, repo: str) -> str | None:
    """The task's repo when the docs root sits in a workbench with code/<repo>, else None."""
    if repo and (_workbench(root) / "code" / repo).is_dir():
        return repo
    return None


# ---------------------------------------------------------------- plan trees


def plan_branch(plan: str) -> str:
    """The branch and tree name of a plan: its slug."""
    return plan


def _submodule_branch(wb: Path, repo: str) -> str:
    r = _git(wb, "config", "--file", ".gitmodules", "--get", f"submodule.{repo}.branch")
    return r.stdout.strip() or "main"


def tree_layout(root: Path, plan_dir: Path) -> list[tuple[str, str]]:
    """(repo, base) per plan tree, from plan.md `repos`: ("", "main") in meta mode, else one
    per entry that is a code/<repo> checkout, based on its tracked branch. A plan naming both
    kinds is refused."""
    repos = list(read_plan(plan_dir).meta.get("repos") or [])
    wb = _workbench(root)
    comp = sorted(r for r in repos if r and (wb / "code" / r).is_dir())
    if not comp:
        return [("", "main")]
    if set(repos) - set(comp):
        raise TicketError(
            f"plan {plan_dir.name} mixes meta and component repos "
            f"({'; '.join(sorted(repos))}); split it into two plans"
        )
    return [(r, _submodule_branch(wb, r)) for r in comp]


def plan_trees(root: Path, plan_dir: Path) -> dict[str, Path]:
    """Plan tree path per repo ("" for the superrepo); the only place they are computed."""
    d = _mod().worktrees_dir(_workbench(root)) / plan_branch(plan_dir.name)
    return {r: (d / r if r else d) for r, _ in tree_layout(root, plan_dir)}


def ensure_plan_trees(root: Path, plan_dir: Path) -> list[dict]:
    """Create or reuse the plan's trees; one worktree-create integration() result per tree."""
    mod = _mod()
    out = []
    for repo, base in tree_layout(root, plan_dir):
        try:
            out.append(
                mod.integration(
                    plan_branch(plan_dir.name), base=base, repo=repo or None, start=root
                )
            )
        except mod.WorktreeError as e:
            raise TicketError(str(e)) from e
    return out


def cmd_worktrees(a: argparse.Namespace) -> int:
    """Create or reuse the trees of an in-progress plan."""
    root = Path(a.root)
    require_main_checkout(root)
    plan_dir = resolve_plan(a.plan, root)
    phase = phase_of(plan_dir)
    if phase != "in-progress":
        raise TicketError(f"plan {plan_dir.name!r} is in {phase}; worktrees needs it in-progress")
    for tree in ensure_plan_trees(root, plan_dir):
        print(f"tree {tree['path']} ({tree['verb']})")
        if a.refresh:
            base = a.base or tree["base"]
            print(f"refresh {tree['path']} {_mod().fast_forward(Path(tree['path']), base)}")
    return 0


def _section_replace(body: str, name: str, text: str) -> str:
    return re.sub(
        rf"(^## {re.escape(name)}[ \t]*\n).*?(?=^## |\Z)",
        lambda m: m.group(1) + "\n" + text + "\n\n",
        body,
        count=1,
        flags=re.M | re.S,
    )


# ---------------------------------------------------------------- epic state

VERDICT_RE = re.compile(r"^Verdict: (pass|fail) \(\d{4}-\d{2}-\d{2}\)$", re.M)


def _epics(root: Path) -> dict[str, Ticket]:
    return {t.slug: t for t in scan(root) if t.kind == "epic"}


def resolve_blocker(title: str, epics: dict[str, Ticket]) -> Ticket | None:
    """The epic a `blockers` entry names: by exact title, else by its slug."""
    for t in epics.values():
        if t.meta.get("title") == title:
            return t
    return epics.get(slug(title))


def _tasks_of(epic_dir: Path) -> list[tuple[Path, dict]]:
    return [(p, _read_doc(p).meta) for p in _task_files(epic_dir)]


def _undelivered(tasks: list[tuple[Path, dict]]) -> list[str]:
    out = []
    for p, m in tasks:
        status = m.get("status", "")
        if status != "done":
            out.append(f"task {p.stem!r} is {status or 'without a status'}, not done")
        elif not m.get("verified_head"):
            out.append(f"task {p.stem!r} is done without a verified_head")
    return out


def _update_readme(epic_dir: Path, **updates) -> tuple[Path, bool]:
    p = epic_dir / "README.md"
    doc = _read_doc(p)
    meta = dict(doc.meta)
    meta.update(updates)
    text = dump(Doc(meta, doc.body))
    changed = text != p.read_text()
    if changed:
        p.write_text(text)
    return p, changed


def _git_user(root: Path) -> str:
    r = _git(_existing(Path(root)), "config", "user.name")
    return r.stdout.strip() or os.environ.get("USER", "")


def _refuse(problems: list[str]) -> None:
    if problems:
        raise TicketError("; ".join(problems))


def last_verdict(readme_text: str) -> str | None:
    """The verdict of the last `Verdict:` line in the README's Review section, or None."""
    found = VERDICT_RE.findall(_sections(readme_text).get("Review", ""))
    return found[-1] if found else None


def _append_to_section(body: str, name: str, text: str) -> str:
    m = re.search(rf"^## {re.escape(name)}\s*$", body, re.M)
    if not m:
        return body.rstrip("\n") + f"\n\n## {name}\n\n{text}\n"
    nxt = re.search(r"^## ", body[m.end() :], re.M)
    end = m.end() + nxt.start() if nxt else len(body)
    head, tail = body[:end].rstrip("\n"), body[end:]
    return f"{head}\n\n{text}\n" + (f"\n{tail}" if tail else "")


def _move_in_progress(a: argparse.Namespace, root: Path, plan_dir: Path) -> int:
    """The claim: refused unless the plan is in todo with an agreed rung and an
    implementation-plan.md (the human gate passed); creates or reuses the plan trees, then
    moves the dir to in-progress and sets the owner."""
    name, phase = plan_dir.name, phase_of(plan_dir)
    if phase != "todo":
        raise TicketError(f"plan {name!r} is in {phase}; move in-progress needs it in todo")
    problems = []
    if not str(read_plan(plan_dir).meta.get("rung", "")).strip():
        problems.append(
            f"plan {name!r} has no agreed rung (plan.md rung is empty); the gate sets it"
        )
    if not (plan_dir / PATH_KINDS["implementation"]).is_file():
        problems.append(
            f"plan {name!r} has no implementation-plan.md; the plan-writer writes it after the gate"
        )
    _refuse(problems)
    if _in_git(root):
        for tree in ensure_plan_trees(root, plan_dir):
            print(f"tree {tree['path']} ({tree['verb']})")
    dest = _git_mv(plan_dir, "in-progress", root)
    update_plan_meta(dest, owner=a.owner or _git_user(root))
    commit_ticket_change(name, "move in-progress", [plan_dir, dest], root)
    print(dest)
    return 0


def _task_src(root: Path, m: dict) -> Path:
    """The checkout a task's branch lives in: code/<repo> in a workbench, else the repo itself."""
    repo = _task_repo(root, m.get("repo", ""))
    wb = _workbench(root)
    return wb / "code" / repo if repo else wb


def _branch_exists(src: Path, branch: str) -> bool:
    return (
        bool(branch)
        and _git(src, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}").returncode == 0
    )


def _task_merged(src: Path, verified_head: str, base: str) -> bool:
    """Whether the task's verified_head is contained in base (ancestry, else patch equivalence)."""
    return bool(verified_head) and _merge().contained(src, verified_head, base)[0]


def _trunk(wb: Path, repo: str, base: str) -> tuple[str, bool]:
    """(ref the integration branch must be in, whether to fetch it): the local base in meta
    mode, origin/<tracked branch> in component mode."""
    if not repo:
        return base, False
    return f"origin/{_submodule_branch(wb, repo)}", True


def _fetch_trunk(src: Path, target: str) -> None:
    _git(src, "fetch", "origin", target.split("/", 1)[1])


def _integration_problems(root: Path, epic_dir: Path, base: str) -> list[str]:
    """One line per integration branch that is not contained in its trunk."""
    wb, name = _workbench(root), epic_dir.name
    try:
        plan = tree_layout(root, epic_dir)
    except TicketError as e:
        return [str(e)]
    out = []
    for repo, _ in plan:
        src = wb / "code" / repo if repo else wb
        branch = plan_branch(name)
        if not _branch_exists(src, branch):
            continue
        target, fetch = _trunk(wb, repo, base)
        if fetch:
            _fetch_trunk(src, target)
        ok, why = _merge().contained(src, branch, target)
        if not ok:
            out.append(f"integration branch {branch!r} is not merged into {target!r}: {why}")
    return out


def review_gate(epic_dir: Path, action: str) -> None:
    """Refuse unless the epic is in-progress at stage review with a last verdict of pass; the
    gate `move done` and `close` share."""
    name, phase = epic_dir.name, _phase_of(epic_dir)
    if phase != "in-progress":
        raise TicketError(f"epic {name!r} is in {phase}; {action} needs it in-progress")
    readme = _read_doc(epic_dir / "README.md")
    stage = readme.meta.get("stage", "")
    if stage != "review":
        raise TicketError(f"epic {name!r} is at stage {stage!r}; {action} needs stage review")
    verdict = last_verdict(readme.body)
    if verdict is None:
        raise TicketError(f"epic {name!r} has no review verdict; run `review` first")
    if verdict != "pass":
        raise TicketError(f"epic {name!r}: the last review verdict is {verdict}, not pass")


def _move_done(a: argparse.Namespace, root: Path, epic_dir: Path) -> int:
    name = epic_dir.name
    review_gate(epic_dir, "move done")
    problems = _undelivered(_tasks_of(epic_dir))
    problems += _integration_problems(root, epic_dir, a.base)
    _refuse(problems)
    dest = _git_mv(epic_dir, "done", root)
    commit_ticket_change(name, "move done", [epic_dir, dest], root)
    sweep = Sweep(a.base, dry_run=False)
    try:
        sweep.epic(root, dest)
    except Exception as e:  # the move is committed; a sweep error must not undo or hide it
        print(
            f"ticket.py: epic {name!r} moved to done, but the worktree sweep failed: {e}",
            file=sys.stderr,
        )
        print(json.dumps(sweep.summary(), indent=2))
        return 1
    print(json.dumps(sweep.summary(), indent=2))
    return 0


def cmd_move(a: argparse.Namespace) -> int:
    root = Path(a.root)
    require_main_checkout(root)
    epic_dir = resolve_plan(a.plan, root)
    if a.phase == "in-progress":
        return _move_in_progress(a, root, epic_dir)
    return _move_done(a, root, epic_dir)


def cmd_stage(a: argparse.Namespace) -> int:
    root = Path(a.root)
    require_main_checkout(root)
    epic_dir = resolve_epic(a.epic, root)
    name, phase = epic_dir.name, _phase_of(epic_dir)
    if phase != "in-progress":
        raise TicketError(f"epic {name!r} is in {phase}; stage needs it in-progress")
    if a.stage == "review":
        tasks = _tasks_of(epic_dir)
        if not tasks:
            raise TicketError(f"epic {name!r} has no tasks to review")
        _refuse(_undelivered(tasks))
    readme, changed = _update_readme(epic_dir, stage=a.stage)
    if changed:
        commit_ticket_change(name, f"stage {a.stage}", [readme], root)
    print(f"{name}: stage {a.stage}")
    return 0


def cmd_review(a: argparse.Namespace) -> int:
    root = Path(a.root)
    require_main_checkout(root)
    epic_dir = resolve_epic(a.epic, root)
    name = epic_dir.name
    path = epic_dir / "README.md"
    doc = _read_doc(path)
    if _phase_of(epic_dir) != "in-progress" or doc.meta.get("stage") != "review":
        raise TicketError(
            f"epic {name!r} is not in-progress at stage review; run `stage {name} review` first"
        )
    notes = Path(a.notes_file).read_text().strip()
    if any(ln.startswith("Verdict:") for ln in notes.splitlines()):
        raise TicketError(
            "the notes must not contain a 'Verdict:' line; only the verdict "
            "line this command writes may start with it"
        )
    line = f"Verdict: {a.verdict} ({datetime.date.today().isoformat()})"
    entry = f"{line}\n\n{notes}" if notes else line
    path.write_text(dump(Doc(doc.meta, _append_to_section(doc.body, "Review", entry))))
    commit_ticket_change(name, f"review {a.verdict}", [path], root)
    print(line)
    return 0


# ---------------------------------------------------------------- cleanup and reap


def _merge_module():
    """worktree-merge's module: the one implementation of merged/dirty checks and cleanup."""
    p = Path(__file__).resolve().parents[2] / "worktree-merge" / "scripts" / "merge.py"
    spec = importlib.util.spec_from_file_location("worktree_merge", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_MERGE = None


def _merge():
    global _MERGE
    if _MERGE is None:
        _MERGE = _merge_module()
    return _MERGE


def _linked_worktrees(src: Path) -> set[Path]:
    """Every worktree registered in src's repository except its main working tree."""
    r = _git(src, "worktree", "list", "--porcelain")
    if r.returncode != 0:
        return set()
    paths = [Path(ln[9:]).resolve() for ln in r.stdout.splitlines() if ln.startswith("worktree ")]
    return set(paths[1:])


def _rmdir_if_empty(d: Path) -> None:
    if d.is_dir() and not any(d.iterdir()):
        d.rmdir()


class Sweep:
    """Removes merged, clean worktrees and their branches through merge.py cleanup(); everything
    else is listed with its reason."""

    def __init__(self, base: str, dry_run: bool) -> None:
        self.base, self.dry_run = base, dry_run
        self.removed: list[str] = []
        self.branches: list[str] = []
        self.left: list[dict] = []
        self.seen: set[Path] = set()

    def summary(self) -> dict:
        return {"removed": self.removed, "branches": self.branches, "left": self.left}

    def leave(self, wt: Path | str, reason: str) -> None:
        self.left.append({"path": str(wt), "reason": reason})

    def tree(self, wt: Path, src: Path, branch: str, target: str, fetch: bool = False) -> None:
        """One worktree: removed, with its branch, when clean and contained in target (ancestry,
        else patch equivalence); else left and listed with the reason."""
        if not wt.is_dir() or wt.resolve() in self.seen:
            return
        self.seen.add(wt.resolve())
        mm = _merge()
        if not (src / ".git").exists():
            return self.leave(wt, f"no source checkout at {src}")
        if wt.resolve() not in _linked_worktrees(src):
            return self.leave(wt, f"not a linked worktree of {src}")
        if mm.is_dirty(wt):
            return self.leave(wt, "dirty: uncommitted or untracked changes")
        if fetch:
            _fetch_trunk(src, target)
        ok, why = mm.contained(wt, "HEAD", target)
        if not ok:
            return self.leave(wt, f"unmerged: {why}")
        if _branch_exists(src, branch):
            ok, why = mm.contained(src, branch, target)
            if not ok:
                return self.leave(wt, f"unmerged: {why}")
        head = _git(wt, "symbolic-ref", "--quiet", "--short", "HEAD").stdout.strip() or branch
        if self.dry_run:
            self.removed.append(str(wt))
            if _branch_exists(src, head):
                self.branches.append(head)
            return None
        notes = mm.cleanup(src, wt, head, merged_into_ref=target)
        if wt.exists():
            return self.leave(wt, "; ".join(notes))
        self.removed.append(str(wt))
        for n in notes:
            if n.startswith("deleted branch "):
                self.branches.append(n[len("deleted branch ") :])
            elif n.startswith("branch ") and " kept " in n:
                self.leave(wt, f"worktree removed, {n}")
        return None

    def branch_only(self, src: Path, branch: str, target: str, fetch: bool = False) -> None:
        """A branch whose tree is already gone: deleted when contained in target, else listed."""
        if not _branch_exists(src, branch):
            return
        if fetch:
            _fetch_trunk(src, target)
        ok, why = _merge().contained(src, branch, target)
        if not ok:
            return self.leave(f"{src} (branch {branch})", f"unmerged: {why}")
        if self.dry_run:
            if branch not in self.branches:
                self.branches.append(branch)
            return None
        note = _merge().delete_if_merged(src, branch, target)
        if note.startswith("deleted branch "):
            self.branches.append(branch)
        else:
            self.leave(f"{src} (branch {branch})", note)
        return None

    def container(
        self, d: Path, branch: str, wb: Path, src: Path, target: str | None = None
    ) -> None:
        """A <config dir>/worktrees/<name> entry: a worktree of src itself, or a component-mode
        directory holding one worktree per code/<repo>."""
        target = target or self.base
        if (d / ".git").exists():
            self.tree(d, src, branch, target)
            return
        for sub in sorted(p for p in d.iterdir() if p.is_dir()):
            self.tree(sub, wb / "code" / sub.name, branch, target)
        if not self.dry_run:
            _rmdir_if_empty(d)

    def integration(self, d: Path, epic: str, wb: Path) -> None:
        """An integration entry (<config dir>/worktrees/<epic> or legacy .worktrees/<epic>):
        the meta tree itself or one tree per repo, each judged against its trunk."""
        if (d / ".git").exists():
            self.tree(d, wb, epic, self.base)
            return
        for sub in sorted(p for p in d.iterdir() if p.is_dir()):
            target, fetch = _trunk(wb, sub.name, self.base)
            self.tree(sub, wb / "code" / sub.name, epic, target, fetch)
        if not self.dry_run:
            _rmdir_if_empty(d)

    def epic(self, root: Path, epic_dir: Path) -> None:
        """The epic's integration trees at <config dir>/worktrees/<epic>[/<repo>] and legacy
        .worktrees/<epic>/<repo>, then its integration branches (target: the trunk)."""
        wb = _workbench(root)
        name = epic_dir.name
        for d in (workbench.worktrees_dir(wb) / plan_branch(name), wb / ".worktrees" / name):
            if d.is_dir():
                self.integration(d, name, wb)
        try:
            plan = tree_layout(root, epic_dir)
        except TicketError:
            return
        for repo, _ in plan:
            target, fetch = _trunk(wb, repo, self.base)
            self.branch_only(wb / "code" / repo if repo else wb, plan_branch(name), target, fetch)


def cmd_reap(a: argparse.Namespace) -> int:
    root = Path(a.root)
    if not a.dry_run:
        require_main_checkout(root)
    sweep = Sweep(a.base, a.dry_run)
    if a.epic:
        epic_dir = resolve_epic(a.epic, root)
        if _phase_of(epic_dir) != "done":
            raise TicketError(f"reap: epic {epic_dir.name} is not done (in {_phase_of(epic_dir)}/)")
        sweep.epic(root, epic_dir)
        print(json.dumps({"dryRun": a.dry_run, **sweep.summary()}, indent=2))
        return 0
    epics = _epics(root)
    for t in epics.values():
        if t.phase == "done":
            sweep.epic(root, t.path.parent)
    wb = _workbench(root)
    names = ticket_names(root)
    wt_dir = workbench.worktrees_dir(wb)
    for d in sorted(p for p in wt_dir.iterdir() if p.is_dir()) if wt_dir.is_dir() else []:
        owner = names.get(d.name)
        if owner:
            stale = epics[owner[0]].phase != "in-progress"
        else:
            legacy_epic, sep, _ = d.name.partition(LEGACY_SEP)
            stale = bool(sep) and not (
                legacy_epic in epics and epics[legacy_epic].phase == "in-progress"
            )
        if not stale:
            continue
        sweep.container(d, d.name, wb, wb)
    print(json.dumps({"dryRun": a.dry_run, **sweep.summary()}, indent=2))
    return 0


# ---------------------------------------------------------------- lint


def _task_problems(t: Ticket, placeholder: dict[str, str]) -> list[str]:
    """What a task file lacks (a Requirement, an acceptance condition, verify, files, points)
    and its malformed points, counts and roles."""
    sec = _sections(t.body)
    out = []
    req = sec.get("Requirement", "")
    if not req or req == placeholder.get("Requirement"):
        out.append(f"task {t.slug!r} has an empty Requirement")
    try:
        if not _parse_ac(sec.get("Acceptance conditions", ""), t.slug):
            out.append(f"task {t.slug!r} has no acceptance condition")
    except TicketError as e:
        out.append(str(e))
    for key in ("verify", "files", "points"):
        if not t.meta.get(key):
            out.append(f"task {t.slug!r} has no {key}")
    return out + _number_problems(t.meta, t.slug)


def _coverage_problems(design: Path, slugs: set[str]) -> list[str]:
    """Every `### D<n>` of design.md maps to existing task slugs in its Decision coverage."""
    text = design.read_text()
    rows: dict[str, list[str]] = {}
    for line in _sections(text).get("Decision coverage", "").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        m = re.match(r"(D\d+)\b", cells[0])
        if m and len(cells) > 1:
            rows[m.group(1)] = [x.strip(" `") for x in cells[1].split(",") if x.strip(" `")]
    out = []
    for d in re.findall(r"^### (D\d+)\b", text, re.M):
        if d not in rows:
            out.append(f"design.md Decision coverage has no row for {d}")
        elif not rows[d]:
            out.append(f"design.md Decision coverage maps {d} to no task")
        out += [
            f"design.md Decision coverage maps {d} to unknown task {x!r}"
            for x in rows.get(d, [])
            if x not in slugs
        ]
    return out


def lint_problems(root: Path, only: str | None = None) -> list[str]:
    """Invariant breaks across every epic, or only `only`."""
    placeholder = _template_sections()
    tickets = scan(root)
    epics = {t.slug: t for t in tickets if t.kind == "epic"}
    out = []
    for e in epics.values():
        if only and e.slug != only:
            continue
        where = f"epic {e.slug!r} ({e.phase})"
        stage = e.meta.get("stage", "build")
        if stage not in EPIC_STAGES:
            out.append(f"{where}: stage {stage!r} is not one of {', '.join(EPIC_STAGES)}")
        if stage == "review" and e.phase == "todo":
            out.append(f"{where}: stage review before the epic left todo")
        for b in e.meta.get("blockers", []):
            if resolve_blocker(b, epics) is None:
                out.append(f"{where}: blocker {b!r} names no epic")
        tasks = [t for t in tickets if t.kind == "task" and t.epic == e.slug]
        slugs = {t.slug for t in tasks}
        for t in tasks:
            status = t.meta.get("status", "")
            if status not in TASK_STATUSES:
                out.append(
                    f"{where}: task {t.slug!r} status {status!r} is not one of "
                    f"{', '.join(TASK_STATUSES)}"
                )
            if e.phase == "todo" and status != "todo":
                out.append(f"{where}: todo epic has task {t.slug!r} with status {status!r}")
            if e.phase == "done" and status != "done":
                out.append(f"{where}: done epic has task {t.slug!r} with status {status!r}")
            if stage == "review" and e.phase != "done" and status != "done":
                out.append(f"{where}: stage review with open task {t.slug!r} ({status!r})")
            for d in t.meta.get("depends_on", []):
                if d not in slugs:
                    out.append(f"{where}: task {t.slug!r} depends_on unknown task {d!r}")
            # a done epic is history: only `ticket.py migrate` rewrites its task files
            if e.phase != "done":
                out += [f"{where}: {p}" for p in _task_problems(t, placeholder)]
        try:
            dependency_order({t.slug: list(t.meta.get("depends_on", [])) for t in tasks})
        except TicketError as cycle:
            out.append(f"{where}: {cycle}")
        design = e.path.parent / "design.md"
        if e.phase != "done" and design.is_file():
            out += [f"{where}: {p}" for p in _coverage_problems(design, slugs)]
    return out


def cmd_lint(a: argparse.Namespace) -> int:
    root = Path(a.root)
    only = resolve_epic(a.epic, root).name if a.epic else None
    problems = lint_problems(root, only)
    for p in problems:
        print(f"ticket.py: lint: {p}", file=sys.stderr)
    if not problems:
        print("lint: ok")
    return 1 if problems else 0


CMD_DIR = Path(__file__).resolve().parent / "ticket_cmds"


class _ModuleSub:
    """Subparsers facade for a command module: adds --root, rejects name clashes."""

    def __init__(self, sub, owners: dict[str, str], module: str) -> None:
        self._sub, self._owners, self._module = sub, owners, module

    def add_parser(self, name: str, root: bool = True, **kw) -> argparse.ArgumentParser:
        if name in self._owners:
            raise TicketError(
                f"subcommand {name!r} of module {self._module!r} clashes with {self._owners[name]}"
            )
        self._owners[name] = f"module {self._module!r}"
        sp = self._sub.add_parser(name, **kw)
        if root:
            sp.add_argument("--root", default=None, help="plans root (default: git top/docs/plans)")
        return sp

    def __getattr__(self, attr: str):
        return getattr(self._sub, attr)


def _load_cmd_modules(sub, cmd_dir: Path) -> None:
    owners = {n: "built-in" for n in sub.choices}
    me = sys.modules[__name__]
    for path in sorted(cmd_dir.glob("*.py"), key=lambda p: p.name):
        if path.name == "__init__.py":
            continue
        spec = importlib.util.spec_from_file_location(f"ticket_cmds.{path.stem}", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if not hasattr(mod, "register"):
            raise TicketError(f"{path}: command module has no register(sub, t)")
        mod.register(_ModuleSub(sub, owners, path.stem), me)


def build_parser(cmd_dir: Path | None = None) -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="ticket.py", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name: str, fn, root: bool = True) -> argparse.ArgumentParser:
        sp = sub.add_parser(name)
        sp.set_defaults(fn=fn)
        if root:
            sp.add_argument("--root", default=None, help="plans root (default: git top/docs/plans)")
        return sp

    sp = add("slug", cmd_slug, root=False)
    sp.add_argument("title")
    sp = add("new", cmd_new)
    sp.add_argument("--title", required=True)
    sp.add_argument("--repos", help="comma-separated repos the plan touches")
    sp.add_argument(
        "--force",
        action="store_true",
        help="create even when a live (todo/in-progress) plan is a near duplicate",
    )
    sp = add("new-task", cmd_new_task)
    for opt in ("epic", "title", "repo", "value", "files", "verify"):
        sp.add_argument(f"--{opt}", required=True)
    for opt in ("depends-on", "model", "review", "requirement-file", "ac-file"):
        sp.add_argument(f"--{opt}")
    sp.add_argument(
        "--points",
        required=True,
        type=int,
        help="Fibonacci storypoints (1, 2, 3, 5, 8, 13); fills expected_minutes and "
        "expected_tokens from calibration",
    )
    sp = add("check", cmd_check)
    sp.add_argument("--title", required=True)
    add("index", cmd_index)
    add("existing", cmd_existing)
    sp = add("tasks", cmd_tasks)
    sp.add_argument("epic")
    sp.add_argument("--only", help="comma-separated task slugs; others are not validated")
    sp.add_argument("--out", help="write the JSON to this file instead of stdout")
    sp = add("worktrees", cmd_worktrees)
    sp.add_argument("plan")
    sp.add_argument("--base", default=None, help="--refresh target (default: each tree's trunk)")
    sp.add_argument(
        "--refresh",
        action="store_true",
        help="fast-forward each clean plan tree with nothing ahead of --base",
    )
    sp = add("move", cmd_move)
    sp.add_argument("plan")
    sp.add_argument("phase", choices=("in-progress", "done"))
    sp.add_argument("--owner", help="who claims the plan (default: git user.name)")
    sp.add_argument("--base", default="main", help="branch the epic branch must be merged into")
    sp = add("stage", cmd_stage)
    sp.add_argument("epic")
    sp.add_argument("stage", choices=EPIC_STAGES)
    sp = add("review", cmd_review)
    sp.add_argument("epic")
    sp.add_argument("--verdict", required=True, choices=("pass", "fail"))
    sp.add_argument("--notes-file", required=True)
    sp = add("rename", cmd_rename)
    sp.add_argument("plan")
    sp.add_argument("title")
    sp = add("lint", cmd_lint)
    sp.add_argument("epic", nargs="?")
    sp = add("reap", cmd_reap)
    sp.add_argument("--dry-run", action="store_true", help="list what would go, remove nothing")
    sp.add_argument("--base", default="main")
    sp.add_argument("--epic", help="reap only this done epic's integration trees")
    sp = add("path", cmd_path)
    sp.add_argument("plan")
    sp.add_argument("kind", choices=sorted(PATH_KINDS))
    _load_cmd_modules(sub, cmd_dir or CMD_DIR)
    return ap


def main(argv: list[str] | None = None) -> int:
    try:
        a = build_parser().parse_args(argv)
        if hasattr(a, "root"):
            a.root = str(Path(a.root).resolve()) if a.root else str(default_root())
        return a.fn(a)
    except TicketError as e:
        print(f"ticket.py: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
