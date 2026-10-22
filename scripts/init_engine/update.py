"""init update: merge the template's tooling into a workbench, minus the template's own docs."""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import owned
import project_files
from gitops import Refusal, git


def preflight(root: Path) -> None:
    agents = root / "AGENTS.md"
    if not agents.is_file() or project_files.UNINIT_RE.search(agents.read_text()):
        raise Refusal("this workbench is not initialised; run init (new or adopt) first")
    if git("rev-parse", "-q", "--verify", "MERGE_HEAD", cwd=root, check=False).returncode == 0:
        raise Refusal("a merge is in progress; finish or abort it first")
    dirty = git("status", "--porcelain", cwd=root).stdout.splitlines()
    if dirty:
        raise Refusal("the working tree is not clean: " + "; ".join(dirty))


def fetch_template(root: Path, url: str, branch: str) -> str:
    if git("remote", "get-url", "template", cwd=root, check=False).returncode != 0:
        git("remote", "add", "template", url, cwd=root)
    git("fetch", "template", branch, cwd=root)
    return git("rev-parse", "FETCH_HEAD^{commit}", cwd=root).stdout.strip()


def restore_owned(root: Path) -> None:
    """Resolve every instance-owned path to the project side (HEAD), dropping template content."""
    for rel, _kind in owned.INSTANCE_OWNED:
        git("rm", "-rf", "--cached", "--ignore-unmatch", "-q", "--", rel, cwd=root)
        target = root / rel
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        elif target.exists() or target.is_symlink():
            target.unlink()
        if git("ls-tree", "-r", "--name-only", "HEAD", "--", rel, cwd=root).stdout.strip():
            git("checkout", "HEAD", "--", rel, cwd=root)


def abort(root: Path, reason: str) -> Refusal:
    if git("rev-parse", "-q", "--verify", "MERGE_HEAD", cwd=root, check=False).returncode == 0:
        git("merge", "--abort", cwd=root)
    # the tree was clean at preflight, so this only drops what the update itself wrote
    git("reset", "--hard", "HEAD", cwd=root)
    git("clean", "-fdq", cwd=root)
    return Refusal(reason)


def tail(proc: subprocess.CompletedProcess) -> str:
    lines = (proc.stderr or proc.stdout).strip().splitlines()
    return lines[-1] if lines else "no output"


def cmd_update(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    preflight(root)
    sha = fetch_template(root, args.url, args.branch)
    short = sha[:12]
    if git("merge-base", "--is-ancestor", sha, "HEAD", cwd=root, check=False).returncode == 0:
        print(f"up to date with template/{args.branch} {short}")
        return 0
    merge = git("merge", "--no-commit", "--no-ff", sha, cwd=root, check=False)
    merging = (
        git("rev-parse", "-q", "--verify", "MERGE_HEAD", cwd=root, check=False).returncode == 0
    )
    if merge.returncode != 0 and not merging:
        raise Refusal(f"git merge failed: {tail(merge)}")
    restore_owned(root)
    if git("ls-files", "-u", cwd=root).stdout.strip():
        raise abort(root, "the merge leaves conflicts outside the instance-owned paths")
    refresh = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "init_engine" / "cli.py"),
            "--root",
            str(root),
            "refresh",
            "--event",
            f"template update {short}",
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if refresh.returncode != 0:
        raise abort(root, f"refresh failed after the merge: {tail(refresh)}")
    lint = subprocess.run(args.lint_command, shell=True, cwd=root, capture_output=True, text=True)
    if lint.returncode != 0:
        raise abort(root, f"lint failed after the merge ({args.lint_command}): {tail(lint)}")
    subject = f"chore(workbench): template update {short}"
    git("add", "-A", cwd=root)
    git("commit", "-m", subject, "-m", f"Template-Commit: {sha}", cwd=root)
    print(f"committed {subject}")
    return 0
