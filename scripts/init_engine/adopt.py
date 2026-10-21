"""adopt: an existing checkout or a URL becomes a component under code/<name>.

`--path` moves the checkout (os.rename, never copy and delete) so its .git directory, .env,
venvs, untracked files, branches and stashes come along, repairs its registered worktrees and
adds it as a submodule in place. Every refusal happens before anything is created or moved, and
no file inside the adopted repo is ever edited. `--url` adds a fresh clone as a submodule.
"""

import errno
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import gitops
import remotes
import scaffold
from gitops import Refusal, git

SYMREF_HEAD_RE = re.compile(r"^ref:\s+refs/heads/(\S+)\s+HEAD$")
PLAN_WORKTREE_RE = re.compile(r"^\s*worktree:\s*[\"']?(/[^\s\"']+)", re.MULTILINE)


def device_of(path: Path) -> int:
    return path.stat().st_dev


def remote_default_branch(url: str, cwd: Path | None = None) -> str | None:
    """The branch the remote HEAD points at (`git ls-remote --symref <url> HEAD`), or None."""
    proc = subprocess.run(
        ["git", "ls-remote", "--symref", url, "HEAD"],
        cwd=cwd,
        capture_output=True,
        text=True,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if proc.returncode != 0:
        return None
    for line in proc.stdout.splitlines():
        match = SYMREF_HEAD_RE.match(line.strip())
        if match:
            return match.group(1)
    return None


def current_branch(repo: Path) -> str | None:
    proc = git("symbolic-ref", "--short", "-q", "HEAD", cwd=repo, check=False)
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def url_name(url: str) -> str:
    tail = re.split(r"[/:]", url.strip().rstrip("/"))[-1]
    return tail[: -len(".git")] if tail.endswith(".git") else tail


def check_name(root: Path, name: str) -> None:
    if not scaffold.NAME_RE.match(name):
        raise Refusal(
            f"invalid component name {name!r}: lowercase letters, digits, hyphen; pass --name"
        )
    if (root / "code" / name).exists() or (root / "code" / name).is_symlink():
        raise Refusal(f"code/{name} already exists")
    modules = root / ".gitmodules"
    if modules.is_file():
        taken = git("config", "-f", str(modules), "--get", f"submodule.{name}.path", check=False)
        if taken.returncode == 0:
            raise Refusal(f"submodule {name} is already in .gitmodules")


def check_checkout(root: Path, raw: str) -> Path:
    """Resolve and vet the checkout to move; refuse anything that is not a main checkout."""
    given = remotes.invoking_cwd() / Path(raw).expanduser()
    if given.is_symlink():
        raise Refusal(f"{raw} is a symlink; pass the real path {given.resolve()}")
    if not given.exists():
        raise Refusal(f"{raw} does not exist")
    src = given.resolve()
    if src == root or root in src.parents:
        raise Refusal(f"{src} is inside the workbench; adopt checkouts from outside it")
    if src in root.parents:
        raise Refusal(f"{src} contains the workbench; adopt a checkout outside it")
    if not src.is_dir():
        raise Refusal(f"{src} is not a directory")
    top = git("rev-parse", "--show-toplevel", cwd=src, check=False)
    if top.returncode != 0:
        raise Refusal(f"{src} is not a git checkout")
    if Path(top.stdout.strip()).resolve() != src:
        raise Refusal(f"{src} is not the top of a git checkout (that is {top.stdout.strip()})")
    if not (src / ".git").is_dir():
        raise Refusal(
            f"{src} is a linked worktree or a submodule checkout (.git is a file); "
            "adopt its main checkout"
        )
    if git("rev-parse", "--verify", "-q", "HEAD", cwd=src, check=False).returncode != 0:
        raise Refusal(f"{src} has no commits")
    return src


def linked_worktrees(src: Path) -> list[Path]:
    """Paths of the linked worktrees registered in src (the main checkout excluded)."""
    out = git("worktree", "list", "--porcelain", cwd=src).stdout
    paths = [
        Path(line[len("worktree ") :]) for line in out.splitlines() if line.startswith("worktree ")
    ]
    return [p for p in paths if p.resolve() != src]


def plan_worktree_paths(repo: Path) -> list[tuple[str, str]]:
    """(file relative to repo, absolute path) for each `worktree: /...` in docs/plans/**."""
    plans = repo / "docs" / "plans"
    found = []
    for f in sorted(plans.rglob("*")) if plans.is_dir() else []:
        if f.is_file() and not f.is_symlink():
            text = f.read_text(errors="replace")
            found += [(str(f.relative_to(repo)), m) for m in PLAN_WORKTREE_RE.findall(text)]
    return found


@dataclass
class PathPlan:
    src: Path
    dest: Path
    name: str
    origin: str | None
    bare_mode: str | None
    branch: str
    branch_source: str
    worktrees: list[tuple[Path, Path]] = field(default_factory=list)


def plan_path(root: Path, raw: str, name: str | None, remote: str | None) -> PathPlan:
    """Every check for `adopt --path`, run before anything is created or moved."""
    src = check_checkout(root, raw)
    name = name or src.name
    check_name(root, name)
    origin_proc = git("remote", "get-url", "origin", cwd=src, check=False)
    origin = origin_proc.stdout.strip() if origin_proc.returncode == 0 else None
    bare_mode = None
    if remote is not None:
        kind, arg = remotes.parse_mode(remote)
        if kind != "local-bare":
            raise Refusal(f"adopt --remote takes local-bare[:<dir>] only, not {remote!r}")
        if origin:
            raise Refusal(f"{src} already has an origin ({origin}); drop --remote")
        base = (remotes.invoking_cwd() / Path(arg).expanduser()).resolve() if arg else None
        bare_mode = f"local-bare:{base}" if base else "local-bare"
        bare = (base or remotes.default_bare_dir(root)) / f"{name}.git"
        if bare.exists():
            raise Refusal(f"bare repo {bare} already exists")
    elif not origin:
        raise Refusal(
            f"{src} has no origin; add one, or pass --remote local-bare[:<dir>] to create a bare "
            "origin and push every branch to it first"
        )
    if origin:
        branch, source = remote_default_branch("origin", cwd=src), "remote default"
    else:
        branch, source = None, ""
    if not branch:
        branch, source = current_branch(src), "current branch"
    if not branch:
        raise Refusal(f"{src} has a detached HEAD and no readable origin HEAD; check out a branch")
    code = root / "code"
    if device_of(src) != device_of(code if code.is_dir() else root):
        raise Refusal(
            f"{src} is on a different filesystem than the workbench, where a move would copy "
            "and delete; move it onto the workbench's filesystem yourself first"
        )
    dest = code / name
    moved = []
    for wt in linked_worktrees(src):
        real = wt.resolve()
        moved.append((wt, dest / real.relative_to(src) if src in real.parents else real))
    return PathPlan(src, dest, name, origin, bare_mode, branch, source, moved)


def create_origin(root: Path, plan: PathPlan) -> str:
    """Create the local bare origin, push every branch and tag, point its HEAD at the branch."""
    bare = remotes.prepare(plan.bare_mode or "local-bare", root, plan.name)
    git("remote", "add", "origin", bare, cwd=plan.src)
    git("push", "-q", "origin", "--all", cwd=plan.src)
    git("push", "-q", "origin", "--tags", cwd=plan.src)
    git("--git-dir", bare, "symbolic-ref", "HEAD", f"refs/heads/{plan.branch}")
    print(f"origin created: {bare} (every branch and tag pushed)")
    return bare


def adopt_path(
    root: Path, raw: str, name: str | None, remote: str | None, origin_is_template: bool
) -> int:
    root = root.resolve()
    plan = plan_path(root, raw, name, remote)
    origin = plan.origin or create_origin(root, plan)
    if gitops.ensure_repo(root):
        print("git init -b main")
    if gitops.rename_template_origin(root, origin_is_template):
        print("renamed origin to template")

    plan.dest.parent.mkdir(exist_ok=True)
    if plan.dest.exists():
        raise Refusal(f"code/{plan.name} already exists")
    try:
        os.rename(plan.src, plan.dest)
    except OSError as e:
        if e.errno == errno.EXDEV:
            raise Refusal(f"{plan.src} is on a different filesystem; nothing moved") from None
        raise Refusal(f"moving {plan.src} failed: {e.strerror}; nothing moved") from None
    print(f"moved {plan.src} to code/{plan.name}")

    problems = []
    present = [new for _, new in plan.worktrees if new.exists()]
    for old, new in plan.worktrees:
        if not new.exists():
            problems.append(
                f"worktree {old} is missing, not repaired (git worktree prune drops it)"
            )
    if present:
        rep = git("worktree", "repair", *map(str, present), cwd=plan.dest, check=False)
        if rep.returncode == 0:
            print("\n".join(f"worktree repaired: {p}" for p in present))
        else:
            problems.append(f"git worktree repair failed: {rep.stderr.strip()}")

    cmd = gitops.submodule_add_command(plan.name, origin, plan.branch)
    add = git(*cmd, cwd=root, check=False)
    if add.returncode != 0:
        detail = add.stderr.strip().splitlines()
        raise Refusal(
            f"the checkout is now at code/{plan.name}, but git submodule add failed "
            f"({detail[-1] if detail else 'no output'}); run: git {' '.join(cmd)}"
        )
    print(
        f"submodule {plan.name}: code/{plan.name}, origin {origin}, "
        f"branch {plan.branch} ({plan.branch_source})"
    )
    for rel, path in plan_worktree_paths(plan.dest):
        print(f"absolute worktree path in code/{plan.name}/{rel}: {path} (not rewritten)")
    for p in problems:
        print(f"warning: {p}")
    return 1 if problems else 0


def adopt_url(root: Path, url: str, name: str | None, origin_is_template: bool) -> int:
    root = root.resolve()
    name = name or url_name(url)
    check_name(root, name)
    branch = remote_default_branch(url, cwd=root if root.is_dir() else None)
    if gitops.ensure_repo(root):
        print("git init -b main")
    if gitops.rename_template_origin(root, origin_is_template):
        print("renamed origin to template")
    (root / "code").mkdir(exist_ok=True)
    gitops.submodule_add(root, name, url, branch, note="nothing was cloned")
    source = "remote default"
    if not branch:
        branch, source = current_branch(root / "code" / name) or "main", "cloned branch"
        git("config", "-f", ".gitmodules", f"submodule.{name}.branch", branch, cwd=root)
        git("add", ".gitmodules", cwd=root)
    print(f"submodule {name}: code/{name}, origin {url}, branch {branch} ({source})")
    return 0
