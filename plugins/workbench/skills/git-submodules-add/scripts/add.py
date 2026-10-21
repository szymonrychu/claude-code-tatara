#!/usr/bin/env python3
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "_lib"))

from common import RepoError, Report, all_repos, repo_root, run  # noqa: E402

SYMREF_HEAD_RE = re.compile(r"^ref:\s+refs/heads/(\S+)\s+HEAD$")


def default_branch(url: str) -> str:
    result = run(["git", "ls-remote", "--symref", url, "HEAD"], check=False)
    if result.returncode != 0:
        raise RepoError(f"ls-remote failed for {url}: {result.stderr.strip()}")
    for line in result.stdout.splitlines():
        match = SYMREF_HEAD_RE.match(line.strip())
        if match:
            return match.group(1)
    raise RepoError(f"could not determine default branch for {url}")


def submodule_name(url: str) -> str:
    name = url.rstrip("/")
    if name.endswith(".git"):
        name = name[: -len(".git")]
    name = name.rsplit("/", 1)[-1]
    if not name:
        raise RepoError(f"cannot derive submodule name from url: {url}")
    return name


def process_url(url: str, root: Path, report: Report) -> None:
    try:
        name = submodule_name(url)
    except RepoError as e:
        report.add(url, "failed", str(e))
        return

    target = root / "code" / name
    if target.exists() or name in all_repos():
        report.add(name, "skipped", f"code/{name} already present")
        return

    try:
        branch = default_branch(url)
    except RepoError as e:
        report.add(name, "failed", str(e))
        return

    result = run(
        ["git", "submodule", "add", "-b", branch, url, f"code/{name}"],
        cwd=root,
        check=False,
    )
    if result.returncode != 0:
        report.add(name, "failed", result.stderr.strip())
        return

    report.add(name, "added", f"branch={branch}")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Add git submodules under code/")
    parser.add_argument("urls", nargs="+", help="one or more git repo URLs")
    args = parser.parse_args(argv)

    root = repo_root()
    report = Report()
    for url in args.urls:
        process_url(url, root, report)
    report.print_and_exit()


if __name__ == "__main__":
    main()
