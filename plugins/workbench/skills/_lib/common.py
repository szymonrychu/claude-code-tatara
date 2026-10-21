"""Shared python helpers for workbench git/GitHub skills."""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts" / "lib"))
import workbench  # noqa: E402


class RepoError(Exception):
    pass


def repo_root() -> Path:
    for start in (Path.cwd(), Path(__file__).resolve().parent):
        d = start
        while True:
            if (d / "code").is_dir() and (d / ".gitmodules").is_file():
                return d
            if d.parent == d:
                break
            d = d.parent
    raise RepoError("workbench root not found (need code/ + .gitmodules)")


def all_repos() -> list[str]:
    root = repo_root()
    gm = root / ".gitmodules"
    names = []
    if gm.is_file():
        for line in gm.read_text().splitlines():
            line = line.strip()
            if line.startswith("path = code/"):
                names.append(line.split("path = code/", 1)[1].strip())
    if not names:
        code_dir = root / "code"
        if code_dir.is_dir():
            names = sorted(p.name for p in code_dir.iterdir() if p.is_dir())
    return names


def resolve_repo(name: str) -> Path:
    root = repo_root()
    if name not in all_repos():
        raise RepoError(f"unknown repo: {name}")
    return root / "code" / name


def configured_branch(name: str) -> str | None:
    """The repo's .gitmodules branch, or None when unset (or no workbench found)."""
    try:
        root = repo_root()
    except RepoError:
        return None
    result = run(
        [
            "git",
            "config",
            "-f",
            str(root / ".gitmodules"),
            "--get",
            f"submodule.{name}.branch",
        ],
        check=False,
    )
    return result.stdout.strip() or None


def tracked_branch(name: str) -> str:
    repo_root()
    return configured_branch(name) or "main"


def worktree_path(branch: str, repo: str) -> Path:
    return workbench.worktrees_dir(repo_root()) / branch / repo


def run(cmd: list[str], cwd=None, check=True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=check)


def gh_json(args: list[str], cwd=None):
    result = run(["gh"] + list(args), cwd=cwd)
    return json.loads(result.stdout)


class Report:
    def __init__(self):
        self._rows = []

    def add(self, repo, status, detail):
        self._rows.append((repo, status, detail))

    def render(self) -> str:
        lines = [f"{'REPO':<20} {'STATUS':<10} DETAIL"]
        for repo, status, detail in self._rows:
            lines.append(f"{repo!s:<20} {status!s:<10} {detail}")
        return "\n".join(lines)

    @property
    def exit_code(self) -> int:
        return 1 if any(status == "failed" for _, status, _ in self._rows) else 0

    def print_and_exit(self):
        print(self.render())
        sys.exit(self.exit_code)


def parse_repos(value) -> list[str]:
    if isinstance(value, str):
        items = value.split(",")
    else:
        items = []
        for v in value:
            items.extend(str(v).split(","))
    seen = []
    for item in items:
        item = item.strip()
        if item and item not in seen:
            seen.append(item)
    return seen


def slugify(text, max_len=60):
    """Twin of common.sh slugify: only ASCII [A-Za-z0-9] survives, A-Z lowercased,
    every other character (non-ASCII letters included) is a separator."""
    out = []
    for ch in text:
        if "A" <= ch <= "Z":
            out.append(ch.lower())
        elif ("a" <= ch <= "z") or ("0" <= ch <= "9"):
            out.append(ch)
        else:
            out.append("-")
    slug = "-".join(p for p in "".join(out).split("-") if p)
    return slug[:max_len].rstrip("-")
