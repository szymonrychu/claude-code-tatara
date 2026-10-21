#!/usr/bin/env python3
"""Report whether the workbench is initialised and whether another `workbench` plugin collides.

Usage: doctor.py [--root DIR] [--user-settings FILE]

Prints the core `workbench.py doctor` output, `state:`, `plugins:` and `packs:` lines. When the
user settings enable a plugin named `workbench` from another marketplace, writes
`"workbench@<marketplace>": false` into <config_dir>/settings.local.json (never the user file).
Exit 0 unless the tree is broken, then 1 naming the problem on stderr.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "workbench" / "scripts" / "lib"))
import workbench as wb  # noqa: E402

BEGIN = "<!-- workbench:uninitialised:begin -->"
END = "<!-- workbench:uninitialised:end -->"


class Broken(Exception):
    pass


def _json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text())
    except (ValueError, OSError) as e:
        raise Broken(f"{path}: {e}") from e
    if not isinstance(data, dict):
        raise Broken(f"{path}: must be a JSON object")
    return data


def core_doctor(root: Path) -> None:
    env = {k: v for k, v in os.environ.items() if k not in ("WORKBENCH_ROOT", "CLAUDE_PROJECT_DIR")}
    script = Path(wb.__file__).resolve()
    r = subprocess.run(
        [sys.executable, str(script), "doctor", "--from", str(root)],
        capture_output=True,
        text=True,
        env=env,
    )
    sys.stdout.write(r.stdout)
    if r.returncode != 0:
        raise Broken(f"workbench.py doctor failed: {r.stderr.strip()}")


def collisions(user_file: Path, market: str) -> list[str]:
    if not user_file.is_file():
        return []
    enabled = _json(user_file).get("enabledPlugins", {})
    if not isinstance(enabled, dict):
        return []
    return sorted(
        k
        for k, v in enabled.items()
        if v is True and k.startswith("workbench@") and k != f"workbench@{market}"
    )


def write_overrides(root: Path, keys: list[str]) -> None:
    try:
        local = wb.config_dir(root) / "settings.local.json"
    except wb.ConfigError as e:
        raise Broken(str(e)) from e
    data = _json(local) if local.is_file() else {}
    enabled = data.setdefault("enabledPlugins", {})
    new = [k for k in keys if enabled.get(k) is not False]
    if not new:
        return
    for k in new:
        enabled[k] = False
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_text(json.dumps(data, indent=2) + "\n")
    for k in new:
        print(f'wrote "{k}": false to {local}')


def run(root: Path, user_file: Path) -> None:
    agents = root / "AGENTS.md"
    if not agents.is_file():
        raise Broken(f"{agents}: AGENTS.md is missing")
    core_doctor(root)
    text = agents.read_text()
    state = "uninitialised" if BEGIN in text and END in text else "initialised"
    print(f"state: {state}")

    market = _json(root / ".claude-plugin" / "marketplace.json")
    mname = market.get("name", "")
    names = {p["name"] for p in market.get("plugins", [])}
    settings = _json(root / ".claude" / "settings.json")
    enabled = settings.get("enabledPlugins", {})
    if not isinstance(enabled, dict):
        raise Broken(f"{root / '.claude' / 'settings.json'}: enabledPlugins must be an object")
    listed = {k.split("@", 1)[0] for k in enabled if k.endswith(f"@{mname}")}
    if listed != names:
        diff = sorted(listed ^ names)
        raise Broken(
            f"marketplace {mname!r} and .claude/settings.json disagree on plugins: "
            + ", ".join(diff)
        )
    on = sorted(k for k, v in enabled.items() if v is True)
    print("plugins: " + (", ".join(on) or "(none)"))
    print("packs: " + (", ".join(k for k in on if k.startswith("workbench-")) or "(none)"))

    write_overrides(root, collisions(user_file, mname))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument(
        "--user-settings", type=Path, default=Path("~/.claude/settings.json").expanduser()
    )
    args = ap.parse_args()
    try:
        run(args.root.resolve(), args.user_settings)
    except Broken as e:
        print(f"doctor: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
