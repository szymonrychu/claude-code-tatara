"""Remote modes: url:<url>, local-bare[:<dir>], github and gitlab (forge, needs confirmation)."""

import json
import os
import re
import subprocess
from pathlib import Path

from gitops import Refusal, git


def invoking_cwd() -> Path:
    """The directory the user ran the command from (the mise task cds to the root)."""
    return Path(os.environ.get("INIT_ENGINE_CWD") or os.getcwd())


def parse_mode(mode: str) -> tuple[str, str]:
    kind, _, arg = mode.partition(":")
    if kind == "url":
        if not arg:
            raise Refusal("remote mode url needs a value: url:<url>")
        return kind, arg
    if kind == "local-bare":
        return kind, arg
    if kind in FORGES and not arg:
        return kind, ""
    raise Refusal(
        f"unknown remote mode {mode!r}; use url:<url>, local-bare[:<dir>], github or gitlab"
    )


FORGES = {"github": "gh", "gitlab": "glab"}
URL_RE = re.compile(r"(?:https?|ssh|git)://\S+|git@\S+:\S+|/\S+")


def is_forge(mode: str) -> bool:
    return parse_mode(mode)[0] in FORGES


def _run(argv: list[str]) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(argv, capture_output=True, text=True)
    except FileNotFoundError:
        raise Refusal(f"{argv[0]} is not installed or not on PATH") from None


def resolve_owner(mode: str, owner: str | None) -> str:
    """The explicit owner/group, else the authenticated forge user (read-only API call)."""
    if owner:
        return owner
    kind, _ = parse_mode(mode)
    tool = FORGES[kind]
    argv = [tool, "api", "user", "-q", ".login"] if kind == "github" else [tool, "api", "user"]
    proc = _run(argv)
    out = proc.stdout.strip()
    if proc.returncode == 0 and kind == "gitlab" and out:
        try:
            out = json.loads(out).get("username", "")
        except (ValueError, AttributeError):
            out = ""
    if proc.returncode != 0 or not out:
        raise Refusal(
            f"cannot determine the {kind} user via `{' '.join(argv)}`; pass --forge-owner"
        )
    return out


def create_command(mode: str, owner: str, name: str, public: bool = False) -> list[str]:
    kind, _ = parse_mode(mode)
    return [
        FORGES[kind],
        "repo",
        "create",
        f"{owner}/{name}",
        "--public" if public else "--private",
    ]


def forge_exists(mode: str, owner: str, name: str) -> bool:
    kind, _ = parse_mode(mode)
    return _run([FORGES[kind], "repo", "view", f"{owner}/{name}"]).returncode == 0


def preflight(mode: str, owner: str, names: list[str], public: bool, confirm: bool) -> None:
    """Refuse (printing the exact commands) unless confirmed; refuse when a repo exists."""
    if not confirm:
        lines = [" ".join(create_command(mode, owner, n, public)) for n in names]
        raise Refusal(
            "creating forge repos needs --confirm-forge; it would run:\n" + "\n".join(lines),
            printed=True,
        )
    for n in names:
        if forge_exists(mode, owner, n):
            raise Refusal(f"{owner}/{n} already exists on the {parse_mode(mode)[0]} forge")


def default_bare_dir(root: Path) -> Path:
    root = root.resolve()
    return root.parent / f"{root.name}-remotes"


def validate(mode: str, names: list[str]) -> None:
    kind, arg = parse_mode(mode)
    if kind == "url" and "{name}" not in arg and len(names) > 1:
        raise Refusal("remote url:<url> names one repo; use {name} in it for several components")


def prepare(
    mode: str, root: Path, name: str, owner: str | None = None, public: bool = False
) -> str:
    """Return the origin URL for a component, creating a bare repo or forge repo as needed.

    Forge modes must have passed preflight (confirmation) first."""
    kind, arg = parse_mode(mode)
    if kind in FORGES:
        argv = create_command(mode, resolve_owner(mode, owner), name, public)
        proc = _run(argv)
        if proc.returncode != 0:
            detail = (proc.stderr.strip() or proc.stdout.strip()).splitlines()
            raise Refusal(f"`{' '.join(argv)}` failed: {detail[-1] if detail else 'no output'}")
        urls = URL_RE.findall(proc.stdout + "\n" + proc.stderr)
        if not urls:
            raise Refusal(f"`{' '.join(argv)}` printed no repo URL")
        return urls[-1].rstrip(".,")
    if kind == "url":
        return arg.replace("{name}", name)
    base = Path(arg).expanduser() if arg else default_bare_dir(root)
    bare = (base if base.is_absolute() else invoking_cwd() / base).resolve() / f"{name}.git"
    if bare.exists():
        raise Refusal(f"bare repo {bare} already exists")
    bare.parent.mkdir(parents=True, exist_ok=True)
    git("init", "--bare", "-b", "main", str(bare))
    return str(bare)
