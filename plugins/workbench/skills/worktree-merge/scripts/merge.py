#!/usr/bin/env python3
"""Rebase one subagent worktree onto base, land it in base's worktree, then clean up.

The target is whichever worktree has base checked out (an epic integration tree or
the main checkout); no checkout is ever switched.

Cleanup is conditional: the worktree and its branch are removed only after the
merge is verified to have landed. A worktree that fails any check is left in
place, because a stranded worktree is recoverable and lost commits are not.
"""

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "worktree-create" / "scripts"))

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "lib"))

from create import WorktreeError, run, workbench_root, worktrees_dir  # noqa: E402
from workbench import ConfigError, load_config, overlap_ignored  # noqa: E402


def is_dirty(wt: Path) -> bool:
    r = run(["git", "status", "--porcelain"], cwd=wt, check=False)
    return bool(r.stdout.strip())


def commits_ahead(wt: Path, base: str) -> list[str]:
    r = run(["git", "log", "--oneline", f"{base}..HEAD"], cwd=wt, check=False)
    return [ln for ln in r.stdout.strip().splitlines() if ln]


def contained(repo: Path, head: str, target: str) -> tuple[bool, str]:
    """Whether every commit of head is already in target, and why.

    Ancestry first; failing that, patch equivalence (git cherry), which survives a
    rebase of target. git cherry skips merge commits, so a merge of target into head
    never counts against it.
    """
    r = run(["git", "rev-list", "--count", f"{target}..{head}"], cwd=repo, check=False)
    if r.returncode == 0 and r.stdout.strip() == "0":
        return True, "ancestor"
    c = run(["git", "cherry", target, head], cwd=repo, check=False)
    lines = c.stdout.splitlines()
    if c.returncode == 0 and all(ln.startswith("-") for ln in lines):
        return True, "patch-equivalent"
    n = sum(1 for ln in lines if ln.startswith("+"))
    return False, f"{n} commit(s) of {head} have no equivalent in {target}"


def merged_into(repo: Path, branch: str, base: str) -> bool:
    """True when every commit on branch is already contained in base (see contained)."""
    return contained(repo, branch, base)[0]


def _only_empty_dirs(d: Path) -> bool:
    """True when d holds nothing but (recursively) empty real directories."""
    for e in d.iterdir():
        if e.is_symlink() or not e.is_dir() or not _only_empty_dirs(e):
            return False
    return True


def _remove_empty_tree(d: Path) -> None:
    for e in list(d.iterdir()):
        _remove_empty_tree(e)
    d.rmdir()


def prune_empty_dirs(root: Path, paths: list[str]) -> list[str]:
    """Remove directories left empty under deleted repo-relative paths.

    Walks from each path's parent up to (not including) root, removing each
    directory that is empty or holds only empty directories; stops at the first
    directory holding any file. Never removes root, never follows symlinks.
    Returns the removed directories, relative to root, sorted.
    """
    root = Path(root)
    removed: set[str] = set()
    for rel in paths:
        d = root / rel
        if any((root / q).is_symlink() for q in Path(rel).parents if str(q) != "."):
            continue
        while True:
            d = d.parent
            if d == root or root not in d.parents:
                break
            if d.is_symlink() or not d.is_dir() or not _only_empty_dirs(d):
                break
            for sub in sorted(p for p in d.rglob("*") if p.is_dir()):
                removed.add(str(sub.relative_to(root)))
            removed.add(str(d.relative_to(root)))
            _remove_empty_tree(d)
    return sorted(removed)


def files_changed(wt: Path, base: str) -> list[str]:
    r = run(["git", "diff", "--name-only", f"{base}...HEAD"], cwd=wt, check=False)
    return [ln for ln in r.stdout.strip().splitlines() if ln]


def predicts_conflict(src: Path, base: str, branch: str):
    """Ask git whether merging would conflict, without touching any worktree.

    Returns True/False, or None when git is too old to answer cheaply.
    """
    r = run(["git", "merge-tree", "--write-tree", base, branch], cwd=src, check=False)
    if r.returncode == 0:
        return False
    if "unknown option" in (r.stderr or "") or "usage:" in (r.stderr or "").lower():
        return None
    return True


def assess(name: str, base: str = "main", repo: str = None, start: Path = None) -> dict:
    """Cheap complexity signal so the orchestrator can size the merge agent.

    Deliberately returns a summary, never a diff: the orchestrator should never
    have to read the changes itself to decide who merges them.
    """
    root = workbench_root(start)
    src = root / "code" / repo if repo else root
    wt = worktrees_dir(root) / name
    if repo:
        wt = wt / repo
    if not wt.is_dir():
        raise WorktreeError(f"no worktree at {wt}")

    commits = commits_ahead(wt, base)
    files = files_changed(wt, base)
    conflict = predicts_conflict(src, base, name)
    dirty = is_dirty(wt)

    # opus only for the problematic case, a predicted conflict; sonnet otherwise.
    if conflict:
        model, why = "opus", "conflict predicted"
    else:
        model, why = "sonnet", f"{len(files)} files / {len(commits)} commits, no conflict predicted"

    return {
        "name": name,
        "commits": len(commits),
        "files": len(files),
        "conflictPredicted": conflict,
        "dirty": dirty,
        "model": model,
        "why": why,
    }


def _stage(wt: Path, n: int, path: str):
    r = subprocess.run(["git", "show", f":{n}:{path}"], cwd=wt, capture_output=True)
    return r.stdout if r.returncode == 0 else None


def _union_file(wt: Path, path: str) -> bool:
    """Resolve one conflicted path by keeping both sides; False when a stage is missing."""
    ours, theirs = _stage(wt, 2, path), _stage(wt, 3, path)
    if ours is None or theirs is None:
        return False
    base = _stage(wt, 1, path) or b""
    with tempfile.TemporaryDirectory() as td:
        files = []
        for n, data in (("ours", ours), ("base", base), ("theirs", theirs)):
            f = Path(td) / n
            f.write_bytes(data)
            files.append(str(f))
        r = subprocess.run(["git", "merge-file", "--union", "-p", *files], capture_output=True)
        if r.returncode < 0 or r.returncode > 127:
            return False
        (wt / path).write_bytes(r.stdout)
    return run(["git", "add", "--", path], cwd=wt, check=False).returncode == 0


def _rebase_with_union(wt: Path, target: str, globs: list) -> tuple:
    """Rebase wt onto target, union-merging doc conflicts.

    Returns (ok, unionMerged, blocking) where blocking lists conflicted paths that are
    not docs (empty when the failure had another cause). Aborts the rebase on failure.
    """
    union: list[str] = []
    env = dict(os.environ, GIT_EDITOR="true")
    r = subprocess.run(["git", "rebase", target], cwd=wt, capture_output=True, text=True, env=env)
    while r.returncode != 0:
        conflicted = run(
            ["git", "diff", "--name-only", "--diff-filter=U"], cwd=wt, check=False
        ).stdout.split()
        docs = [p for p in conflicted if overlap_ignored(p, globs)]
        blocking = [p for p in conflicted if p not in docs]
        if not conflicted or blocking or not all(_union_file(wt, p) for p in docs):
            run(["git", "rebase", "--abort"], cwd=wt, check=False)
            return False, union, blocking or [p for p in conflicted if p in docs]
        union += [p for p in docs if p not in union]
        r = subprocess.run(
            ["git", "rebase", "--continue"], cwd=wt, capture_output=True, text=True, env=env
        )
    return True, union, []


SUITE_LOCK = Path(__file__).resolve().parent / "suite-lock.sh"


def run_suites(src: Path, target: Path = None) -> tuple[str, list[str]]:
    """Run the source checkout config's suites in order, each under suite-lock.sh,
    from the target tree root. Stops at the first failure. Returns (status, tail)."""
    suites = load_config(src)["suites"]
    if not suites:
        return "none configured", []
    for cmd in suites:
        r = subprocess.run(
            ["bash", str(SUITE_LOCK), "--", "bash", "-c", cmd],
            cwd=target or src,
            capture_output=True,
            text=True,
        )
        if r.returncode != 0:
            tail = (r.stdout + r.stderr).splitlines()[-15:]
            return f"FAIL {cmd} exit {r.returncode}", tail
    return "pass", []


def target_tree(src: Path, base: str) -> Path:
    """The worktree of src that has <base> checked out (integration tree or main checkout)."""
    out = run(["git", "worktree", "list", "--porcelain"], cwd=src, check=False).stdout
    path = None
    for ln in out.splitlines():
        if ln.startswith("worktree "):
            path = Path(ln[len("worktree ") :])
        elif ln == f"branch refs/heads/{base}" and path is not None:
            return path
    raise WorktreeError(
        f"{base} is not checked out in any worktree of {src}; run ticket.py move <epic> "
        "in-progress for an integration branch, or check out {0} in the main checkout".format(base)
    )


def _run_verify(cmd: str, wt: Path) -> tuple[bool, list[str]]:
    """Run cmd in wt under suite-lock.sh. Returns (passed, last 15 output lines)."""
    r = subprocess.run(
        ["bash", str(SUITE_LOCK), "--", "bash", "-c", cmd],
        cwd=wt,
        capture_output=True,
        text=True,
    )
    return r.returncode == 0, (r.stdout + r.stderr).splitlines()[-15:]


MAX_ATTEMPTS = 3


def merge_back(
    name: str,
    base: str = "main",
    repo: str = None,
    keep: bool = False,
    start: Path = None,
    suites: bool = True,
    verify: str = None,
) -> dict:
    root = workbench_root(start)
    src = root / "code" / repo if repo else root
    cfg = load_config(src)  # a bad workbench.json fails here, before any git work
    wt = worktrees_dir(root) / name
    if repo:
        wt = wt / repo
    if not wt.is_dir():
        raise WorktreeError(f"no worktree at {wt}")

    if is_dirty(wt):
        raise WorktreeError(
            f"{wt} has uncommitted changes. Commit them in the worktree first - "
            "this skill never discards work it did not create."
        )

    target = target_tree(src, base)
    ahead = commits_ahead(wt, base)
    is_in, by = contained(wt, "HEAD", base)
    if is_in:
        notes = [f"nothing to merge ({by}: every commit is already in {base})"]
        sha = run(["git", "rev-parse", base], cwd=target, check=False).stdout.strip()
        verification = {"command": verify, "passed": True, "tail": []}
        if verify:
            passed, tail = _run_verify(verify, target)
            verification = {"command": verify, "passed": passed, "tail": tail}
            if not passed:
                notes.append(f"--verify failed; {base} not advanced, {name} kept")
        cleaned = False
        if not keep and verification["passed"]:
            notes += cleanup(src, wt, name, target)
            cleaned = True
        return {
            "name": name,
            "merged": 0,
            "contained": True,
            "containedBy": by,
            "cleaned": cleaned,
            "notes": notes,
            "baseBefore": sha,
            "baseAfter": sha,
            "verification": verification,
        }

    notes = [f"{len(ahead)} commit(s) to merge", f"landing in {target}"]

    # Fetch so refs are current, but NEVER rebase onto origin/<base>. The branch
    # is merged into LOCAL <base>, so that is the only correct rebase target.
    # Rebasing onto origin/<base> when local and origin have diverged rewrites
    # the unpushed local commits and the fast-forward then fails as diverging
    # branches. worktree-create already merged origin/<base> into the worktree,
    # so the remote's work is present either way. A base with no remote (an
    # integration branch) fails the fetch harmlessly.
    fetched = run(["git", "fetch", "origin", base], cwd=wt, check=False)
    notes.append(
        f"fetched origin/{base}" if fetched.returncode == 0 else f"no remote {base} to fetch"
    )

    union: list[str] = []
    verification = {"command": verify, "passed": True, "tail": []}
    for attempt in range(1, MAX_ATTEMPTS + 1):
        ok, merged_docs, blocking = _rebase_with_union(wt, base, cfg["overlapIgnore"])
        if not ok:
            named = f" Conflicted paths: {', '.join(blocking)}." if blocking else ""
            raise WorktreeError(
                f"rebase of {name} onto {base} conflicted and was aborted.{named} The worktree is "
                "intact at {0}; resolve the conflict there, then run this skill again.".format(wt)
            )
        union += [p for p in merged_docs if p not in union]
        notes.append(f"rebased onto {base}")
        if verify:
            passed, tail = _run_verify(verify, wt)
            verification = {"command": verify, "passed": passed, "tail": tail}
            if not passed:
                sha = run(["git", "rev-parse", base], cwd=target, check=False).stdout.strip()
                notes.append(f"--verify failed; {base} not advanced, {name} kept")
                return {
                    "name": name,
                    "merged": 0,
                    "cleaned": False,
                    "notes": notes,
                    "unionMerged": union,
                    "baseBefore": sha,
                    "baseAfter": sha,
                    "verification": verification,
                }
        old = run(["git", "rev-parse", base], cwd=target, check=False).stdout.strip()
        # Fast-forward only, in the target tree: after a clean rebase anything else
        # means the base moved under us, and a merge commit would hide that.
        m = run(["git", "merge", "--ff-only", name], cwd=target, check=False)
        if m.returncode == 0:
            break
        # <base> moved when it is no longer an ancestor of the rebased tip.
        moved = (
            run(
                ["git", "merge-base", "--is-ancestor", base, name], cwd=target, check=False
            ).returncode
            != 0
        )
        if not moved:
            raise WorktreeError(
                f"fast-forward merge of {name} into {base} failed in {target}: "
                f"{m.stderr.strip()}. {base} is still behind the tip; the worktree is intact."
            )
        notes.append(f"{base} moved after the rebase (attempt {attempt}); rebasing again")
    else:
        raise WorktreeError(
            f"{base} kept moving: fast-forward of {name} failed after {MAX_ATTEMPTS} attempts "
            f"(each rebased and re-verified). {base} was not advanced; the worktree is intact."
        )
    if union:
        notes.append("union-merged doc files (both sides kept, review them): " + ", ".join(union))
    notes.append(f"fast-forwarded {base}")
    new = run(["git", "rev-parse", base], cwd=target, check=False).stdout.strip()
    deleted = run(
        ["git", "diff", "--name-only", "--diff-filter=D", f"{old}..{new}"], cwd=target, check=False
    ).stdout.splitlines()
    pruned = prune_empty_dirs(target, [ln for ln in deleted if ln])
    if pruned:
        notes.append("pruned empty directories: " + ", ".join(pruned))

    if not merged_into(target, name, base):
        raise WorktreeError(
            f"post-merge check failed: {name} still has commits absent from {base}. Worktree kept."
        )
    notes.append("verified: every commit is present in base")

    cleaned = False
    if not keep:
        notes += cleanup(src, wt, name, target)
        cleaned = True
    status, tail = run_suites(src, target) if suites else ("skipped (--no-suites)", [])
    return {
        "suites": status,
        "suitesTail": tail,
        "name": name,
        "merged": len(ahead),
        "cleaned": cleaned,
        "notes": notes,
        "unionMerged": union,
        "baseBefore": old,
        "baseAfter": new,
        "verification": verification,
    }


def delete_if_merged(src: Path, name: str, target: str) -> str:
    """Guarded delete: `git branch -D name` run in src, only after contained(name, target)
    passed, so src's HEAD does not matter. Returns the note for the outcome."""
    ok, why = contained(src, name, target)
    if not ok:
        return f"branch {name} kept ({why})"
    d = run(["git", "branch", "-D", name], cwd=src, check=False)
    if d.returncode == 0:
        return f"deleted branch {name}"
    return f"branch {name} kept ({d.stderr.strip()})"


def cleanup(
    src: Path, wt: Path, name: str, target: Path = None, merged_into_ref: str = None
) -> list[str]:
    """Remove wt, then delete its branch. With merged_into_ref the delete is guarded: an
    explicit contained(name, merged_into_ref) check, then `git branch -D` (see
    delete_if_merged). Without it, `git branch -d` runs from the target tree, so a branch
    merged into an integration branch is deleted though main's HEAD lacks it."""
    notes = []
    r = run(["git", "worktree", "remove", str(wt)], cwd=src, check=False)
    if r.returncode != 0:
        notes.append(f"worktree remove failed ({r.stderr.strip()}); left at {wt}")
        return notes
    notes.append(f"removed worktree {wt}")
    if merged_into_ref:
        notes.append(delete_if_merged(src, name, merged_into_ref))
    else:
        d = run(["git", "branch", "-d", name], cwd=target or src, check=False)
        notes.append(
            f"deleted branch {name}"
            if d.returncode == 0
            else f"branch {name} kept ({d.stderr.strip()})"
        )
    run(["git", "worktree", "prune"], cwd=src, check=False)
    return notes


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--name", required=True)
    ap.add_argument("--base", default="main")
    ap.add_argument("--repo", default=None)
    ap.add_argument("--keep", action="store_true", help="merge but do not remove the worktree")
    ap.add_argument(
        "--no-suites", action="store_true", help="skip the suites configured in workbench.json"
    )
    ap.add_argument(
        "--verify",
        default=None,
        help="command run in the rebased named tree, under suite-lock.sh, before the "
        "fast-forward; a failure exits 4 and leaves <base> untouched",
    )
    ap.add_argument(
        "--assess",
        action="store_true",
        help="report complexity and a model recommendation, merge nothing",
    )
    args = ap.parse_args(argv)
    try:
        if args.assess:
            a = assess(args.name, base=args.base, repo=args.repo)
            print(
                f"{a['name']}: {a['commits']} commit(s), {a['files']} file(s), "
                f"conflict={a['conflictPredicted']}, dirty={a['dirty']}"
            )
            print(f"dispatch merge agent with model: {a['model']}  ({a['why']})")
            return 0
        info = merge_back(
            args.name,
            base=args.base,
            repo=args.repo,
            keep=args.keep,
            suites=not args.no_suites,
            verify=args.verify,
        )
    except (WorktreeError, ConfigError) as e:
        print(f"[ERR] {e}", file=sys.stderr)
        return 1
    print(f"{info['name']}: merged {info['merged']} commit(s), cleaned={info['cleaned']}")
    for n in info["notes"]:
        print(f"  - {n}")
    v = info.get("verification")
    if v and v["command"]:
        print(f"verify: {'pass' if v['passed'] else 'FAIL'} {v['command']}")
        for ln in v["tail"] if not v["passed"] else []:
            print(f"  {ln}")
        if not v["passed"]:
            return 4
    if "suites" in info:
        print(f"suites: {info['suites']}")
        for ln in info.get("suitesTail", []):
            print(f"  {ln}")
        if info["suites"].startswith("FAIL"):
            return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
