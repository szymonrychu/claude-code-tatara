#!/usr/bin/env python3
"""Two-phase git worktree commit.

Phase 1 (collect): print each repo's diff so the agent can compose a
semantic-commit title. Phase 2 (commit): stage and commit using the
agent-supplied titles. This script never invents a commit message.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_lib"))

import common  # noqa: E402


def _repo_dir_or_none(report: common.Report, branch: str, repo: str) -> Path | None:
    try:
        common.resolve_repo(repo)
    except common.RepoError as e:
        report.add(repo, "failed", str(e))
        return None
    repo_dir = common.worktree_path(branch, repo)
    if not repo_dir.is_dir():
        report.add(repo, "failed", f"worktree not found: {repo_dir}")
        return None
    return repo_dir


def cmd_collect(branch: str, repos: list[str], files: list[str]) -> int:
    report = common.Report()
    for repo in repos:
        repo_dir = _repo_dir_or_none(report, branch, repo)
        if repo_dir is None:
            continue
        status_cmd = ["git", "status", "--short"] + (["--", *files] if files else [])
        status = common.run(status_cmd, cwd=repo_dir, check=False)
        if not status.stdout.strip():
            report.add(repo, "skipped", "no changes")
            continue
        diff_cmd = ["git", "diff", "HEAD"] + (["--", *files] if files else [])
        diff = common.run(diff_cmd, cwd=repo_dir, check=False)
        print(f"===== {repo} =====")
        print("-- git status --short --")
        print(status.stdout.rstrip())
        print("-- git diff --")
        print(diff.stdout.rstrip())
        print()
    print(report.render())
    return report.exit_code


def cmd_commit(branch: str, repos: list[str], files: list[str], messages: dict[str, str]) -> int:
    report = common.Report()
    for repo in repos:
        repo_dir = _repo_dir_or_none(report, branch, repo)
        if repo_dir is None:
            continue
        status_cmd = ["git", "status", "--short"] + (["--", *files] if files else [])
        status = common.run(status_cmd, cwd=repo_dir, check=False)
        if not status.stdout.strip():
            report.add(repo, "skipped", "no changes")
            continue
        title = messages.get(repo)
        if not title:
            report.add(repo, "failed", "no commit message provided")
            continue
        add_cmd = ["git", "add", "--", *files] if files else ["git", "add", "-A"]
        add_result = common.run(add_cmd, cwd=repo_dir, check=False)
        if add_result.returncode != 0:
            report.add(repo, "failed", f"git add failed: {add_result.stderr.strip()}")
            continue
        commit_result = common.run(["git", "commit", "-m", title], cwd=repo_dir, check=False)
        if commit_result.returncode != 0:
            report.add(repo, "failed", f"git commit failed: {commit_result.stderr.strip()}")
            continue
        sha = common.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=repo_dir, check=False
        ).stdout.strip()
        report.add(repo, "committed", f"{sha} {title}")
    print(report.render())
    return report.exit_code


def _parse_messages(pairs: list[str]) -> dict[str, str]:
    messages = {}
    for pair in pairs:
        if "=" not in pair:
            print(f"invalid --message (expected repo=title): {pair}", file=sys.stderr)
            sys.exit(2)
        repo, title = pair.split("=", 1)
        messages[repo.strip()] = title.strip()
    return messages


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="commit.py")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common_args(p):
        p.add_argument("--branch", required=True)
        p.add_argument("--repos", required=True, action="append")
        p.add_argument("--files", default=None)

    collect_p = sub.add_parser("collect")
    add_common_args(collect_p)

    commit_p = sub.add_parser("commit")
    add_common_args(commit_p)
    commit_p.add_argument("--message", action="append", default=[], metavar="repo=title")

    args = parser.parse_args(argv)
    repos = common.parse_repos(args.repos)
    files = common.parse_repos(args.files) if args.files else []

    if args.command == "collect":
        return cmd_collect(args.branch, repos, files)
    messages = _parse_messages(args.message)
    return cmd_commit(args.branch, repos, files, messages)


if __name__ == "__main__":
    sys.exit(main())
