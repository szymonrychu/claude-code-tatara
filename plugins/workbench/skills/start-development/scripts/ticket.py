#!/usr/bin/env python3
"""ticket.py: file-based epic and task tickets under docs/plans/{todo,in-progress,done}.

Core: layout, slugs, restricted frontmatter, new-epic, new-task, path. Dedup: check, index,
existing. Run: tasks, worktrees, apply-run. Epic state: move, stage, review, rename, lint, reap.
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
TASK_STATUSES = ("todo", "in-progress", "done", "blocked", "escalated")
EPIC_STAGES = ("build", "review")
SLUG_MAX = 28
WORKTREE_MAX = SLUG_MAX + 1 + SLUG_MAX
LEGACY_SEP = "--"  # separator of pre-existing <epic>--<task> tree names, matched by reap-all only
NEAR_DUP = 0.6
LEGACY_SEP = "--"  # the old `<epic>--<task>` tree and branch separator, still swept on disk
EXIT_NEAR_DUPLICATE = 3  # new-epic stopped on a live near-duplicate epic; --force overrides
TEMPLATES = Path(__file__).resolve().parents[1] / "templates"
AC_KINDS = ("test", "symbol", "command", "doc-section", "judgement")
AC_LINE = re.compile(r"^- (\S+?): (.+?) \[evidence: ([a-z-]+)(?::\s*(.*?))?\]$")
REQUIRED_SECTIONS = ("Requirement", "Acceptance conditions", "Files", "Steps")
PATH_KINDS = {
    "readme": "README.md",
    "design": "design.md",
    "approvals": "approvals.json",
    "record": "record.md",
    "tasks": "tasks",
}


class TicketError(Exception):
    pass


# ---------------------------------------------------------------- slugs and names


def slug(title: str) -> str:
    return slugify(title, SLUG_MAX)


def worktree_name(epic: str, task: str) -> str:
    name = f"{epic}-{task}"
    if len(name) > WORKTREE_MAX:
        raise TicketError(f"worktree name {name!r} is {len(name)} characters, max {WORKTREE_MAX}")
    return name


# ---------------------------------------------------------------- branch-name collisions


def ticket_names(root: Path) -> dict[str, tuple[str, str | None]]:
    """Every epic slug -> (epic, None) and every `<epic>-<task>` -> (epic, task), all phases.
    `<epic>-<task>` cannot be split back into its parts, so this is the one name-to-ticket map."""
    names: dict[str, tuple[str, str | None]] = {}
    for t in scan(Path(root)):
        if t.kind == "epic":
            names[t.slug] = (t.slug, None)
        else:
            names[f"{t.epic}-{t.slug}"] = (t.epic, t.slug)
    return names


def _disk_names(root: Path) -> dict[str, str]:
    """Names taken on disk -> what holds them: local branches of the source checkouts and
    directories under <configdir>/worktrees/. Empty outside a git checkout."""
    try:
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
            found[d.name] = f"tree {d.name}"
        return found
    except Exception:  # not in a git checkout: nothing on disk to collide with
        return {}


def name_clashes(
    root: Path, wanted: list[tuple[str, str | None, str | None]], own_epic: str | None = None
) -> list[str]:
    """Failure lines for names that would clash. `wanted` is (name, epic, task): task None means
    the name is an epic slug. Tickets of `own_epic` are skipped (a rename frees its old names)."""
    taken = {n: v for n, v in ticket_names(root).items() if own_epic is None or v[0] != own_epic}
    disk = _disk_names(root)
    out: list[str] = []
    for name, epic, task in wanted:
        what = f"epic slug {name}" if task is None else f"task branch {name}"
        hit = taken.get(name)
        if hit is not None:
            other = hit[1]
            if task is None and other is None:
                continue  # an equal epic slug is reported as "already exists"
            if task is not None and other is not None and hit[0] == epic:
                continue  # the same task slug in the same epic is reported as "already exists"
            if other is None:
                out.append(f"{what} collides with epic slug {name}")
            else:
                out.append(f"{what} collides with the branch of task {other} in epic {hit[0]}")
        elif name in disk:
            out.append(f"{what} collides with existing {disk[name]}")
        if task is not None:
            legacy = LEGACY_SEP.join((epic or "", task))
            if legacy in disk:
                out.append(
                    f"task branch {name} would be swept with legacy {disk[legacy]} "
                    f"(old {legacy} name)"
                )
    return out


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


# ---------------------------------------------------------------- layout


def default_root() -> Path:
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    top = Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else Path.cwd()
    return top / "docs" / "plans"


def find_epic(slug_: str, root: Path) -> Path | None:
    for phase in PHASES:
        d = root / phase / slug_
        if d.is_dir():
            return d
    return None


def resolve_epic(arg: str, root: Path) -> Path:
    """An epic slug or an epic directory path, to the epic directory."""
    p = Path(arg)
    if (p.parent != Path(".") or arg.startswith(".")) and p.is_dir():
        resolved = p.resolve()
        if not resolved.is_relative_to(root.resolve()):
            raise TicketError(f"epic path {arg!r} is outside the plans root {root}")
        return resolved
    found = find_epic(arg, root)
    if found is None:
        raise TicketError(f"unknown epic {arg!r} under {root}")
    return found.resolve()


def _phase_of(epic_dir: Path) -> str:
    return epic_dir.parent.name


# ---------------------------------------------------------------- git guard and commit


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def _existing(p: Path) -> Path:
    p = p.resolve()
    while not p.exists():
        p = p.parent
    return p


def require_main_checkout(root: Path) -> None:
    cwd = _existing(Path(root))
    g = _git(cwd, "rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir")
    if g.returncode != 0:
        return
    git_dir, common = g.stdout.split("\n")[:2]
    if Path(git_dir).resolve() != Path(common).resolve():
        raise TicketError("run in the main checkout, not a linked worktree")


def commit_ticket_change(epic: str, event: str, paths: list[Path], root: Path) -> None:
    """Commit exactly `paths` (under root) as 'chore(ticket): <epic> <event>'; no-op outside git."""
    cwd = _existing(Path(root))
    if _git(cwd, "rev-parse", "--git-dir").returncode != 0:
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
    done = _git(cwd, "commit", "-m", f"chore(ticket): {epic} {event}", "--", *rel)
    if done.returncode != 0:
        raise TicketError(f"git commit failed: {(done.stderr or done.stdout).strip()}")


# ---------------------------------------------------------------- subcommands


def _csv(value: str | None) -> list[str]:
    return [x.strip() for x in (value or "").split(",") if x.strip()]


def _read(path: str | None) -> str:
    return Path(path).read_text().strip() if path else ""


def _render(body: str, values: dict[str, str]) -> str:
    for k, v in values.items():
        body = body.replace("{{" + k + "}}", v)
    return body


def _template(name: str) -> Doc:
    p = TEMPLATES / name
    return load(p.read_text(), p)


def cmd_new_epic(a: argparse.Namespace) -> int:
    root = Path(a.root)
    require_main_checkout(root)
    epic = slug(a.title)
    if not epic:
        raise TicketError("title has no usable characters")
    res = run_check(root, a.title, blockers=_csv(a.blockers), goals=_read(a.goals_file))
    if report(res):
        return 1
    if not a.force:
        for twin, phase, score in res.near_epics:
            if phase != "done":
                print(
                    f"new-epic: near duplicate {twin} ({score:.2f}); pass --force to create anyway",
                    file=sys.stderr,
                )
                return EXIT_NEAR_DUPLICATE
    doc = _template("epic.md")
    doc.meta.update(
        title=a.title,
        blockers=_csv(a.blockers),
        stage="build",
        owner="",
        repos=_csv(a.repos),
        created=datetime.date.today().isoformat(),
    )
    body = _render(
        doc.body,
        {
            "title": a.title,
            "what": a.what or "",
            "how": a.how or "",
            "why": a.why or "",
            "description": _read(a.description_file),
            "goals": _read(a.goals_file),
            "non_goals": _read(a.non_goals_file),
        },
    )
    readme = root / "todo" / epic / "README.md"
    readme.parent.mkdir(parents=True)
    readme.write_text(dump(Doc(doc.meta, body)))
    commit_ticket_change(epic, "new-epic", [readme], root)
    print(readme)
    return 0


def _estimate_arg(value: str | None) -> str:
    """The planner's `--estimate` minutes for a new task; unset stays empty."""
    return str(_minutes(value, "new task", "estimate")) if value else ""


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
    files = _csv(a.files)
    if report(run_check(root, a.title, epic_dir.name, files, _csv(a.owns))):
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
        owns=_csv(a.owns),
        uses=_csv(a.uses),
        model=a.model or "",
        estimate=_estimate_arg(a.estimate),
        review=a.review or "",
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


# ---------------------------------------------------------------- dedup: check, index, existing


class Ticket(NamedTuple):
    kind: str  # "epic" or "task"
    slug: str
    epic: str
    phase: str
    path: Path
    meta: dict
    body: str


def _read_doc(path: Path) -> Doc:
    return load(path.read_text(), path)


def scan(root: Path) -> list[Ticket]:
    """Every epic and task under root, all phases, in phase then slug order."""
    out: list[Ticket] = []
    for phase in PHASES:
        base = Path(root) / phase
        if not base.is_dir():
            continue
        for d in sorted(p for p in base.iterdir() if p.is_dir()):
            readme = d / "README.md"
            doc = _read_doc(readme) if readme.exists() else Doc({}, "")
            out.append(Ticket("epic", d.name, d.name, phase, readme, doc.meta, doc.body))
            for tp in sorted((d / "tasks").glob("*.md")):
                doc = _read_doc(tp)
                out.append(Ticket("task", tp.stem, d.name, phase, tp, doc.meta, doc.body))
    return out


def ticket_names(root: Path) -> dict[str, tuple[str, str | None]]:
    """Every tree or branch name a ticket owns: `<epic>` -> (epic, None) and
    `<epic>-<task>` -> (epic, task). `<epic>-<task>` cannot be split, so this lookup is the
    only way code maps a name back to a ticket."""
    out: dict[str, tuple[str, str | None]] = {}
    for t in scan(root):
        if t.kind == "epic":
            out[t.slug] = (t.slug, None)
            continue
        try:
            out[worktree_name(t.epic, t.slug)] = (t.epic, t.slug)
        except TicketError:
            continue  # too long to ever be created as a tree
    return out


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _norm(title: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", title.lower()))


def _goals(body: str) -> str:
    m = re.search(r"^## Goals\s*\n(.*?)(?=^## |\Z)", body, re.M | re.S)
    return m.group(1) if m else ""


def _similarity(title_a: str, text_a: str, title_b: str, text_b: str) -> float:
    ratio = difflib.SequenceMatcher(None, _norm(title_a), _norm(title_b)).ratio()
    wa, wb = _words(title_a + " " + text_a), _words(title_b + " " + text_b)
    jac = len(wa & wb) / len(wa | wb) if wa | wb else 0.0
    return max(ratio, jac)


def _extra_text(t: Ticket) -> str:
    return _goals(t.body) if t.kind == "epic" else str(t.meta.get("value", ""))


def _live_worktrees(root: Path) -> list[str]:
    r = _git(_existing(Path(root)), "worktree", "list", "--porcelain")
    if r.returncode != 0:
        return []
    return [Path(line[9:]).name for line in r.stdout.splitlines() if line.startswith("worktree ")]


def _tree_live(wt: str) -> bool:
    """True when `wt` is a live git worktree, whichever repo (docs root or code/<repo>) owns it."""
    path = Path(wt)
    return path.is_dir() and path.name in _live_worktrees(path)


class CheckResult(NamedTuple):
    failures: list[str]
    warnings: list[str]
    notes: list[str]
    near_epics: list[tuple[str, str, float]]  # (slug, phase, score), new-epic only


def _blocker_slug(name: str, epics: dict[str, Ticket]) -> str:
    found = resolve_blocker(name, epics)
    return found.slug if found else name


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
    branch = other.meta.get("branch") or worktree_name(other.epic, other.slug)
    try:
        if _task_merged(
            _task_src(root, other.meta), branch, other.meta.get("verified_head", ""), "main"
        ):
            return []
    except (OSError, _mod().WorktreeError):
        pass  # no git checkout to ask (e.g. a bare plans dir): not merged
    return left


def run_check(
    root: Path,
    title: str | None = None,
    epic: str | None = None,
    files: list[str] | None = None,
    owns: list[str] | None = None,
    blockers: list[str] | None = None,
    goals: str = "",
) -> CheckResult:
    """Dedup rules. `epic` None with a title is a new epic; with an epic, a title is a new task
    and no title checks every task of that epic."""
    root = Path(root)
    fails: list[str] = []
    warns: list[str] = []
    notes: list[str] = []
    near_epics: list[tuple[str, str, float]] = []
    tickets = scan(root)
    epics = {t.slug: t for t in tickets if t.kind == "epic"}
    if epic is not None and epic not in epics:
        raise TicketError(f"unknown epic {epic!r} under {root}")
    named = set(blockers or [])
    if epic is not None:
        named |= set(epics[epic].meta.get("blockers", []))
    own_blockers = {_blocker_slug(b, epics) for b in named}

    def candidates() -> list[tuple[list[str], list[str], str]]:
        """(files, owns, label) to run the files and owns checks on."""
        if title is not None:
            return [(files or [], owns or [], f"task {slug(title)!r}")]
        return [
            (list(t.meta.get("files", [])), list(t.meta.get("owns", [])), f"task {t.slug!r}")
            for t in tickets
            if t.kind == "task" and t.epic == epic
        ]

    if title is not None:
        new_slug = slug(title)
        if epic is None:
            for t in tickets:
                if t.kind == "epic" and t.slug == new_slug:
                    fails.append(f"epic slug {new_slug!r} already exists in {t.phase}")
        else:
            for t in tickets:
                if t.kind == "task" and t.epic == epic and t.slug == new_slug:
                    fails.append(f"task slug {new_slug!r} already exists in epic {epic!r}")
        if epic is None:
            fails += name_clashes(root, [(new_slug, None, None)])
        else:
            fails += name_clashes(root, [(f"{epic}-{new_slug}", epic, new_slug)])
        kind = "epic" if epic is None else "task"
        extra = goals if epic is None else ""
        for t in tickets:
            if t.kind != kind or (t.slug == new_slug and (kind == "epic" or t.epic == epic)):
                continue
            other = str(t.meta.get("title", t.slug))
            score = _similarity(title, extra, other, _extra_text(t))
            if score >= NEAR_DUP:
                if kind == "epic":
                    near_epics.append((t.slug, t.phase, score))
                where = t.slug if kind == "epic" else f"{t.epic}/{t.slug}"
                notes.append(
                    f"near-duplicate {kind} {where} ({t.phase}): {t.meta.get('title', t.slug)!r}"
                )

    if epic is not None:
        for tfiles, towns, label in candidates():
            for t in tickets:
                if t.kind != "task" or t.epic == epic or t.epic in own_blockers:
                    continue
                shared = sorted(set(tfiles) & set(t.meta.get("files", [])))
                if t.phase == "in-progress" and shared:
                    for f in _counting_overlaps(root, t, shared):
                        fails.append(
                            f"{label}: file {f!r} is also in task {t.slug!r} of "
                            f"in-progress epic {t.epic!r}"
                        )
                for part in towns:
                    if part not in t.meta.get("owns", []):
                        continue
                    if t.phase == "done":
                        notes.append(
                            f"existing: {part!r} is owned by done epic {t.epic!r} "
                            f"(task {t.slug!r}); reuse it"
                        )
                    else:
                        fails.append(
                            f"{label}: part {part!r} is owned by task {t.slug!r} of "
                            f"{t.phase} epic {t.epic!r}"
                        )

    names = ticket_names(root)
    for name in _live_worktrees(root):
        owner = names.get(name)
        if owner and epics[owner[0]].phase != "in-progress":
            warns.append(
                f"warning: live worktree {name!r} belongs to epic {owner[0]!r} "
                f"which is in {epics[owner[0]].phase}, not in-progress"
            )
    return CheckResult(fails, warns, notes, near_epics)


def report(res: CheckResult) -> int:
    for n in res.notes:
        print(n)
    for w in res.warnings:
        print(w, file=sys.stderr)
    for f in res.failures:
        print(f"ticket.py: {f}", file=sys.stderr)
    return 1 if res.failures else 0


def cmd_check(a: argparse.Namespace) -> int:
    if a.title is None and a.epic is None:
        raise TicketError("check needs --title (new epic) or --epic (new task, or all tasks)")
    return report(
        run_check(
            Path(a.root),
            a.title,
            a.epic,
            _csv(a.files),
            _csv(a.owns),
            _csv(a.blockers),
            _read(a.goals_file),
        )
    )


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
                "owns": m.get("owns", []),
                "provides": m.get("provides", []),
            }
        )
    out = root / "index.json"
    out.write_text(json.dumps(rows, indent=2) + "\n")
    print(out)
    return 0


def cmd_existing(a: argparse.Namespace) -> int:
    root = Path(a.root)
    seen: dict[str, str] = {}
    for t in scan(root):
        if t.kind != "task" or t.phase != "done":
            continue
        where = str(t.path.relative_to(root))
        for name in [*t.meta.get("owns", []), *t.meta.get("provides", [])]:
            seen.setdefault(name, where)
    print(json.dumps([{"name": n, "where": w} for n, w in seen.items()], indent=2))
    return 0


# ---------------------------------------------------------------- run: tasks, worktrees, apply-run


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


def _minutes(value, task: str, field: str) -> int:
    """A task's `estimate` or `actual` frontmatter value in minutes; unset is 0."""
    if value in (None, ""):
        return 0
    try:
        n = int(value)
    except (TypeError, ValueError):
        n = -1
    if n < 0:
        raise TicketError(f"task {task!r}: {field} must be a whole number of minutes: {value!r}")
    return n


def time_summary(epic_dir: Path) -> str:
    """Sum of estimates, sum of actuals and remaining estimate (tasks not done), in minutes."""
    rows = [(p.stem, m) for p, m in _tasks_of(epic_dir)]
    est = sum(_minutes(m.get("estimate"), s, "estimate") for s, m in rows)
    act = sum(_minutes(m.get("actual"), s, "actual") for s, m in rows)
    left = sum(
        _minutes(m.get("estimate"), s, "estimate") for s, m in rows if m.get("status") != "done"
    )
    return f"Estimate: {est} min | Actual: {act} min | Remaining estimate: {left} min"


def update_time_section(epic_dir: Path) -> tuple[Path, bool]:
    """Regenerate the derived `## Time` section of the epic README; (path, changed)."""
    p = epic_dir / "README.md"
    doc = _read_doc(p)
    text = time_summary(epic_dir)
    if re.search(r"^## Time\s*$", doc.body, flags=re.M):
        body = _section_replace(doc.body, "Time", text)
    else:
        body = doc.body.rstrip("\n") + f"\n\n## Time\n\n{text}\n"
    changed = body != doc.body
    if changed:
        p.write_text(dump(Doc(doc.meta, body)))
    return p, changed


def derive_tasks(epic_dir: Path, only: list[str] | None = None) -> list[dict]:
    """The plan-execute task list for an epic, one entry per task file (or per `only` slug)."""
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
                "owns": m.get("owns", []),
                "uses": m.get("uses", []),
                "dependsOn": m.get("depends_on", []),
                "model": m.get("model", ""),
                "review": m.get("review", ""),
                "worktree": m.get("worktree", ""),
                "acsForAudit": m.get("acs_for_audit", []),
                "estimate": _minutes(m.get("estimate"), path.stem, "estimate"),
                "actual": _minutes(m.get("actual"), path.stem, "actual"),
                "branch": m.get("branch", ""),
                "verifiedHead": m.get("verified_head", ""),
            }
        )
    return out


def cmd_tasks(a: argparse.Namespace) -> int:
    epic_dir = resolve_epic(a.epic, Path(a.root))
    text = json.dumps(derive_tasks(epic_dir, _csv(a.only)), indent=2)
    if (epic_dir / "README.md").is_file():
        update_time_section(epic_dir)
    if a.out:
        Path(a.out).write_text(text + "\n")
    else:
        print(text)
    return 0


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


def _create():
    return _mod().create


def _workbench(root: Path) -> Path:
    return _mod().workbench_root(_existing(Path(root)))


def _task_repo(root: Path, repo: str) -> str | None:
    """The task's repo when the docs root sits in a workbench with code/<repo>, else None."""
    if repo and (_workbench(root) / "code" / repo).is_dir():
        return repo
    return None


def integration_branch(epic: str) -> str:
    """The integration branch and tree name of an epic: its slug."""
    return epic


def _submodule_branch(wb: Path, repo: str) -> str:
    r = _git(wb, "config", "--file", ".gitmodules", "--get", f"submodule.{repo}.branch")
    return r.stdout.strip() or "main"


def _integration_plan(root: Path, epic_dir: Path) -> list[tuple[str, str]]:
    """(repo, base) per integration tree: ("", main) in meta mode, else one per submodule."""
    scope = _read_doc(epic_dir / "README.md").meta.get("repos") or []
    task_repos = [doc.meta.get("repo", "") for doc in map(_read_doc, _task_files(epic_dir))]
    comp = {r for r in scope if _task_repo(root, r)}
    outside = False
    for r in task_repos:
        if _task_repo(root, r):
            comp.add(r)
        else:
            outside = True
    if not comp:
        return [("", "main")]
    if outside:
        raise TicketError(
            f"epic {epic_dir.name} mixes meta and component tasks; split it into two epics"
        )
    wb = _workbench(root)
    return [(r, _submodule_branch(wb, r)) for r in sorted(comp)]


def integration_trees(root: Path, epic_dir: Path) -> dict[str, Path]:
    """Integration tree path per repo ("" for the superrepo); the only place they are computed."""
    d = _mod().worktrees_dir(_workbench(root)) / integration_branch(epic_dir.name)
    return {r: (d / r if r else d) for r, _ in _integration_plan(root, epic_dir)}


def ensure_integration_trees(root: Path, epic_dir: Path) -> list[dict]:
    """Create or reuse the epic's integration trees; one create.integration result per tree."""
    mod = _mod()
    out = []
    for repo, base in _integration_plan(root, epic_dir):
        try:
            out.append(
                mod.integration(
                    integration_branch(epic_dir.name), base=base, repo=repo or None, start=root
                )
            )
        except mod.WorktreeError as e:
            raise TicketError(str(e)) from e
    return out


def _write_task(path: Path, doc: Doc, changed: list[Path], **updates) -> None:
    """Rewrite the task with updated frontmatter; record it in `changed` only if it differs."""
    meta = dict(doc.meta)
    meta.update(updates)
    text = dump(Doc(meta, doc.body))
    if text != path.read_text():
        path.write_text(text)
        changed.append(path)


def _require_integration_branch(root: Path, meta: dict, base: str, epic: str) -> None:
    """Exit 1 naming the upgrade command when the epic branch is missing in the task's checkout."""
    if base != integration_branch(epic):
        return
    src = _task_src(root, meta)
    if not _branch_exists(src, base):
        raise TicketError(
            f"integration branch {base} missing in {src}; "
            f"run ticket.py worktrees {epic} --integration"
        )


def _worktrees_integration(root: Path, epic_dir: Path) -> int:
    """Create or reuse the integration trees of an in-progress epic; no task tree."""
    phase = _phase_of(epic_dir)
    if phase != "in-progress":
        raise TicketError(
            f"epic {epic_dir.name!r} is in {phase}; worktrees --integration needs it in-progress"
        )
    for tree in ensure_integration_trees(root, epic_dir):
        print(f"integration {tree['path']} ({tree['verb']})")
    return 0


def cmd_worktrees(a: argparse.Namespace) -> int:
    root = Path(a.root)
    require_main_checkout(root)
    epic_dir = resolve_epic(a.epic, root)
    if getattr(a, "integration", False):
        return _worktrees_integration(root, epic_dir)
    derive_tasks(epic_dir)
    create, create_mod = _create(), _mod()
    changed: list[Path] = []
    refresh = getattr(a, "refresh", False)
    base = getattr(a, "base", None) or integration_branch(epic_dir.name)
    results: list[str] = []
    for path in _task_files(epic_dir):
        doc = _read_doc(path)
        if doc.meta.get("status") == "done":
            continue
        name = worktree_name(epic_dir.name, path.stem)
        live = doc.meta.get("worktree", "")
        if live and Path(live).is_dir():
            wt, verb = live, "reused"
            branch = doc.meta.get("branch") or name
        else:
            branch = name
            repo = _task_repo(root, doc.meta.get("repo", ""))
            existing = workbench.worktrees_dir(_workbench(root)) / name
            if existing.is_dir():
                wt, verb = str(existing / repo if repo else existing), "reused"
            else:
                _require_integration_branch(root, doc.meta, base, epic_dir.name)
                wt, verb = create(name=name, base=base, repo=repo, start=root)["path"], "created"
        status = "in-progress" if doc.meta.get("status", "todo") == "todo" else doc.meta["status"]
        _write_task(path, doc, changed, worktree=wt, branch=branch, status=status)
        if refresh:
            if verb == "created" or _tree_live(wt):
                results.append(f"{path.stem} {create_mod.fast_forward(Path(wt), base)}")
        else:
            print(f"{verb} {name}: {wt}")
    if changed:
        commit_ticket_change(epic_dir.name, "worktrees", changed, root)
    for line in results:
        print(line)
    return 0


def _ids(entries, *keys) -> set[str]:
    return {str(e.get(k)) for e in entries or [] if isinstance(e, dict) for k in keys if e.get(k)}


def _reasons(entries, tid: str) -> list[str]:
    """Every escalation reason the run recorded for one task."""
    out = []
    for e in entries or []:
        if isinstance(e, dict) and tid in (str(e.get("id")), str(e.get("taskId"))):
            rs = e.get("reasons") or [e.get("reason")]
            out += [str(r) for r in rs if r]
    return out


def _dependency_only(entries, tid: str) -> bool:
    reasons = _reasons(entries, tid)
    return bool(reasons) and set(reasons) == {"dependency-failed"}


def _run_status(
    t: dict, blocked: set[str], escalated: set[str], escalations: list | None = None
) -> str:
    tid = t["id"]
    if tid in blocked or t.get("stopped") == "blocked":
        return "blocked"
    if t.get("verified") and t.get("processOnly") and t.get("stopped") != "review-shallow":
        return "done"
    if tid in escalated:
        return "todo" if _dependency_only(escalations, tid) else "escalated"
    if t.get("verified") and t.get("clean") and not t.get("stopped"):
        return "done"
    return "in-progress"


def _dependency_note(entries, t: dict, meta: dict, run: str) -> str:
    deps = []
    for e in entries or []:
        if isinstance(e, dict) and t["id"] in (str(e.get("id")), str(e.get("taskId"))):
            deps += [str(d) for d in e.get("waitingOn") or e.get("dependsOn") or []]
    deps = deps or [str(d) for d in t.get("waitingOn") or meta.get("depends_on") or []]
    day = datetime.date.today().isoformat()
    return f"- {day} run {run}: dependency-failed on {', '.join(dict.fromkeys(deps))}"


def _gap_summary(g) -> str:
    if isinstance(g, dict):
        return str(g.get("what") or g.get("summary") or "")
    return str(g)


def _section_replace(body: str, name: str, text: str) -> str:
    return re.sub(
        rf"(^## {re.escape(name)}[ \t]*\n).*?(?=^## |\Z)",
        lambda m: m.group(1) + "\n" + text + "\n\n",
        body,
        count=1,
        flags=re.M | re.S,
    )


def _new_discovered(epic_dir: Path, d: dict, src: Doc | None, run: str, root: Path) -> Path | None:
    title = str(d.get("what", "")).strip()
    task = slug(title)
    if not task:
        raise TicketError(f"discovered entry has no usable 'what': {d!r}")
    worktree_name(epic_dir.name, task)
    path = epic_dir / "tasks" / f"{task}.md"
    if path.exists():
        return None
    where, why = str(d.get("where", "")), str(d.get("why", ""))
    doc = _template("task.md")
    files = [where] if where and " " not in where else []
    clash = run_check(root, title, epic_dir.name, files).failures
    doc.meta.update(
        title=title,
        status="blocked" if clash else "todo",
        repo=(src.meta.get("repo", "") if src else ""),
        value=why,
        files=files,
    )
    finding = f"{title} at {where or 'the place the run named'}"
    body = _render(
        doc.body,
        {
            "title": title,
            "ac": f"- AC1: {title} at {where or 'the place the run named'} is resolved "
            "[evidence: judgement]",
            "requirement": f"{title}\n\nWhere: {where}\n\nWhy: {why}",
            "files": "\n".join(f"- `{f}`" for f in files),
        },
    )
    for name, text in (
        (
            "Interfaces",
            f"Keep the interfaces around {where or 'the finding'} unchanged "
            f"unless resolving it requires otherwise: {title}.",
        ),
        (
            "Expected outcome",
            f"{finding} is resolved, and {why or 'the reason it was raised'} no longer applies.",
        ),
        (
            "Steps",
            f"1. Write a failing test that shows: {title}.\n"
            f"2. Fix it at {where or 'the place named above'}.\n"
            "3. Run the task verify command and confirm it passes.",
        ),
    ):
        body = _section_replace(body, name, text)
    note = f"Discovered in task `{d.get('taskId', '')}` during run `{run}`."
    if clash:
        note += "\n\nBlocked by the dedup check:\n" + "\n".join(f"- {m}" for m in clash)
    body = _section_replace(body, "Notes", note)
    path.parent.mkdir(exist_ok=True)
    path.write_text(dump(Doc(doc.meta, body)))
    return path


def _actual_update(meta: dict, t: dict, run: str) -> dict:
    """`actual` minutes from durationMs: added to earlier runs, replaced on a re-apply."""
    ms = t.get("durationMs")
    if not isinstance(ms, (int, float)) or ms <= 0:
        return {}
    minutes = max(1, round(ms / 60000))
    before = _minutes(meta.get("actual"), t["id"], "actual")
    return {"actual": str(minutes if meta.get("run") == run else before + minutes)}


def _run_dir_durations(run_dir: Path) -> dict[str, int]:
    """Task id -> ms between the first and last transcript timestamp of its agents."""
    labels: dict[str, str] = {}
    try:
        lines = (run_dir / "journal.jsonl").read_text().splitlines()
    except OSError:
        return {}
    for line in lines:
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if (
            isinstance(e, dict)
            and e.get("type") == "started"
            and e.get("agentId")
            and e.get("label")
        ):
            labels[str(e["agentId"])] = str(e["label"])
    spans: dict[str, list[float]] = {}
    for agent, label in labels.items():
        tid = re.sub(r"\+\d+$", "", label.split(":")[-1])
        try:
            rows = (run_dir / f"agent-{agent}.jsonl").read_text().splitlines()
        except OSError:
            continue
        for row in rows:
            try:
                raw = str(json.loads(row)["timestamp"]).replace("Z", "+00:00")
                ts = datetime.datetime.fromisoformat(raw)
            except (ValueError, KeyError, TypeError):
                continue
            spans.setdefault(tid, []).append(ts.timestamp() * 1000)
    return {t: round(max(v) - min(v)) for t, v in spans.items() if len(v) > 1}


def cmd_apply_run(a: argparse.Namespace) -> int:
    root = Path(a.root)
    require_main_checkout(root)
    epic_dir = resolve_epic(a.epic, root)
    if _phase_of(epic_dir) != "in-progress":
        raise TicketError(
            f"epic {epic_dir.name!r} is in {_phase_of(epic_dir)}; apply-run needs it in-progress"
        )
    ret = json.loads(Path(a.run_return).read_text())
    if a.run_dir:
        for t, ms in _run_dir_durations(Path(a.run_dir)).items():
            for entry in ret.get("tasks", []):
                if str(entry.get("id")) == t:
                    entry["durationMs"] = ms
    run = str(ret.get("run") or ret.get("name") or ret.get("runName") or epic_dir.name)
    files = {p.stem: p for p in _task_files(epic_dir)}
    unknown = sorted({str(t.get("id")) for t in ret.get("tasks", [])} - set(files))
    if unknown:
        raise TicketError(
            f"return names tasks with no file in {epic_dir.name!r}: {', '.join(unknown)}"
        )
    blocked = _ids(ret.get("blocked"), "id", "taskId")
    escalated = _ids(ret.get("escalated"), "id", "taskId")
    provides: dict[str, list[str]] = {}
    for p in ret.get("provides", []):
        provides.setdefault(str(p.get("taskId")), []).append(str(p.get("name")))
    changed: list[Path] = []
    for t in ret.get("tasks", []):
        path = files[t["id"]]
        doc = _read_doc(path)
        status = _run_status(t, blocked, escalated, ret.get("escalated"))
        body = doc.body
        if status == "todo" and t["id"] in escalated:
            line = _dependency_note(ret.get("escalated"), t, doc.meta, run)
            if line not in body:
                body = _append_to_section(body, "Notes", line)
            doc = Doc(doc.meta, body)
        have = list(doc.meta.get("provides", []))
        have += [n for n in provides.get(t["id"], []) if n not in have]
        _write_task(
            path,
            doc,
            changed,
            status=status,
            branch=t.get("branch") or doc.meta.get("branch", ""),
            verified_head=(t.get("verification") or {}).get("head") or "",
            run=run,
            acs_for_audit=[str(x) for x in t.get("acsForAudit") or []],
            process_gaps=[_gap_summary(g) for g in t.get("processGaps") or []],
            provides=have,
            **_actual_update(doc.meta, t, run),
        )
        print(f"{t['id']}: {status}")
    for d in ret.get("discovered", []):
        src = _read_doc(files[d["taskId"]]) if d.get("taskId") in files else None
        path = _new_discovered(epic_dir, d, src, run, root)
        if path:
            changed.append(path)
            status = _read_doc(path).meta["status"]
            print(f"discovered {path.stem}: new {status} task from {d.get('taskId', '')}")
    if changed:
        readme, moved = update_time_section(epic_dir)
        if moved:
            changed.append(readme)
        commit_ticket_change(epic_dir.name, f"apply-run {run}", changed, root)
    return 0


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


def _in_git(root: Path) -> bool:
    return _git(_existing(Path(root)), "rev-parse", "--git-dir").returncode == 0


def _git_mv(epic_dir: Path, phase: str, root: Path, name: str | None = None) -> Path:
    """Move an epic directory to <root>/<phase>/<name> with `git mv` (plain rename outside git)."""
    dest = Path(root).resolve() / phase / (name or epic_dir.name)
    if dest.exists():
        raise TicketError(f"{dest} already exists")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not _in_git(root):
        epic_dir.rename(dest)
        return dest
    r = _git(_existing(Path(root)), "mv", str(epic_dir), str(dest))
    if r.returncode != 0:
        raise TicketError(f"git mv failed: {r.stderr.strip()}")
    return dest


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


def _move_in_progress(a: argparse.Namespace, root: Path, epic_dir: Path) -> int:
    name, phase = epic_dir.name, _phase_of(epic_dir)
    if phase != "todo":
        raise TicketError(f"epic {name!r} is in {phase}; move in-progress needs it in todo")
    epics = _epics(root)
    problems = []
    for b in _read_doc(epic_dir / "README.md").meta.get("blockers", []):
        t = resolve_blocker(b, epics)
        if t is None:
            problems.append(f"blocker {b!r} names no epic")
        elif t.phase != "done":
            problems.append(f"blocker {b!r} (epic {t.slug!r}) is in {t.phase}, not done")
    problems += run_check(root, epic=name).failures
    _refuse(problems)
    if _in_git(root):
        for tree in ensure_integration_trees(root, epic_dir):
            print(f"integration {tree['path']} ({tree['verb']})")
    dest = _git_mv(epic_dir, "in-progress", root)
    _update_readme(dest, owner=a.owner or _git_user(root), stage="build")
    for path in _task_files(dest):
        doc = _read_doc(path)
        if doc.meta.get("status") == "todo":
            _write_task(path, doc, [], status="in-progress")
    commit_ticket_change(name, "move in-progress", [epic_dir, dest], root)
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


def _task_contained(src: Path, branch: str, verified_head: str, base: str) -> tuple[bool, str]:
    """Whether the task is contained in base (ancestry, else patch equivalence), and why not.
    A branch worktree-merge already deleted is judged by its verified_head."""
    mm = _merge()
    if _branch_exists(src, branch):
        return mm.contained(src, branch, base)
    if not verified_head:
        return False, f"branch {branch!r} is gone and the task has no verified_head"
    return mm.contained(src, verified_head, base)


def _task_merged(src: Path, branch: str, verified_head: str, base: str) -> bool:
    return _task_contained(src, branch, verified_head, base)[0]


def _epic_target(src: Path, epic: str, base: str) -> str:
    """What a task branch must be merged into: the epic's integration branch when src has it
    (an epic claimed before integration trees existed has none), else base."""
    branch = integration_branch(epic)
    return branch if _branch_exists(src, branch) else base


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
        plan = _integration_plan(root, epic_dir)
    except TicketError as e:
        return [str(e)]
    out = []
    for repo, _ in plan:
        src = wb / "code" / repo if repo else wb
        branch = integration_branch(name)
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
    tasks = _tasks_of(epic_dir)
    problems = _undelivered(tasks)
    for p, m in tasks:
        branch = m.get("branch") or worktree_name(name, p.stem)
        src = _task_src(root, m)
        target = _epic_target(src, name, a.base)
        ok, why = _task_contained(src, branch, m.get("verified_head", ""), target)
        if not ok:
            problems.append(
                f"task {p.stem!r}: branch {branch!r} is not merged into {target!r}: {why}"
            )
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
    epic_dir = resolve_epic(a.epic, root)
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


def cmd_rename(a: argparse.Namespace) -> int:
    root = Path(a.root)
    require_main_checkout(root)
    epic_dir = resolve_epic(a.epic, root)
    name, phase = epic_dir.name, _phase_of(epic_dir)
    if phase != "todo":
        raise TicketError(f"epic {name!r} is in {phase}; its slug froze when it left todo")
    new = slug(a.title)
    if not new:
        raise TicketError("title has no usable characters")
    tasks = _tasks_of(epic_dir)
    live = [p.stem for p, m in tasks if m.get("worktree") or m.get("branch")]
    if live and new != name:
        raise TicketError(
            f"epic {name!r} has task worktrees ({', '.join(live)}) named after "
            "its slug; rename refused"
        )
    for p, _ in tasks:
        worktree_name(new, p.stem)
    epics = _epics(root)
    if new != name and new in epics:
        raise TicketError(f"epic slug {new!r} already exists in {epics[new].phase}")
    if new != name:
        wanted = [(new, None, None)] + [(f"{new}-{p.stem}", new, p.stem) for p, _ in tasks]
        clashes = name_clashes(root, wanted, own_epic=name)
        if clashes:
            raise TicketError("; ".join(clashes))
    old_title = str(epics[name].meta.get("title", name))
    if new == name and old_title == a.title:
        print(epic_dir)
        return 0
    dest = _git_mv(epic_dir, "todo", root, new) if new != name else epic_dir
    readme, _ = _update_readme(dest, title=a.title)
    changed = [epic_dir, dest]
    for t in epics.values():
        blockers = list(t.meta.get("blockers", []))
        if t.slug == name or not any(b in (old_title, name) for b in blockers):
            continue
        fixed = [a.title if b in (old_title, name) else b for b in blockers]
        changed.append(_update_readme(t.path.parent, blockers=fixed)[0])
    commit_ticket_change(new, "rename", changed, root)
    print(dest)
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
    else is listed with its reason. Task trees and branches go before the integration ones."""

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

    def task(self, root: Path, epic: str, p: Path, m: dict) -> None:
        """One task's worktree (frontmatter `worktree`, else <config dir>/worktrees/<epic>-<task>)
        and its branch, removed when contained in the epic branch (else base) and clean."""
        wb = _workbench(root)
        tree = worktree_name(epic, p.stem)
        branch = m.get("branch") or tree
        src = _task_src(root, m)
        target = _epic_target(src, epic, self.base)
        wt = Path(m["worktree"]) if m.get("worktree") else workbench.worktrees_dir(wb) / tree
        if wt.name == tree:
            if wt.is_dir():
                self.container(wt, branch, wb, src, target)
            else:
                self.branch_only(src, branch, target)
            return
        self.tree(wt, src, branch, target)
        if not wt.is_dir():
            self.branch_only(src, branch, target)
        if wt.parent.name == tree and not self.dry_run:
            _rmdir_if_empty(wt.parent)

    def epic(self, root: Path, epic_dir: Path) -> None:
        """Every task tree and branch of the epic (target: the epic branch), then its integration
        trees at <config dir>/worktrees/<epic>[/<repo>] and legacy .worktrees/<epic>/<repo>, and
        the integration branches (target: the trunk)."""
        wb = _workbench(root)
        name = epic_dir.name
        for p, m in _tasks_of(epic_dir):
            self.task(root, name, p, m)
        for d in (workbench.worktrees_dir(wb) / integration_branch(name), wb / ".worktrees" / name):
            if d.is_dir():
                self.integration(d, name, wb)
        try:
            plan = _integration_plan(root, epic_dir)
        except TicketError:
            return
        for repo, _ in plan:
            target, fetch = _trunk(wb, repo, self.base)
            self.branch_only(
                wb / "code" / repo if repo else wb, integration_branch(name), target, fetch
            )


def cmd_reap(a: argparse.Namespace) -> int:
    root = Path(a.root)
    if not a.dry_run:
        require_main_checkout(root)
    sweep = Sweep(a.base, a.dry_run)
    if a.task and not a.epic:
        raise TicketError("reap: --task needs --epic")
    if a.epic and a.task:
        epic_dir = resolve_epic(a.epic, root)
        found = [(p, m) for p, m in _tasks_of(epic_dir) if p.stem == a.task]
        if not found:
            raise TicketError(f"reap: epic {epic_dir.name} has no task {a.task!r}")
        sweep.task(root, epic_dir.name, *found[0])
        print(json.dumps({"dryRun": a.dry_run, **sweep.summary()}, indent=2))
        for item in sweep.left:
            print(f"reap: {a.task} left in place: {item['reason']}", file=sys.stderr)
        return 1 if sweep.left else 0
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


def lint_problems(root: Path, only: str | None = None) -> list[str]:
    """Invariant breaks across every epic, or only `only`."""
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


def cmd_path(a: argparse.Namespace) -> int:
    print(resolve_epic(a.epic, Path(a.root)) / PATH_KINDS[a.kind])
    return 0


def cmd_slug(a: argparse.Namespace) -> int:
    print(slug(a.title))
    return 0


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
    sp = add("new-epic", cmd_new_epic)
    sp.add_argument("--title", required=True)
    sp.add_argument(
        "--force",
        action="store_true",
        help="create even when a live (todo/in-progress) epic is a near duplicate",
    )
    for opt in (
        "blockers",
        "repos",
        "what",
        "how",
        "why",
        "description-file",
        "goals-file",
        "non-goals-file",
    ):
        sp.add_argument(f"--{opt}")
    sp = add("new-task", cmd_new_task)
    for opt in ("epic", "title", "repo", "value", "files", "verify"):
        sp.add_argument(f"--{opt}", required=True)
    for opt in (
        "depends-on",
        "owns",
        "uses",
        "model",
        "review",
        "estimate",
        "requirement-file",
        "ac-file",
    ):
        sp.add_argument(f"--{opt}")
    sp = add("check", cmd_check)
    for opt in ("title", "epic", "files", "owns", "blockers", "goals-file"):
        sp.add_argument(f"--{opt}")
    add("index", cmd_index)
    add("existing", cmd_existing)
    sp = add("tasks", cmd_tasks)
    sp.add_argument("epic")
    sp.add_argument("--only", help="comma-separated task slugs; others are not validated")
    sp.add_argument("--out", help="write the JSON to this file instead of stdout")
    sp = add("worktrees", cmd_worktrees)
    sp.add_argument("epic")
    sp.add_argument("--base", default=None, help="default: the epic's integration branch")
    sp.add_argument(
        "--integration",
        action="store_true",
        help="create or reuse the integration tree(s) of an in-progress epic; no task tree",
    )
    sp.add_argument(
        "--refresh",
        action="store_true",
        help="fast-forward each live, clean tree with nothing ahead of --base",
    )
    sp = add("apply-run", cmd_apply_run)
    sp.add_argument("epic")
    sp.add_argument("run_return", metavar="return.json")
    sp.add_argument("--run-dir", help="Workflow transcript dir: task actuals from timestamps")
    sp = add("move", cmd_move)
    sp.add_argument("epic")
    sp.add_argument("phase", choices=("in-progress", "done"))
    sp.add_argument("--owner", help="who claims the epic (default: git user.name)")
    sp.add_argument("--base", default="main", help="branch task branches must be merged into")
    sp = add("stage", cmd_stage)
    sp.add_argument("epic")
    sp.add_argument("stage", choices=EPIC_STAGES)
    sp = add("review", cmd_review)
    sp.add_argument("epic")
    sp.add_argument("--verdict", required=True, choices=("pass", "fail"))
    sp.add_argument("--notes-file", required=True)
    sp = add("rename", cmd_rename)
    sp.add_argument("epic")
    sp.add_argument("title")
    sp = add("lint", cmd_lint)
    sp.add_argument("epic", nargs="?")
    sp = add("reap", cmd_reap)
    sp.add_argument("--dry-run", action="store_true", help="list what would go, remove nothing")
    sp.add_argument("--base", default="main")
    sp.add_argument("--epic", help="reap only this done epic (slug or directory)")
    sp.add_argument("--task", help="with --epic: reap only this task's merged, clean worktree")
    sp = add("path", cmd_path)
    sp.add_argument("epic")
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
