#!/usr/bin/env python3
"""Move the workbench config dir to the active harness's own directory (D22, gate answer Q4).

    migrate.py <harness> [--root DIR]    harness is a key of HARNESS_DIRS; `claude` moves back

Moves workbench.json, settings.local.json, harness-manifest.json and worktrees/ from the
current config dir to HARNESS_DIRS[harness] and sets (or, for claude, clears) harness.active.
Claude-specific files and files a generator owns in the target dir are never touched. Refuses,
moving nothing, while a registered git worktree lives under the current worktrees/ or the
destination holds a different workbench-owned file. Same harness twice is a no-op.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

OWNED = ("workbench.json", "settings.local.json", "harness-manifest.json", "worktrees")


class MigrateError(Exception):
    pass


def _core():
    path = Path(__file__).resolve().parents[2] / "plugins/workbench/scripts/lib/workbench.py"
    spec = importlib.util.spec_from_file_location("_workbench_core_migrate", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _registered_worktrees(root: Path) -> list[Path]:
    r = subprocess.run(
        ["git", "-C", str(root), "worktree", "list", "--porcelain"], capture_output=True, text=True
    )
    if r.returncode != 0:
        return []
    return [
        Path(line[len("worktree ") :]).resolve()
        for line in r.stdout.splitlines()
        if line.startswith("worktree ")
    ]


def _same(a: Path, b: Path) -> bool:
    return a.is_file() and b.is_file() and a.read_bytes() == b.read_bytes()


def _set_active(path: Path, harness: str) -> None:
    cfg = json.loads(path.read_text())
    h = cfg.setdefault("harness", {})
    if harness == "claude":
        h.pop("active", None)
        if not h:
            del cfg["harness"]
    else:
        h["active"] = harness
    path.write_text(json.dumps(cfg, indent=2) + "\n")


def migrate(root: Path, harness: str) -> Path:
    """Move the config dir to `harness`'s directory; returns it. Raises MigrateError on refusal."""
    core = _core()
    root = Path(root).resolve()
    if harness not in core.HARNESS_DIRS:
        raise MigrateError(f"unknown harness {harness!r} (known: {', '.join(core.HARNESS_DIRS)})")
    dst = root / core.HARNESS_DIRS[harness]
    found = core._config_dirs(root)
    if dst in found and len(found) > 1:
        raise MigrateError(
            f"{dst / 'workbench.json'} already exists next to another workbench.json "
            f"({', '.join(str(f) for f in found if f != dst)}); nothing moved"
        )
    src = core.config_dir(root)
    if not (src / "workbench.json").is_file():
        raise MigrateError(f"{src}: no workbench.json to migrate")
    if src == dst:
        _set_active(dst / "workbench.json", harness)
        return dst
    wt = (src / "worktrees").resolve()
    live = [p for p in _registered_worktrees(root) if p != root and wt in p.parents]
    if live:
        raise MigrateError(
            f"{len(live)} git worktree(s) live under {src / 'worktrees'} "
            f"({', '.join(str(p) for p in live)}); merge or remove them first"
        )
    for name in OWNED:
        s, d = src / name, dst / name
        if not s.exists() or not d.exists():
            continue
        if not _same(s, d):
            raise MigrateError(f"{d} already exists and differs from {s}; nothing moved")
    dst.mkdir(parents=True, exist_ok=True)
    for name in OWNED:
        s, d = src / name, dst / name
        if not s.exists():
            continue
        if d.exists():
            d.unlink()
        shutil.move(str(s), str(d))
    _set_active(dst / "workbench.json", harness)
    for d in (src,):
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
    return dst


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="migrate", description=__doc__.split("\n\n")[0])
    p.add_argument("harness")
    p.add_argument("--root", type=Path, default=Path.cwd())
    a = p.parse_args(argv)
    try:
        print(migrate(a.root, a.harness))
    except (MigrateError, OSError, ValueError, _core().ConfigError) as e:
        print(f"migrate: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
