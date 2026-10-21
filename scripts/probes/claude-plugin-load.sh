#!/usr/bin/env bash
# Maintainer probe: does Claude Code load the in-repo workbench plugin after the trust dialog?
# Exit 0 when workbench@workbench-template loads from <dir>/plugins/workbench and no other
# workbench plugin does; 1 on mismatch; 3 when the claude binary is absent.
set -euo pipefail

if ! command -v claude >/dev/null 2>&1; then
  echo "skipped: claude not found (install Claude Code to run this probe)" >&2
  exit 3
fi

repo="$(git rev-parse --show-toplevel)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
proj="$(cd "$tmp" && mkdir project && cd project && pwd -P)"
cfg="$tmp/config"
mkdir -p "$cfg"
git -C "$repo" archive HEAD | tar -x -C "$proj"

PROJ="$proj" python3 - >"$cfg/.claude.json" <<'PY'
import json, os
print(json.dumps({"projects": {os.environ["PROJ"]: {"hasTrustDialogAccepted": True}}}))
PY

echo "claude version: $(claude --version)"
out="$tmp/stream.jsonl"
(
  cd "$proj"
  CLAUDE_CONFIG_DIR="$cfg" CLAUDE_CODE_SYNC_PLUGIN_INSTALL=1 \
    claude -p --output-format stream-json --verbose --max-turns 1 "hi" >"$out" 2>"$tmp/stderr.txt"
) &
pid=$!
for _ in $(seq 1 120); do
  grep -q '"subtype":"init"' "$out" 2>/dev/null && break
  kill -0 "$pid" 2>/dev/null || break
  sleep 1
done
pkill -P "$pid" 2>/dev/null || true
kill "$pid" 2>/dev/null || true
wait "$pid" 2>/dev/null || true

PROJ="$proj" python3 - "$out" <<'PY'
import json, os, sys
proj = os.environ["PROJ"]
init = None
for line in open(sys.argv[1]):
    try:
        ev = json.loads(line)
    except ValueError:
        continue
    if ev.get("type") == "system" and ev.get("subtype") == "init":
        init = ev
        break
if init is None:
    print("FAIL: no system/init event captured", file=sys.stderr)
    sys.exit(1)
plugins = init.get("plugins", [])
print("loaded plugins:", [(p.get("name"), p.get("source")) for p in plugins])
wb = [p for p in plugins if "workbench" in str(p.get("name"))]
want = os.path.realpath(os.path.join(proj, "plugins", "workbench"))
ok = (
    len(wb) == 1
    and wb[0].get("name") == "workbench"
    and wb[0].get("source") == "workbench@workbench-template"
    and os.path.realpath(str(wb[0].get("path"))) == want
)
if not ok:
    print("FAIL: expected only workbench@workbench-template from <dir>/plugins/workbench", file=sys.stderr)
    sys.exit(1)
print("OK: workbench@workbench-template loaded from <dir>/plugins/workbench")
PY
