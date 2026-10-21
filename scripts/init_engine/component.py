"""Components after init: scaffold new ones, and remove one only when nothing can be lost."""

import shutil
import tempfile
from pathlib import Path

import gitops
import project_files
import remotes
import scaffold
from gitops import Refusal, git


def add_new(
    root: Path,
    project: str,
    component_specs: list[str],
    remote: str,
    forge_owner: str | None,
    public: bool,
    confirm_forge: bool,
    origin_is_template: bool,
) -> list[tuple[str, str]]:
    """Validate, then scaffold each NAME[:LANG] component, push its origin, add the submodule."""
    if not component_specs:
        raise Refusal("at least one --component is required")
    specs = [scaffold.parse_component(c) for c in component_specs]
    names = [n for n, _ in specs]
    for name, lang in specs:
        if not scaffold.NAME_RE.match(name):
            raise Refusal(f"invalid component name {name!r}: lowercase letters, digits, hyphen")
        if lang not in scaffold.LANGS:
            raise Refusal(f"unknown language {lang!r} for {name}; use {', '.join(scaffold.LANGS)}")
        if (root / "code" / name).exists():
            raise Refusal(f"code/{name} already exists")
    if len(set(names)) != len(names):
        raise Refusal("duplicate component names")
    remotes.validate(remote, names)
    owner = None
    if remotes.is_forge(remote):
        owner = remotes.resolve_owner(remote, forge_owner)
        remotes.preflight(remote, owner, names, public, confirm_forge)

    if gitops.ensure_repo(root):
        print("git init -b main")
    if gitops.rename_template_origin(root, origin_is_template):
        print("renamed origin to template")

    (root / "code").mkdir(exist_ok=True)
    for name, lang in specs:
        url = remotes.prepare(remote, root, name, owner, public)
        with tempfile.TemporaryDirectory(prefix="workbench-new-") as tmp:
            repo = Path(tmp) / name
            scaffold.write(repo, project, name, lang)
            gitops.init_component(repo, url)
        gitops.submodule_add(root, name, url)
        print(f"component {name} ({lang}): origin {url}, submodule code/{name}")
    return specs


def unpushed_problems(repo: Path) -> list[str]:
    """What exists nowhere else: dirty files, unpushed commits, stashes, linked worktrees."""
    problems = []
    status = git("status", "--porcelain", "--untracked-files=all", cwd=repo).stdout.splitlines()
    if status:
        problems.append(f"{len(status)} uncommitted or untracked change(s), e.g. {status[0]}")
    heads = git(
        "for-each-ref", "--format=%(refname:short) %(objectname)", "refs/heads", cwd=repo
    ).stdout.splitlines()
    tips = [tuple(h.split(" ", 1)) for h in heads]
    detached = git("symbolic-ref", "-q", "HEAD", cwd=repo, check=False).returncode != 0
    if detached:
        tips.append(("HEAD (detached)", git("rev-parse", "HEAD", cwd=repo).stdout.strip()))
    for label, sha in tips:
        if not git("branch", "-r", "--contains", sha, cwd=repo).stdout.strip():
            problems.append(f"{label} has commits that are not on any remote branch")
    stashes = git("stash", "list", cwd=repo).stdout.splitlines()
    if stashes:
        problems.append(f"{len(stashes)} stash(es) are never pushed, e.g. {stashes[0]}")
    listing = git("worktree", "list", "--porcelain", cwd=repo).stdout
    extra = [x for x in listing.splitlines() if x.startswith("worktree ")][1:]
    if extra:
        problems.append(f"{len(extra)} linked worktree(s): {extra[0].split(' ', 1)[1]}")
    return problems


def check_removable(root: Path, name: str) -> Path:
    """Every refusal check, before anything is changed. Returns code/<name>."""
    if name not in {n for n, _ in project_files.components(root)}:
        raise Refusal(f"{name} is not a component of this workbench")
    repo = root / "code" / name
    if not (repo / ".git").exists():
        raise Refusal(f"code/{name} is not checked out, so its local state cannot be verified")
    problems = unpushed_problems(repo)
    if problems:
        raise Refusal(f"refusing to remove {name}, nothing changed: " + "; ".join(problems))
    return repo


def remove(root: Path, name: str) -> None:
    root = root.resolve()
    if not gitops.is_repo_root(root):
        raise Refusal("the workbench is not a git repository")
    if not scaffold.NAME_RE.match(name):
        raise Refusal(f"invalid component name {name!r}")
    check_removable(root, name)
    staged = git("diff", "--cached", "--name-only", cwd=root).stdout.split()
    if staged:
        raise Refusal(f"the workbench has staged changes ({staged[0]}...); commit or unstage first")

    git("submodule", "deinit", "-f", f"code/{name}", cwd=root)
    git("rm", "-f", f"code/{name}", cwd=root)
    shutil.rmtree(root / "code" / name, ignore_errors=True)
    gitdir = Path(git("rev-parse", "--git-dir", cwd=root).stdout.strip())
    shutil.rmtree(
        (root / gitdir if not gitdir.is_absolute() else gitdir) / "modules" / name,
        ignore_errors=True,
    )
    print(f"removed code/{name} and .git/modules/{name}")

    project_files.write_all(root, event=f"component {name} removed")
    paths = [
        p
        for p in (
            ".gitmodules",
            "AGENTS.md",
            ".mise.toml",
            "docs/architecture.md",
            "MEMORY.md",
            "ROADMAP.md",
        )
        if (root / p).exists()
    ]
    git("add", "--", *paths, cwd=root)
    git("commit", "-m", f"chore(workbench): remove component {name}", cwd=root)
    print(f"committed chore(workbench): remove component {name}")
