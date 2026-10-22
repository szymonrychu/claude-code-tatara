"""init update: merge the template's tooling into a workbench, minus the template's own docs."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import owned
import project_files
from finalize import TEMPLATE_MARKET, load_wb
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
    return {
        (cfg / rel).as_posix() if rel in cfg_names else rel for rel in owned.GENERATED_ON_CONFLICT
    }


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


def cmd_update(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    preflight(root)
    sha = fetch_template(root, args.url, args.branch)
    short = sha[:12]
    if git("merge-base", "--is-ancestor", sha, "HEAD", cwd=root, check=False).returncode == 0:
        print(f"up to date with template/{args.branch} {short}")
        return 0
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
