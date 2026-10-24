#!/usr/bin/env python3
"""Locate a workbench root and resolve components inside it.

Three tree shapes exist in the wild, and tooling must stop hardcoding paths:

  metarepo (preferred)     <root>/.gitmodules + <root>/code/<component>

  flat                     <root>/CLAUDE.md + <root>/<project>-<component>
                           (each component its own repo)

  legacy flat              <root>/<component>, no CLAUDE.md at root

Resolution order for the root:
  1. $WORKBENCH_ROOT               explicit override, always wins
  2. $CLAUDE_PROJECT_DIR           set by Claude Code per session
  3. walk up from cwd (or --from)  first dir that looks like a workbench
  4. git superproject of cwd       inside a component checkout code/<x>

Usage:
  workbench.py root [--from DIR]
  workbench.py kind [--from DIR]
  workbench.py components [--from DIR]
  workbench.py resolve <component> [--from DIR]
  workbench.py doctor [--from DIR]
  workbench.py scratchpad [--from DIR]   main checkout's .scratchpad, created
  workbench.py logs [--from DIR]         main checkout's .logs, created
  workbench.py config [--repo DIR] [--plans-root DIR --repo-name NAME]

Exit 0 on success, 1 when nothing resolves. `root` and `doctor` exit 0 with
`kind: none (uninitialised, no .gitmodules)` when no workbench exists yet.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

METAREPO = "metarepo"
FLAT = "flat"


def _is_metarepo(d: Path) -> bool:
    return (d / ".gitmodules").is_file() and (d / "code").is_dir()


def _is_flat_workbench(d: Path) -> bool:
    """A root holding several sibling git repos, marked as a workbench by CLAUDE.md."""
    if not (d / "CLAUDE.md").is_file():
        return False
    repos = [c for c in d.iterdir() if c.is_dir() and (c / ".git").exists()]
    return len(repos) >= 2


def detect_kind(d: Path) -> str | None:
    if _is_metarepo(d):
        return METAREPO
    if _is_flat_workbench(d):
        return FLAT
    return None


def find_root(start: Path | None = None) -> tuple[Path, str] | None:
    for env in ("WORKBENCH_ROOT", "CLAUDE_PROJECT_DIR"):
        val = os.environ.get(env)
        if val:
            p = Path(val).expanduser().resolve()
            kind = detect_kind(p)
            if kind:
                return p, kind

    cur = (start or Path.cwd()).expanduser().resolve()
    for d in [cur, *cur.parents]:
        kind = detect_kind(d)
        if kind:
            return d, kind
    # inside a component checkout the walk-up can miss the metarepo (symlinked
    # path, relocated checkout); the submodule's superproject still names it
    r = subprocess.run(
        ["git", "-C", str(cur), "rev-parse", "--show-superproject-working-tree"],
        capture_output=True,
        text=True,
    )
    if r.returncode == 0 and r.stdout.strip():
        sup = Path(r.stdout.strip()).resolve()
        if _is_metarepo(sup):
            return sup, METAREPO
    return None


def _git_out(cwd: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def main_checkout(start: Path | None = None) -> Path | None:
    """The main checkout holding .scratchpad and .logs; never a linked worktree.

    $WORKBENCH_ROOT, then $CLAUDE_PROJECT_DIR, else the parent of the git common
    dir of `start` (a submodule resolves through its superproject). None outside git.
    """
    for env in ("WORKBENCH_ROOT", "CLAUDE_PROJECT_DIR"):
        val = os.environ.get(env)
        if val:
            return Path(val).expanduser().resolve()
    cur = (start or Path.cwd()).expanduser().resolve()
    if not cur.is_dir():
        return None
    sup = _git_out(cur, "rev-parse", "--show-superproject-working-tree")
    if sup:
        cur = Path(sup).resolve()
    common = _git_out(cur, "rev-parse", "--path-format=absolute", "--git-common-dir")
    return Path(common).resolve().parent if common else None


def _state_dir(name: str, start: Path | None) -> Path | None:
    main = main_checkout(start)
    if main is None:
        return None
    d = main / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def scratchpad_dir(start: Path | None = None) -> Path | None:
    return _state_dir(".scratchpad", start)


def logs_dir(start: Path | None = None) -> Path | None:
    return _state_dir(".logs", start)


def components(root: Path, kind: str, require_git: bool = True) -> dict[str, Path]:
    """component name -> path.

    `require_git=False` accepts plain directories, for explicitly-supplied roots
    and test fixtures that are not real checkouts.
    """
    base = root / "code" if kind == METAREPO else root
    if not base.is_dir():
        return {}
    out = {}
    for child in sorted(base.iterdir()):
        if child.is_dir() and (not require_git or (child / ".git").exists()):
            out[child.name] = child
    return out


def resolve(root: Path, kind: str, name: str, require_git: bool = True) -> Path | None:
    comps = components(root, kind, require_git)
    if name in comps:
        return comps[name]
    # flat trees prefix components with the project name (<project>-<component>)
    suffix_hits = [p for n, p in comps.items() if n.endswith(f"-{name}")]
    if len(suffix_hits) == 1:
        return suffix_hits[0]
    return None


# ---- per-repo config: <repo>/.claude/workbench.json (the only reader) ----

DEFAULT_OVERLAP_IGNORE = [
    "*README.md",
    "MEMORY.md",
    "**/SKILL.md",
    "tests/README.md",
    "CHANGELOG.md",
]
CONFIG_KEYS = ("refRunners", "suites", "deploy", "overlapIgnore", "harness")
HARNESS_TARGETS = ("copilot", "cursor", "codex", "gemini", "antigravity")


class ConfigError(Exception):
    pass


HARNESS_DIRS = {
    "claude": ".claude",
    "copilot": ".github",
    "cursor": ".cursor",
    "codex": ".codex",
    "gemini": ".gemini",
    "antigravity": ".agents",
}


def _read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except (ValueError, OSError) as e:
        raise ConfigError(f"{path}: workbench.json: {e}") from e


def _config_dirs(root: Path) -> list[Path]:
    dirs = [Path(root) / d for d in HARNESS_DIRS.values()]
    return [d for d in dirs if (d / "workbench.json").is_file()]


def config_dir(root: Path) -> Path:
    """The one directory under root holding workbench.json (.claude when none)."""
    found = _config_dirs(root)
    if not found:
        return Path(root) / HARNESS_DIRS["claude"]
    if len(found) > 1:
        raise ConfigError(
            f"{root}: workbench.json found in more than one config dir: "
            + " and ".join(str(f) for f in found)
            + "; keep exactly one"
        )
    d = found[0]
    raw = _read_json(d / "workbench.json")
    h = raw.get("harness") if isinstance(raw, dict) else None
    active = h.get("active") if isinstance(h, dict) else None
    if active is not None and HARNESS_DIRS.get(active) != d.name:
        raise ConfigError(
            f"{d / 'workbench.json'}: harness.active is {active!r} but the file lives in "
            f"{d.name} (expected {HARNESS_DIRS.get(active, '?')})"
        )
    return d


def active_harness(root: Path) -> str:
    found = _config_dirs(root)
    if not found:
        return "claude"
    config_dir(root)
    raw = _read_json(found[0] / "workbench.json")
    h = raw.get("harness") if isinstance(raw, dict) else None
    return (h.get("active") if isinstance(h, dict) else None) or "claude"


def worktrees_dir(root: Path) -> Path:
    return config_dir(root) / "worktrees"


def worktree_markers() -> list[str]:
    return [f"{d}/worktrees/" for d in HARNESS_DIRS.values()] + [".worktrees/"]


def _git_top(d: Path) -> Path:
    d = d.expanduser().resolve()
    r = subprocess.run(
        ["git", "-C", str(d), "rev-parse", "--show-toplevel"], capture_output=True, text=True
    )
    return Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else d


def _is_str_list(v) -> bool:
    return isinstance(v, list) and all(isinstance(x, str) for x in v)


def _validate_harness(h, bad) -> dict:
    shape = '{"targets": [str], "models": {target: {alias: model}}, "active": harness}'
    if not isinstance(h, dict) or set(h) - {"targets", "models", "active"}:
        bad("harness", f"must be an object shaped {shape}")
    if "targets" not in h and "active" not in h:
        bad("harness", f"must be an object shaped {shape}")
    targets = h.get("targets", [])
    if not _is_str_list(targets):
        bad("harness", "targets must be a list of strings")
    for t in [*targets, *(h.get("models", {}) if isinstance(h.get("models", {}), dict) else [])]:
        if t not in HARNESS_TARGETS:
            bad("harness", f"unknown target {t!r} (allowed: {', '.join(HARNESS_TARGETS)})")
    models = h.get("models", {})
    if not isinstance(models, dict) or not all(
        isinstance(m, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in m.items())
        for m in models.values()
    ):
        bad("harness", "models must be an object of target to {alias: model string}")
    out = {"targets": list(targets), "models": {t: dict(m) for t, m in models.items()}}
    if "active" in h:
        if h["active"] not in HARNESS_DIRS:
            bad("harness", f"unknown active {h['active']!r} (allowed: {', '.join(HARNESS_DIRS)})")
        out["active"] = h["active"]
    return out


def _validate(raw, path: Path) -> dict:
    def bad(key: str, why: str):
        raise ConfigError(f"{path}: {key}: {why}")

    if not isinstance(raw, dict):
        bad("workbench.json", "must be a JSON object")
    for k in raw:
        if k not in CONFIG_KEYS:
            bad(k, f"unknown key (allowed: {', '.join(CONFIG_KEYS)})")
    rr = raw.get("refRunners", {})
    if not isinstance(rr, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in rr.items()
    ):
        bad("refRunners", "must be an object of glob to command string")
    suites = raw.get("suites", [])
    if not _is_str_list(suites):
        bad("suites", "must be a list of shell command strings")
    dep = raw.get("deploy", {})
    if dep != {} and not (
        isinstance(dep, dict)
        and set(dep) == {"command", "verify"}
        and all(isinstance(v, str) for v in dep.values())
    ):
        bad("deploy", "must be an object with string keys command and verify")
    ign = raw.get("overlapIgnore", [])
    if not _is_str_list(ign):
        bad("overlapIgnore", "must be a list of glob strings")
    harness = _validate_harness(raw["harness"], bad) if "harness" in raw else None
    return {
        "harness": harness or {"targets": [], "models": {}},
        "refRunners": dict(rr),
        "suites": list(suites),
        "deploy": dict(dep),
        "overlapIgnore": DEFAULT_OVERLAP_IGNORE + list(ign),
    }


def load_config(repo_dir: Path) -> dict:
    path = config_dir(_git_top(Path(repo_dir))) / "workbench.json"
    if not path.is_file():
        return _validate({}, path)
    return _validate(_read_json(path), path)


def config_for_repo(plans_root: Path, repo: str) -> dict:
    plans_root = Path(plans_root)
    found = find_root(plans_root)
    if found:
        comp = resolve(found[0], found[1], repo)
        if comp:
            return load_config(comp)
    return load_config(plans_root)


def _glob_re(pat: str) -> re.Pattern:
    out, i = "", 0
    while i < len(pat):
        if pat.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pat.startswith("**", i):
            out += ".*"
            i += 2
        elif pat[i] == "*":
            out += "[^/]*"
            i += 1
        elif pat[i] == "?":
            out += "[^/]"
            i += 1
        else:
            out += re.escape(pat[i])
            i += 1
    return re.compile(out + r"\Z")


def overlap_ignored(path: str, globs: list) -> bool:
    path = path.removeprefix("./")
    base = path.rsplit("/", 1)[-1]
    for g in globs:
        target = path if "/" in g else base
        if _glob_re(g).match(target):
            return True
    return False


PACKAGE_MARKERS = ("pyproject.toml", "package.json", "package.xml")
_NODE_EXT = (".js", ".mjs", ".cjs", ".ts")


def package_root(path: Path, stop: Path) -> Path:
    """Nearest dir at or above `path` (up to `stop`) holding a package marker, else `stop`."""
    path, stop = Path(path), Path(stop)
    d = path if path.is_dir() else path.parent
    while True:
        if any((d / m).is_file() for m in PACKAGE_MARKERS):
            return d
        if d == stop or d.parent == d:
            return stop
        try:
            d.relative_to(stop)
        except ValueError:
            return stop
        d = d.parent


def _uses_vitest(pkg_json: Path) -> bool:
    try:
        data = json.loads(pkg_json.read_text())
    except (ValueError, OSError):
        return False
    if not isinstance(data, dict):
        return False
    return any(
        isinstance(data.get(k), dict) and "vitest" in data[k]
        for k in ("dependencies", "devDependencies")
    )


def _declares_pytest(pkg: Path) -> bool:
    """True when the package locks or declares pytest (not a tool-only install)."""
    lock = pkg / "uv.lock"
    try:
        if re.search(r'^name = "pytest"\s*$', lock.read_text(), re.M):
            return True
    except OSError:
        return False
    try:
        import tomllib  # python 3.11+; hooks must import on 3.9, so only read toml lazily

        data = tomllib.loads((pkg / "pyproject.toml").read_text())
    except (ImportError, ValueError, OSError):
        return False
    proj = data.get("project", {})
    specs = list(proj.get("dependencies", []))
    for group in (proj.get("optional-dependencies", {}), data.get("dependency-groups", {})):
        for v in group.values():
            specs += [x for x in v if isinstance(x, str)]
    return any(re.match(r"\s*pytest\s*($|[\[<>=!~;@ ])", x) for x in specs)


def runner_for(ref: str, repo_dir: Path) -> dict | None:
    """{cwd, argv, source} that runs a `file::name` test ref from its package root."""
    repo_dir = Path(repo_dir)
    top = _git_top(repo_dir)
    file, _, name = ref.partition("::")
    file = file.removeprefix("./")
    pkg = package_root(top / file, top)
    rel = os.path.relpath(top / file, pkg)
    rel_ref = rel + (f"::{name}" if name else "")
    ext = Path(file).suffix
    vals = {"ref": rel_ref, "file": rel, "name": name, "pkg": pkg.name}
    for glob, tmpl in load_config(repo_dir)["refRunners"].items():
        if overlap_ignored(file, [glob]):
            cmd = re.sub(r"\{(ref|file|name|pkg)\}", lambda m: vals[m.group(1)], tmpl)
            return {"cwd": str(pkg), "argv": ["bash", "-c", cmd], "source": "refRunners"}
    argv = None
    if ext == ".bats":
        argv = ["bats", *(["-f", name] if name else []), rel]
    elif (pkg / "pyproject.toml").is_file() and ext == ".py":
        argv = (
            ["uv", "run", "--frozen", "pytest", rel_ref, "-q"]
            if (pkg / "uv.lock").is_file() and _declares_pytest(pkg)
            else ["pytest", rel_ref, "-q"]
        )
    elif (pkg / "package.json").is_file() and ext in _NODE_EXT:
        if _uses_vitest(pkg / "package.json"):
            argv = ["npx", "vitest", "run", rel, *(["-t", name] if name else [])]
        else:
            argv = ["node", "--test", *(["--test-name-pattern", name] if name else []), rel]
    elif (pkg / "package.xml").is_file() and ext == ".py":
        argv = ["pytest", rel_ref, "-q"]
    elif pkg == top and not any((pkg / m).is_file() for m in PACKAGE_MARKERS):
        if ext == ".py":
            argv = ["pytest", rel_ref, "-q"]
        elif ext in _NODE_EXT:
            argv = ["node", "--test", *(["--test-name-pattern", name] if name else []), rel]
    if argv is None:
        return None
    return {"cwd": str(pkg), "argv": argv, "source": "builtin"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "action",
        choices=[
            *("root", "kind", "components", "resolve", "doctor"),
            *("config", "runner", "config-dir", "scratchpad", "logs"),
        ],
    )
    ap.add_argument("name", nargs="?")
    ap.add_argument("--from", dest="start", type=Path, default=None)
    ap.add_argument("--repo", type=Path, default=None)
    ap.add_argument("--plans-root", type=Path, default=None)
    ap.add_argument("--repo-name", default=None)
    args = ap.parse_args()

    if args.action == "runner":
        if not args.name:
            print("workbench.py: runner needs a test ref", file=sys.stderr)
            return 1
        try:
            got = runner_for(args.name, args.repo or Path.cwd())
        except ConfigError as e:
            print(f"workbench.py: {e}", file=sys.stderr)
            return 1
        if got is None:
            print(f"workbench.py: no runner for {args.name}", file=sys.stderr)
            return 2
        print(json.dumps(got))
        return 0

    if args.action == "config":
        try:
            if args.plans_root:
                cfg = config_for_repo(args.plans_root, args.repo_name or "")
            else:
                cfg = load_config(args.repo or Path.cwd())
        except ConfigError as e:
            print(f"workbench.py: {e}", file=sys.stderr)
            return 1
        print(json.dumps(cfg))
        return 0

    if args.action in ("scratchpad", "logs"):
        d = (scratchpad_dir if args.action == "scratchpad" else logs_dir)(args.start)
        if d is None:
            print("workbench.py: no main checkout found (not inside git)", file=sys.stderr)
            return 1
        print(d)
        return 0

    found = find_root(args.start)
    if not found and args.action in ("root", "doctor"):
        print("kind: none (uninitialised, no .gitmodules)")
        return 0
    if not found:
        print(
            "workbench: no root found. Set WORKBENCH_ROOT, or run inside a tree with "
            "either .gitmodules+code/ or CLAUDE.md+sibling repos.",
            file=sys.stderr,
        )
        return 1
    root, kind = found

    if args.action == "config-dir":
        try:
            print(config_dir(root))
        except ConfigError as e:
            print(f"workbench.py: {e}", file=sys.stderr)
            return 1
    elif args.action == "root":
        print(root)
    elif args.action == "kind":
        print(kind)
    elif args.action == "components":
        for n, p in components(root, kind).items():
            print(f"{n}\t{p}")
    elif args.action == "resolve":
        if not args.name:
            print("workbench: resolve needs a component name", file=sys.stderr)
            return 1
        p = resolve(root, kind, args.name)
        if not p:
            known = ", ".join(components(root, kind)) or "(none)"
            print(
                f"workbench: no component {args.name!r} under {root}. Known: {known}",
                file=sys.stderr,
            )
            return 1
        print(p)
    elif args.action == "doctor":
        comps = components(root, kind)
        print(f"root:       {root}")
        print(f"kind:       {kind}")
        print(f"components: {len(comps)}")
        for n, p in comps.items():
            try:
                br = subprocess.run(
                    ["git", "-C", str(p), "rev-parse", "--abbrev-ref", "HEAD"],
                    capture_output=True,
                    text=True,
                ).stdout.strip()
                rem = subprocess.run(
                    ["git", "-C", str(p), "remote"], capture_output=True, text=True
                ).stdout.split()
                warn = "  !! NO REMOTE" if not rem else ""
                print(f"  {n:34} {br:28}{warn}")
            except Exception as e:  # pragma: no cover
                print(f"  {n:34} (git error: {e})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
