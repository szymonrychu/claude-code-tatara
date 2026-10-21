#!/usr/bin/env python3
"""Run the repo's configured deploy command, then its verify command (phase 6).

Usage: deploy-hook.py [--repo <dir>] [--dry-run]
Config comes only from load_config (the config dir's workbench.json, key "deploy").
"""

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts" / "lib"))
import workbench  # noqa: E402


def run_step(label: str, command: str, cwd: Path) -> bool:
    p = subprocess.run(
        ["bash", "-c", command], cwd=cwd, capture_output=True, text=True, check=False
    )
    if p.returncode == 0:
        print(f"{label} ok")
        return True
    print(f"{label} FAIL exit {p.returncode}")
    out = (p.stdout + p.stderr).splitlines()
    print("\n".join(out[-20:]))
    return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    try:
        repo = Path(workbench._git_top(Path(args.repo)))
        deploy = workbench.load_config(repo)["deploy"]
    except workbench.ConfigError as e:
        print(f"deploy: config error: {e}")
        return 1
    if not deploy:
        print("deploy: none configured")
        return 0
    if args.dry_run:
        print(f"DEPLOY would run: {deploy['command']}")
        print(f"VERIFY would run: {deploy['verify']}")
        return 0
    if not run_step("DEPLOY", deploy["command"], repo):
        return 1
    return 0 if run_step("VERIFY", deploy["verify"], repo) else 1


if __name__ == "__main__":
    sys.exit(main())
