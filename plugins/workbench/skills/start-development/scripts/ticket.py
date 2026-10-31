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


# ---------------------------------------------------------------- plan state


def _git_user(root: Path) -> str:
    r = _git(_existing(Path(root)), "config", "user.name")
    return r.stdout.strip() or os.environ.get("USER", "")


def _refuse(problems: list[str]) -> None:
    if problems:
        raise TicketError("; ".join(problems))


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


def _branch_exists(src: Path, branch: str) -> bool:
    return (
        bool(branch)
        and _git(src, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}").returncode == 0
    )


def _trunk(wb: Path, repo: str, base: str) -> tuple[str, bool]:
    """(ref the plan branch must be in, whether to fetch it): the local base in meta mode,
    origin/<tracked branch> in component mode."""
    if not repo:
        return base, False
    return f"origin/{_submodule_branch(wb, repo)}", True


def _fetch_trunk(src: Path, target: str) -> None:
    _git(src, "fetch", "origin", target.split("/", 1)[1])


def branch_problems(root: Path, plan_dir: Path, base: str) -> list[str]:
    """One line per plan branch that is not contained in its trunk (ancestry, else patch
    equivalence); a branch that is already gone is fine."""
    wb, branch = _workbench(root), plan_branch(plan_dir.name)
    try:
        layout = tree_layout(root, plan_dir)
    except TicketError as e:
        return [str(e)]
    out = []
    for repo, _ in layout:
        src = wb / "code" / repo if repo else wb
        if not _branch_exists(src, branch):
            continue
        target, fetch = _trunk(wb, repo, base)
        if fetch:
            _fetch_trunk(src, target)
        ok, why = _merge().contained(src, branch, target)
        if not ok:
            out.append(f"branch {branch!r} is not merged into {target!r}: {why}")
    return out


def retro_gate(plan_dir: Path, action: str) -> None:
    """Refuse unless the plan is in-progress and the reviewer wrote retro.md (the review
    passed); the gate `move done` and `close` share."""
    name, phase = plan_dir.name, phase_of(plan_dir)
    if phase != "in-progress":
        raise TicketError(f"plan {name!r} is in {phase}; {action} needs it in-progress")
    if not (plan_dir / PATH_KINDS["retro"]).is_file():
        raise TicketError(
            f"plan {name!r} has no retro.md; the reviewer writes it when the review passes"
        )


def finish(root: Path, plan_dir: Path, event: str, base: str) -> int:
    """Move the plan dir to done, commit it (retro.md and close.json with it) as `event`, then
    sweep the plan's trees and branches. A sweep error is reported; the move stands."""
    name = plan_dir.name
    dest = _git_mv(plan_dir, "done", root)
    commit_ticket_change(name, event, [plan_dir, dest], root)
    sweep = Sweep(base, dry_run=False)
    try:
        sweep.plan(root, dest)
    except Exception as e:  # the move is committed; a sweep error must not undo or hide it
        print(
            f"ticket.py: plan {name!r} moved to done, but the worktree sweep failed: {e}",
            file=sys.stderr,
        )
        print(json.dumps(sweep.summary(), indent=2))
        return 1
    print(json.dumps(sweep.summary(), indent=2))
    return 0


def _move_done(a: argparse.Namespace, root: Path, plan_dir: Path) -> int:
    retro_gate(plan_dir, "move done")
    _refuse(branch_problems(root, plan_dir, a.base))
    return finish(root, plan_dir, "move done", a.base)


def cmd_move(a: argparse.Namespace) -> int:
    root = Path(a.root)
    require_main_checkout(root)
    plan_dir = resolve_plan(a.plan, root)
    if a.phase == "in-progress":
        return _move_in_progress(a, root, plan_dir)
    return _move_done(a, root, plan_dir)


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

    def trees(self, d: Path, branch: str, wb: Path) -> None:
        """A <configdir>/worktrees/<plan> entry: the meta tree itself or one tree per
        code/<repo>, each judged against its trunk."""
        if (d / ".git").exists():
            self.tree(d, wb, branch, self.base)
            return
        for sub in sorted(p for p in d.iterdir() if p.is_dir()):
            target, fetch = _trunk(wb, sub.name, self.base)
            self.tree(sub, wb / "code" / sub.name, branch, target, fetch)
        if not self.dry_run:
            _rmdir_if_empty(d)

    def plan(self, root: Path, plan_dir: Path) -> None:
        """The plan's trees at <configdir>/worktrees/<plan>[/<repo>], then its branches
        (target: the trunk)."""
        wb = _workbench(root)
        branch = plan_branch(plan_dir.name)
        d = workbench.worktrees_dir(wb) / branch
        if d.is_dir():
            self.trees(d, branch, wb)
        try:
            layout = tree_layout(root, plan_dir)
        except TicketError:
            return
        for repo, _ in layout:
            target, fetch = _trunk(wb, repo, self.base)
            self.branch_only(wb / "code" / repo if repo else wb, branch, target, fetch)


def cmd_reap(a: argparse.Namespace) -> int:
    """Sweep done plans' trees and trees named after a plan that is not in-progress; with
    --plan only that done plan's trees."""
    root = Path(a.root)
    if not a.dry_run:
        require_main_checkout(root)
    sweep = Sweep(a.base, a.dry_run)
    if a.plan:
        plan_dir = resolve_plan(a.plan, root)
        phase = phase_of(plan_dir)
        if phase != "done":
            raise TicketError(f"reap: plan {plan_dir.name} is not done (in {phase}/)")
        sweep.plan(root, plan_dir)
        print(json.dumps({"dryRun": a.dry_run, **sweep.summary()}, indent=2))
        return 0
    plans = {p.slug: p for p in scan(root)}
    for p in plans.values():
        if p.phase == "done":
            sweep.plan(root, p.dir)
    wb = _workbench(root)
    wt_dir = workbench.worktrees_dir(wb)
    for d in sorted(p for p in wt_dir.iterdir() if p.is_dir()) if wt_dir.is_dir() else []:
        owner = plans.get(d.name)
        if owner and owner.phase != "in-progress":
            sweep.trees(d, d.name, wb)
    print(json.dumps({"dryRun": a.dry_run, **sweep.summary()}, indent=2))
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
    sp = add("new", cmd_new)
    sp.add_argument("--title", required=True)
    sp.add_argument("--repos", help="comma-separated repos the plan touches")
    sp.add_argument(
        "--force",
        action="store_true",
        help="create even when a live (todo/in-progress) plan is a near duplicate",
    )
    sp = add("check", cmd_check)
    sp.add_argument("--title", required=True)
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
    sp.add_argument("--base", default="main", help="branch the plan branch must be merged into")
    sp = add("rename", cmd_rename)
    sp.add_argument("plan")
    sp.add_argument("title")
    sp = add("reap", cmd_reap)
    sp.add_argument("--dry-run", action="store_true", help="list what would go, remove nothing")
    sp.add_argument("--base", default="main")
    sp.add_argument("--plan", help="reap only this done plan's trees")
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
