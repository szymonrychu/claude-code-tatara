"""Git plumbing for the instantiation engine. Never sets protocol.file.allow."""

import re
import subprocess
from pathlib import Path

TEMPLATE_URL_RE = re.compile(
    r"^(?:[a-z+]+://(?:[^@/]+@)?|[^@/:]+@)github\.com[/:]szymonrychu/workbench(?:\.git)?/?$",
    re.IGNORECASE,
)

DEFAULT_TEMPLATE_URL = "https://github.com/szymonrychu/workbench"


class Refusal(Exception):
    """A condition the engine refuses to proceed on; the message is one line.

    printed=True means the message is multi-line output meant for stdout."""

    def __init__(self, message: str = "", printed: bool = False):
        super().__init__(message)
        self.printed = printed


def git(*args: str, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and proc.returncode != 0:
        detail = (proc.stderr.strip() or proc.stdout.strip()).splitlines()
        raise Refusal(f"git {' '.join(args[:2])} failed: {detail[-1] if detail else 'no output'}")
    return proc


def is_template_url(url: str) -> bool:
    return bool(TEMPLATE_URL_RE.match(url.strip()))


def is_repo_root(root: Path) -> bool:
    proc = git("rev-parse", "--show-toplevel", cwd=root, check=False)
    return proc.returncode == 0 and Path(proc.stdout.strip()).resolve() == root.resolve()


def ensure_repo(root: Path) -> bool:
    """git init -b main when the workbench is not its own repo. Returns True if it did."""
    if is_repo_root(root):
        return False
    git("init", "-b", "main", cwd=root)
    return True


def rename_template_origin(root: Path, force: bool = False) -> bool:
    """Rename origin to template when it is the template URL (or when forced)."""
    proc = git("remote", "get-url", "origin", cwd=root, check=False)
    if proc.returncode != 0:
        return False
    if not (force or is_template_url(proc.stdout)):
        return False
    git("remote", "rename", "origin", "template", cwd=root)
    return True


def init_component(path: Path, url: str) -> None:
    """Commit the scaffold already written at path and push it to url as origin/main."""
    git("init", "-b", "main", cwd=path)
    git("add", "-A", cwd=path)
    git("commit", "-m", "chore: initial scaffold", cwd=path)
    git("remote", "add", "origin", url, cwd=path)
    git("push", "-u", "origin", "main", cwd=path)


def is_local_url(url: str) -> bool:
    return url.startswith("file://") or url.startswith("/") or url.startswith(".")


def submodule_add_command(name: str, url: str, branch: str | None = "main") -> list[str]:
    """`git submodule add` with a short name; branch None lets the clone take the remote HEAD."""
    track = ["-b", branch] if branch else []
    return ["submodule", "add", *track, "--name", name, url, f"code/{name}"]


def submodule_add(
    root: Path,
    name: str,
    url: str,
    branch: str | None = "main",
    note: str = "origin is pushed",
) -> None:
    proc = git(*submodule_add_command(name, url, branch), cwd=root, check=False)
    if proc.returncode == 0:
        return
    if is_local_url(url) and "not allowed" in proc.stderr:
        cmd = " ".join(
            ["git", "-c", "protocol.file.allow=always", *submodule_add_command(name, url, branch)]
        )
        lead = f"{note}, run" if note else "run"
        raise Refusal(f"git blocks the local transport for {url}; {lead} this yourself: {cmd}")
    detail = proc.stderr.strip().splitlines()
    raise Refusal(f"git submodule add failed for {name}: {detail[-1] if detail else 'no output'}")
