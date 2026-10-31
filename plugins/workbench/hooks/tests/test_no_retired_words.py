"""Pin: the plugin no longer mentions the retired plan-execute machinery."""

import re
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2]
DIRS = ["skills", "hooks", "rules", "agents"]
RETIRED = re.compile(
    r"plan-execute|heartbeat|hook-probe|verify-task|approvals ledger|approvals\.json"
    r"|apply-run|ticket\.py continue|ticket\.py rule|forward-merge|per-task worktree"
    r"|named copy|Workflow tool",
    re.IGNORECASE,
)


def test_plugin_has_no_retired_words():
    offenders = []
    for d in DIRS:
        for path in sorted((PLUGIN / d).rglob("*")):
            if not path.is_file() or "tests" in path.relative_to(PLUGIN).parts:
                continue
            if "__pycache__" in path.parts:
                continue
            try:
                text = path.read_text()
            except UnicodeDecodeError:
                continue
            for n, line in enumerate(text.splitlines(), 1):
                if RETIRED.search(line):
                    offenders.append(f"{path.relative_to(PLUGIN)}:{n}: {line.strip()[:100]}")
    assert not offenders, "retired words found:\n" + "\n".join(offenders)
