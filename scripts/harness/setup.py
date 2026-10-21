#!/usr/bin/env python3
"""harness-setup: write, check or clean the generated files of the chosen harness targets (D4).

    setup.py                       sync the AGENTS.md generated blocks and regenerate every
                                   recorded target (idempotent; the way to rebuild the rules block)
    setup.py <target>... | all     write the targets plus the shared skills, record the targets
    setup.py --check               regenerate the recorded targets in memory; exit 1 on drift
    setup.py --clean <target>      remove only the files that target wrote (migrates the
                                   config dir back to claude first when it is the active one)

One target also migrates the config dir to that harness's directory (D22); `claude` migrates it
back and writes nothing; several targets or `all` write without migrating and print the config dir.
The migration is a repo-wide choice (tracked workbench.json): a teammate on another harness adds
`--no-migrate` so one target is generated without moving the config dir or changing harness.active.

Ownership is a manifest, `harness-manifest.json`, in the resolved config dir. Unknown target: 2.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    sys.path[:] = [
        str(SCRIPTS),
        *(p for p in sys.path[1:] if Path(p or ".").resolve() != Path(__file__).resolve().parent),
    ]

from harness import agents_md, emit, migrate  # noqa: E402
from harness.skills_emit import SkillError, render_skills  # noqa: E402
from harness.sources import load_sources  # noqa: E402

MANIFEST = "harness-manifest.json"
PATH_RULE_TARGETS = {"codex", "gemini"}


def _core():
    path = SCRIPTS.parent / "plugins/workbench/scripts/lib/workbench.py"
    spec = importlib.util.spec_from_file_location("_workbench_core", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _read(path: Path) -> dict:
    return json.loads(path.read_text()) if path.is_file() else {}


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def _render(sources, targets: list[str], reg) -> dict[str, dict[str, str]]:
    """target -> {path: text}; every target also owns the shared skills output."""
    skills = render_skills(sources)
    return {t: {**skills, **reg[t].render(sources)} for t in targets}


def _prune(root: Path, rel: str) -> None:
    f = root / rel
    f.unlink(missing_ok=True)
    for d in f.parents:
        if d == root or any(d.iterdir()):
            break
        d.rmdir()


def _toplevel(start: Path) -> Path:
    r = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"], capture_output=True, text=True
    )
    return Path(r.stdout.strip()) if r.returncode == 0 and r.stdout.strip() else start


def _check(root: Path, cdir: Path, reg) -> int:
    recorded = _read(cdir / "workbench.json").get("harness", {}).get("targets", [])
    targets = [t for t in recorded if t in reg]
    owned = _read(cdir / MANIFEST)
    drift: set[str] = set()
    wanted: dict[str, set[str]] = {}
    for t, files in _render(load_sources(root), targets, reg).items():
        wanted[t] = set(files)
        for rel, text in files.items():
            f = root / rel
            if not f.is_file() or f.read_text() != text:
                drift.add(rel)
    for t in targets:
        drift.update(
            rel for rel in owned.get(t, []) if rel not in wanted[t] and (root / rel).exists()
        )
    if agents_md.sync(root, bool(PATH_RULE_TARGETS & set(recorded)), write=False):
        drift.add("AGENTS.md")
    for rel in sorted(drift):
        print(rel)
    if drift:
        print(
            f"harness drift in {len(drift)} file(s); run `mise run harness-setup`", file=sys.stderr
        )
    return 1 if drift else 0


def _write(root: Path, cdir: Path, names: list[str], reg) -> int:
    targets = sorted(reg) if names == ["all"] else names
    unknown = [t for t in targets if t not in reg]
    if unknown:
        print(
            f"unknown target(s): {', '.join(unknown)} (known: {', '.join(sorted(reg))})",
            file=sys.stderr,
        )
        return 2
    rendered = _render(load_sources(root), targets, reg)
    owned = _read(cdir / MANIFEST)
    for t, files in rendered.items():
        for rel, text in files.items():
            f = root / rel
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(text)
        stale = set(owned.get(t, [])) - set(files)
        others = {r for o, fs in owned.items() if o != t for r in fs} | {
            r for o, fs in rendered.items() if o != t for r in fs
        }
        for rel in sorted(stale - others):
            _prune(root, rel)
        owned[t] = sorted(files)
    cfg_path = cdir / "workbench.json"
    cfg = _read(cfg_path)
    h = cfg.setdefault("harness", {})
    h["targets"] = [*h.get("targets", []), *(t for t in targets if t not in h.get("targets", []))]
    _write_json(cfg_path, cfg)
    _write_json(cdir / MANIFEST, owned)
    agents_md.sync(root, bool(PATH_RULE_TARGETS & set(h["targets"])))
    return 0


def _sync(root: Path, cdir: Path, reg) -> int:
    """No-argument form: rebuild the AGENTS.md blocks and rewrite every recorded target."""
    recorded = _read(cdir / "workbench.json").get("harness", {}).get("targets", [])
    targets = [t for t in recorded if t in reg]
    if targets:
        return _write(root, cdir, targets, reg)
    agents_md.sync(root, False)
    return 0


def _clean(root: Path, cdir: Path, target: str, reg) -> int:
    if target not in reg:
        print(f"unknown target: {target} (known: {', '.join(sorted(reg))})", file=sys.stderr)
        return 2
    owned = _read(cdir / MANIFEST)
    mine = owned.pop(target, [])
    kept = {r for fs in owned.values() for r in fs}
    for rel in mine:
        if rel not in kept:
            _prune(root, rel)
    cfg_path = cdir / "workbench.json"
    cfg = _read(cfg_path)
    if "targets" in cfg.get("harness", {}):
        cfg["harness"]["targets"] = [t for t in cfg["harness"]["targets"] if t != target]
        if not cfg["harness"]["targets"]:  # leave the file as it was before the first setup
            del cfg["harness"]["targets"]
            if not cfg["harness"]:
                del cfg["harness"]
        _write_json(cfg_path, cfg)
    if owned:
        _write_json(cdir / MANIFEST, owned)
    else:
        (cdir / MANIFEST).unlink(missing_ok=True)
    left = _read(cfg_path).get("harness", {}).get("targets", [])
    agents_md.sync(root, bool(PATH_RULE_TARGETS & set(left)))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="harness-setup", description=__doc__.split("\n\n")[0])
    p.add_argument("targets", nargs="*", help="target names, or `all`")
    p.add_argument(
        "--check", action="store_true", help="exit 1 listing generated files that drifted"
    )
    p.add_argument(
        "--no-migrate",
        action="store_true",
        help="with one target: generate it without moving the config dir (repo-wide choice)",
    )
    p.add_argument("--clean", metavar="TARGET", help="remove the files TARGET wrote")
    p.add_argument("--root", type=Path, default=None, help="repo root (default: git toplevel)")
    a = p.parse_args(argv)
    if sum([bool(a.targets), a.check, bool(a.clean)]) > 1:
        p.error("give targets, or exactly one of --check / --clean TARGET")
    root = (a.root or _toplevel(Path.cwd())).resolve()
    reg = emit.registry()
    try:
        core = _core()
        if a.targets == ["claude"]:
            if a.no_migrate:
                p.error("`claude` only migrates back; --no-migrate does not apply to it")
            print(migrate.migrate(root, "claude"))
            return 0
        cdir = core.config_dir(root)
        if a.check:
            return _check(root, cdir, reg)
        if a.clean:
            if a.clean in reg and core.active_harness(root) == a.clean:
                cdir = migrate.migrate(root, "claude")
            return _clean(root, cdir, a.clean, reg)
        if not a.targets:
            return _sync(root, cdir, reg)
        rc = _write(root, cdir, a.targets, reg)
        if rc == 0:
            single = len(a.targets) == 1 and a.targets != ["all"] and not a.no_migrate
            print(migrate.migrate(root, a.targets[0]) if single else cdir)
        return rc
    except (SkillError, ValueError, OSError, migrate.MigrateError, core.ConfigError) as e:
        print(f"harness-setup: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
