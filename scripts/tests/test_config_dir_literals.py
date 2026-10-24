"""Guard: no literal `.claude` config path in plugin or script code (design D22).

The resolver `workbench.py` owns the config dir; Claude-specific paths and Claude-only
workflow scripts are exempt.
"""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOKEN = re.compile(r"\.claude(?!-plugin)")
SPECIFIC = re.compile(
    r"\.claude/(?:settings(?:\.local)?\.json|rules|skills|agents)"
    r"|\.claude['\"]\s*/\s*['\"](?:settings(?:\.local)?\.json|rules|skills|agents)"
    r"|[\"']\.claude[\"']\s*/\s*[\"'](?:projects|settings(?:\.local)?\.json)"
    r"|code\.claude\.com"
    r"|\.claude\.json"
)
EXEMPT_FILES = {
    "plugins/workbench/scripts/lib/workbench.py",
}
EXEMPT_DIRS = ()


def _tracked():
    out = subprocess.run(
        ["git", "ls-files", "plugins", "scripts"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    for rel in out:
        if not rel.endswith((".py", ".sh", ".js", ".mjs")):
            continue
        parts = rel.split("/")
        if "tests" in parts or Path(rel).name.startswith("test_"):
            continue
        if rel in EXEMPT_FILES or rel.startswith(EXEMPT_DIRS):
            continue
        yield rel


def test_no_literal_config_dir_in_code():
    hits = []
    for rel in _tracked():
        for n, line in enumerate((ROOT / rel).read_text().splitlines(), 1):
            if TOKEN.search(line) and not SPECIFIC.search(line):
                hits.append(f"{rel}:{n}: {line.strip()}")
    assert not hits, "literal .claude path; use the workbench.py resolver:\n" + "\n".join(hits)
