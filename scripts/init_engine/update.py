"""init update: merge the template's tooling into a workbench, minus the template's own docs."""

import argparse
import json
import subprocess
import sys
from pathlib import Path

import owned
import project_files
from finalize import TEMPLATE_MARKET, load_wb
from gitops import DEFAULT_TEMPLATE_URL, Refusal, git


def preflight(root: Path) -> None:
    if not project_files.is_initialised(root):
        raise Refusal("this workbench is not initialised; run init (new or adopt) first")
    if git("rev-parse", "-q", "--verify", "MERGE_HEAD", cwd=root, check=False).returncode == 0:
        raise Refusal("a merge is in progress; finish or abort it first")
    dirty = git("status", "--porcelain", cwd=root).stdout.splitlines()
    if dirty:
        raise Refusal("the working tree is not clean: " + "; ".join(dirty))


def check_args(args: argparse.Namespace) -> None:
    """Refuse a flag value git would read as an option."""
    for flag, value in (("--url", args.url), ("--branch", args.branch), ("--base", args.base)):
        if value and value.startswith("-"):
            raise Refusal(f"{flag} {value!r} starts with '-'")


def fetch_template(root: Path, url: str | None, branch: str) -> str:
    """Fetch `branch` from the template remote; add it from `url` (or the default) if missing.

    An explicit `url` that differs from an existing template remote is refused, never ignored."""
    current = git("config", "--get", "remote.template.url", cwd=root, check=False)
    if current.returncode == 0:
        remote = current.stdout.strip()
        if url is not None and url != remote:
            raise Refusal(
                f"--url {url} differs from the template remote {remote}\n"
                f"to update from {url}, first run: git remote set-url template {url}"
            )
        url = remote
    else:
        url = url or DEFAULT_TEMPLATE_URL
        git("remote", "add", "template", url, cwd=root)
    git("fetch", "template", branch, cwd=root)
    sha = git("rev-parse", "FETCH_HEAD^{commit}", cwd=root).stdout.strip()
    print(f"template: {url} {branch} {sha}")
    return sha


def owned_rels() -> list[str]:
    return [rel for rel, _kind in owned.INSTANCE_OWNED]


def git_paths(root: Path, cmd: str, *args: str) -> set[str]:
    """The paths under the owned paths that a git listing command prints."""
    out = git("--literal-pathspecs", cmd, "-z", *args, "--", *owned_rels(), cwd=root).stdout
    return {p for p in out.split("\0") if p}


def check_ignored_collisions(root: Path, sha: str) -> None:
    """Refuse when the merge would overwrite an ignored local file under an owned path.

    git merge silently overwrites ignored files, so a user's gitignored note at a path the
    template tracks would be lost before restore_owned could leave it alone."""
    ignored = git_paths(root, "ls-files", "--others", "--ignored", "--exclude-standard")
    hit = sorted(ignored & git_paths(root, "ls-tree", "-r", "--name-only", sha))
    if hit:
        raise Refusal(
            "the template tracks paths that are local ignored files here; "
            "move them aside first: " + "; ".join(hit)
        )


def restore_owned(root: Path) -> None:
    """Drop the template's content under every instance-owned path, keeping the project's.

    Only what the merge staged is removed: index paths HEAD does not track leave the index
    and the worktree, and HEAD's version is restored for the rest. Files on disk that HEAD
    does not track and the merge did not stage (gitignored local notes) are left untouched."""
    staged = git_paths(root, "ls-files")
    in_head = git_paths(root, "ls-tree", "-r", "--name-only", "HEAD")
    dropped = sorted(staged - in_head)
    if dropped:
        git("--literal-pathspecs", "rm", "--cached", "-q", "--", *dropped, cwd=root)
    for rel in dropped:
        path = root / rel
        if path.is_symlink() or path.is_file():
            path.unlink()
        parent = path.parent
        while parent != root and parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent
    if in_head:
        git("--literal-pathspecs", "checkout", "HEAD", "--", *sorted(in_head), cwd=root)


def abort(root: Path, reason: str) -> Refusal:
    if git("rev-parse", "-q", "--verify", "MERGE_HEAD", cwd=root, check=False).returncode == 0:
        git("merge", "--abort", cwd=root)
    # Invariant: preflight refused any dirty or untracked state, so everything untracked
    # now was written by this run and removing it restores the exact pre-run tree.
    git("reset", "--hard", "HEAD", cwd=root)
    git("clean", "-fdq", cwd=root)
    return Refusal(reason)


def generated_paths(root: Path) -> set[str]:
    """GENERATED_ON_CONFLICT as repo-relative paths, config-dir entries resolved."""
    wb = load_wb(root)
    try:
        cfg = wb.config_dir(root).resolve().relative_to(root.resolve())
    except (wb.ConfigError, ValueError) as e:
        raise Refusal(f"cannot resolve the config dir: {e}") from e
    cfg_names = {"settings.json", "workbench.json"}
    paths = {
        (cfg / rel).as_posix() if rel in cfg_names else rel for rel in owned.GENERATED_ON_CONFLICT
    }
    # Plugin licenses carry the same project-chosen holder as the root LICENSE.
    paths.update(p.relative_to(root).as_posix() for p in (root / "plugins").glob("*/LICENSE"))
    return paths


def resolve_generated(root: Path, generated: set[str]) -> list[str]:
    """Resolve conflicted generated files to the project side; return the leftover conflicts."""
    conflicted = sorted(set(git("diff", "--name-only", "--diff-filter=U", cwd=root).stdout.split()))
    if not conflicted:
        return []
    rest = []
    for rel in conflicted:
        if (
            rel in generated
            and git("checkout", "--ours", "--", rel, cwd=root, check=False).returncode == 0
        ):
            git("add", "--", rel, cwd=root)
            print(f"kept project side: {rel}")
        else:
            rest.append(rel)
    return rest


def rename_template_keys(root: Path) -> None:
    """Rename @workbench-template settings keys to the project marketplace; project keys win."""
    market = json.loads((root / ".claude-plugin" / "marketplace.json").read_text()).get("name")
    path = load_wb(root).config_dir(root) / "settings.json"
    if not market or market == TEMPLATE_MARKET or not path.is_file():
        return
    settings = json.loads(path.read_text())

    def rename(key: str) -> str:
        if key == TEMPLATE_MARKET:
            return market
        suffix = f"@{TEMPLATE_MARKET}"
        return key[: -len(suffix)] + f"@{market}" if key.endswith(suffix) else key

    for section in ("enabledPlugins", "extraKnownMarketplaces"):
        old = settings.get(section)
        if not isinstance(old, dict):
            continue
        renamed: dict = {}
        for key, value in old.items():  # project keys first so they win a collision
            if rename(key) == key:
                renamed[key] = value
        for key, value in old.items():
            renamed.setdefault(rename(key), value)
        settings[section] = renamed
    path.write_text(json.dumps(settings, indent=2) + "\n")


def tail(proc: subprocess.CompletedProcess) -> str:
    lines = (proc.stderr or proc.stdout).strip().splitlines()
    return lines[-1] if lines else "no output"


def oldest_root(root: Path) -> tuple[str, int]:
    """The project's oldest root commit and its committer timestamp."""
    out = git("log", "--max-parents=0", "--format=%H %ct", "HEAD", cwd=root).stdout.split("\n")
    roots = [(h, int(t)) for h, t in (line.split() for line in out if line.strip())]
    return min(roots, key=lambda r: r[1])


def candidate_base(root: Path, sha: str, not_after: int) -> str | None:
    """The newest template commit whose committer date is not newer than `not_after`."""
    out = git("log", "--format=%H %ct", sha, cwd=root).stdout.split("\n")
    best: tuple[str, int] | None = None
    for h, t in (line.split() for line in out if line.strip()):
        if int(t) <= not_after and (best is None or int(t) > best[1]):
            best = (h, int(t))
    return best[0] if best else None


def check_base(root: Path, base: str, sha: str, branch: str) -> str:
    """Resolve --base to a commit that is an ancestor of the fetched template commit."""
    proc = git("rev-parse", "-q", "--verify", f"{base}^{{commit}}", cwd=root, check=False)
    if proc.returncode != 0:
        raise Refusal(f"--base {base} is not a commit")
    commit = proc.stdout.strip()
    if git("merge-base", "--is-ancestor", commit, sha, cwd=root, check=False).returncode != 0:
        raise Refusal(f"--base {base} is not an ancestor of template/{branch} {sha[:12]}")
    return commit


def cmd_update(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    check_args(args)
    preflight(root)
    sha = fetch_template(root, args.url, args.branch)
    base = args.base
    if git("merge-base", "HEAD", sha, cwd=root, check=False).returncode == 0:
        if base:
            print("--base ignored: history is shared")
        return merge_update(root, args, sha)
    if not base:
        head, when = oldest_root(root)
        candidate = candidate_base(root, sha, when)
        rerun = "mise run init:update -- --base " + (candidate or "<template commit>")
        if args.branch != "main":
            rerun += f" --branch {args.branch}"
        raise Refusal(
            f"no shared history with template/{args.branch}\n"
            f"candidate base: {candidate or 'none'}\n{rerun}"
        )
    commit = check_base(root, base, sha, args.branch)
    project_root, _ = oldest_root(root)
    git("replace", "--graft", project_root, commit, cwd=root)
    try:
        return merge_update(root, args, sha)
    finally:
        git("replace", "-d", project_root, cwd=root, check=False)


def merge_update(root: Path, args: argparse.Namespace, sha: str) -> int:
    short = sha[:12]
    if git("merge-base", "--is-ancestor", sha, "HEAD", cwd=root, check=False).returncode == 0:
        print(f"up to date with template/{args.branch} {short}")
        return 0
    check_ignored_collisions(root, sha)
    generated = generated_paths(root)  # from the project's own config, before the merge
    merge = git("merge", "--no-commit", "--no-ff", sha, cwd=root, check=False)
    merging = (
        git("rev-parse", "-q", "--verify", "MERGE_HEAD", cwd=root, check=False).returncode == 0
    )
    if merge.returncode != 0 and not merging:
        raise Refusal(f"git merge failed: {tail(merge)}")
    restore_owned(root)
    try:
        rest = resolve_generated(root, generated)
        if rest:
            raise abort(
                root,
                "template update conflicts outside the known paths:\n" + "\n".join(rest),
            )
        rename_template_keys(root)
    except (Refusal, OSError, ValueError) as e:
        if git("rev-parse", "-q", "--verify", "MERGE_HEAD", cwd=root, check=False).returncode:
            raise
        raise abort(root, str(e)) from e
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
        out = "\n".join((lint.stdout + lint.stderr).strip().splitlines()[-20:])
        raise abort(root, f"lint failed after the merge ({args.lint_command}):\n{out}")
    subject = f"chore(workbench): template update {short}"
    git("add", "-A", cwd=root)
    git("commit", "-m", subject, "-m", f"Template-Commit: {sha}", cwd=root)
    print(f"committed {subject}")
    return 0
