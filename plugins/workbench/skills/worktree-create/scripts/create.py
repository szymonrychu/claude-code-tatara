#!/usr/bin/env python3
"""Create one isolated worktree for one subagent.

Lives at <workbench>/<config dir>/worktrees/<name>, branched from base, with the
newest origin/<base> and local <base> merged in so the agent starts current.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "lib"))
import workbench  # noqa: E402

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,60}$")


class WorktreeError(RuntimeError):
    pass


def run(cmd, cwd=None, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def git_toplevel(start: Path) -> Path:
    r = run(["git", "rev-parse", "--show-toplevel"], cwd=start, check=False)
    if r.returncode != 0:
        raise WorktreeError(f"not inside a git repository: {start}")
    return Path(r.stdout.strip())


def workbench_root(start: Path = None) -> Path:
    """Workbench superrepo if there is one, else the enclosing git repo."""
    d = (start or Path.cwd()).resolve()
    probe = d
    while True:
        if (probe / "code").is_dir() and (probe / ".gitmodules").is_file():
            return probe
        if probe.parent == probe:
            break
        probe = probe.parent
    return git_toplevel(d)


def worktrees_dir(root: Path) -> Path:
    return workbench.worktrees_dir(root)


def existing_names(root: Path) -> list[str]:
    d = worktrees_dir(root)
    if not d.is_dir():
        return []
    return sorted(p.name for p in d.iterdir() if p.is_dir())


def branch_exists(repo: Path, branch: str) -> bool:
    r = run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"],
        cwd=repo,
        check=False,
    )
    return r.returncode == 0


def validate_name(name: str, root: Path, repo: Path) -> None:
    if not NAME_RE.match(name):
        raise WorktreeError(
            f"invalid worktree name {name!r}: use lowercase letters, digits, "
            "dot, dash or underscore, 2-61 chars"
        )
    taken = existing_names(root)
    if name in taken:
        raise WorktreeError(
            f"worktree {name!r} already exists at {worktrees_dir(root) / name}. "
            f"Propose a different name. In use: {', '.join(taken) or '(none)'}"
        )
    if branch_exists(repo, name):
        raise WorktreeError(
            f"branch {name!r} already exists in {repo}. Propose a different name, "
            "or merge and clean up the previous one with the worktree-merge skill."
        )


def merge_latest(wt: Path, base: str) -> list[str]:
    """Bring the worktree up to date with origin/<base> and local <base>."""
    notes = []
    fetched = run(["git", "fetch", "origin", base], cwd=wt, check=False)
    if fetched.returncode != 0:
        tail = fetched.stderr.strip().splitlines()[-1:] or ["no remote"]
        notes.append(f"no origin fetch ({tail})")
    else:
        r = run(["git", "merge", "--no-edit", f"origin/{base}"], cwd=wt, check=False)
        if r.returncode != 0:
            run(["git", "merge", "--abort"], cwd=wt, check=False)
            raise WorktreeError(
                f"merging origin/{base} into {wt.name} conflicted. The worktree is left "
                "in place for inspection; resolve it there or pick a fresh base."
            )
        notes.append(f"merged origin/{base}")
    if branch_exists(wt, base):
        r = run(["git", "merge", "--no-edit", base], cwd=wt, check=False)
        if r.returncode != 0:
            run(["git", "merge", "--abort"], cwd=wt, check=False)
            raise WorktreeError(
                f"merging local {base} into {wt.name} conflicted. The worktree is left "
                "in place for inspection."
            )
        notes.append(f"merged local {base}")
    return notes


def fast_forward(path: Path, base: str) -> str:
    """Fast-forward a clean tree with nothing ahead of local <base>.

    Returns "updated", "current", "dirty" or "ahead"; dirty and ahead trees are untouched.
    """
    if run(["git", "status", "--porcelain"], cwd=path, check=False).stdout.strip():
        return "dirty"
    ahead = run(["git", "rev-list", "--count", f"{base}..HEAD"], cwd=path, check=False)
    if ahead.returncode != 0 or ahead.stdout.strip() != "0":
        return "ahead"
    behind = run(["git", "rev-list", "--count", f"HEAD..{base}"], cwd=path, check=False)
    if behind.stdout.strip() in ("", "0"):
        return "current"
    r = run(["git", "merge", "--ff-only", base], cwd=path, check=False)
    return "updated" if r.returncode == 0 else "ahead"


def create(name: str, base: str = "main", repo: str = None, start: Path = None) -> dict:
    root = workbench_root(start)
    src = root / "code" / repo if repo else root
    if not (src / ".git").exists():
        raise WorktreeError(f"not a git checkout: {src}")

    validate_name(name, root, src)

    dest = worktrees_dir(root) / name
    if repo:
        dest = dest / repo
    dest.parent.mkdir(parents=True, exist_ok=True)

    r = run(["git", "worktree", "add", "-b", name, str(dest), base], cwd=src, check=False)
    if r.returncode != 0:
        raise WorktreeError(f"git worktree add failed: {r.stderr.strip()}")

    notes = merge_latest(dest, base)
    return {"name": name, "path": str(dest), "branch": name, "base": base, "notes": notes}


def _linked(src: Path) -> dict[Path, str]:
    """Linked worktrees of src's repository (not the main tree) mapped to their branch."""
    r = run(["git", "worktree", "list", "--porcelain"], cwd=src, check=False)
    found: dict[Path, str] = {}
    cur = None
    first = True
    for ln in r.stdout.splitlines():
        if ln.startswith("worktree "):
            cur = Path(ln[9:]).resolve()
            if first:
                first = False
            else:
                found[cur] = ""
        elif ln.startswith("branch ") and cur in found:
            found[cur] = ln[7:].removeprefix("refs/heads/")
    return found


def _ref_resolves(repo: Path, ref: str) -> bool:
    return (
        run(["git", "rev-parse", "--verify", "--quiet", ref], cwd=repo, check=False).returncode == 0
    )


def integration(epic: str, base: str = "main", repo: str = None, start: Path = None) -> dict:
    """Create (or reuse) the epic's integration worktree, named and branched <epic>."""
    root = workbench_root(start)
    src = root / "code" / repo if repo else root
    if not (src / ".git").exists():
        raise WorktreeError(f"not a git checkout: {src}")
    dest = worktrees_dir(root) / epic
    if repo:
        dest = dest / repo
    info = {"name": epic, "path": str(dest), "branch": epic, "base": base, "notes": []}
    if dest.exists() or dest.is_symlink():
        if _linked(src).get(dest.resolve()) == epic:
            return {**info, "verb": "reused"}
        raise WorktreeError(
            f"{dest} exists and is not a worktree of {src} on branch {epic!r}; "
            "move it aside or remove it, then claim again."
        )
    dest.parent.mkdir(parents=True, exist_ok=True)
    if branch_exists(src, epic):
        cmd = ["git", "worktree", "add", str(dest), epic]
    else:
        origin = f"origin/{base}"
        fork = origin if repo and _ref_resolves(src, origin) else base
        cmd = ["git", "worktree", "add", "-b", epic, str(dest), fork]
    r = run(cmd, cwd=src, check=False)
    if r.returncode != 0:
        raise WorktreeError(f"git worktree add failed: {r.stderr.strip()}")
    return {**info, "verb": "created"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--name", required=True, help="worktree name proposed by the orchestrator")
    ap.add_argument("--base", default="main", help="branch to fork from (default: main)")
    ap.add_argument("--repo", default=None, help="code/ submodule name; omit for the superrepo")
    ap.add_argument(
        "--integration",
        action="store_true",
        help="create the epic integration tree: --name is the epic slug, branch <epic>",
    )
    ap.add_argument("--list", action="store_true", help="list names already in use and exit")
    args = ap.parse_args(argv)

    try:
        if args.list:
            for n in existing_names(workbench_root()):
                print(n)
            return 0
        if args.integration:
            info = integration(args.name, base=args.base, repo=args.repo)
            print(f"worktree : {info['path']}")
            print(f"branch   : {info['branch']} (from {info['base']})")
            print(f"verb     : {info['verb']}")
            return 0
        info = create(args.name, base=args.base, repo=args.repo)
    except WorktreeError as e:
        print(f"[ERR] {e}", file=sys.stderr)
        return 1

    print(f"worktree : {info['path']}")
    print(f"branch   : {info['branch']} (from {info['base']})")
    for n in info["notes"]:
        print(f"  - {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
