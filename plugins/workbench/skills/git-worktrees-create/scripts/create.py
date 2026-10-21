#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_lib"))

from common import (
    RepoError,
    Report,
    parse_repos,
    resolve_repo,
    run,
    tracked_branch,
    worktree_path,
)


def branch_exists_locally(repo_path, branch):
    result = run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"],
        cwd=repo_path,
        check=False,
    )
    return result.returncode == 0


def branch_exists_on_remote(repo_path, branch):
    result = run(["git", "ls-remote", "--heads", "origin", branch], cwd=repo_path, check=False)
    return result.returncode == 0 and result.stdout.strip() != ""


def create_worktree(repo, branch, report):
    try:
        repo_path = resolve_repo(repo)
    except RepoError as e:
        report.add(repo, "failed", str(e))
        return

    wt_path = worktree_path(branch, repo)
    if wt_path.exists():
        report.add(repo, "skipped", f"worktree already exists at {wt_path}")
        return

    try:
        run(["git", "fetch", "origin"], cwd=repo_path)

        reuse = branch_exists_locally(repo_path, branch) or branch_exists_on_remote(
            repo_path, branch
        )
        if reuse:
            run(["git", "worktree", "add", str(wt_path), branch], cwd=repo_path)
            report.add(repo, "ok", f"{wt_path} (branch reused)")
        else:
            default = tracked_branch(repo)
            run(
                [
                    "git",
                    "worktree",
                    "add",
                    "-b",
                    branch,
                    str(wt_path),
                    f"origin/{default}",
                ],
                cwd=repo_path,
            )
            report.add(repo, "ok", f"{wt_path} (branch created off origin/{default})")
    except subprocess.CalledProcessError as e:
        report.add(repo, "failed", e.stderr.strip() or str(e))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--branch", required=True)
    parser.add_argument("--repos", required=True, nargs="+")
    args = parser.parse_args()

    repos = parse_repos(args.repos)

    report = Report()
    for repo in repos:
        create_worktree(repo, args.branch, report)

    report.print_and_exit()


if __name__ == "__main__":
    main()
