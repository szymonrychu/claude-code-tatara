"""Every in-flight plan of this repo is already plan.md: the migrator has nothing to change."""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
PLANS = REPO / "docs" / "plans"
TICKET = REPO / "plugins" / "superpowers" / "scripts" / "ticket.py"


def test_inflight_plans_stay_on_plan_md():
    r = subprocess.run(
        [sys.executable, str(TICKET), "migrate", "--all", "--dry-run", "--root", str(PLANS)],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "migrate: nothing to change", r.stdout
    dirs = [d for phase in ("todo", "in-progress") for d in (PLANS / phase).iterdir() if d.is_dir()]
    assert dirs
    missing = [str(d.relative_to(REPO)) for d in dirs if not (d / "plan.md").is_file()]
    assert not missing, missing
