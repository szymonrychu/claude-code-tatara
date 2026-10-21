#!/usr/bin/env bash
# Plain-bash fallback for test_doc_path.bats, for use when bats is unavailable.
set -u

SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/scripts/doc_path.sh"
TMPDIR_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_ROOT"' EXIT

PASS=0
FAIL=0
ok() { PASS=$((PASS + 1)); echo "ok - $1"; }
fail() { FAIL=$((FAIL + 1)); echo "not ok - $1"; }
assert_status() { if [ "$1" -eq "$2" ]; then ok "$3"; else fail "$3 (expected status $2 got $1)"; fi; }
assert_eq() { if [ "$1" = "$2" ]; then ok "$3"; else fail "$3 (expected [$2] got [$1])"; fi; }
assert_contains() { case "$1" in *"$2"*) ok "$3" ;; *) fail "$3 (expected [$1] to contain [$2])" ;; esac; }

WB="$TMPDIR_ROOT/workbench"
mkdir -p "$WB/code/foo"
cat > "$WB/.gitmodules" <<EOF2
[submodule "foo"]
	path = code/foo
	url = x
	branch = main
EOF2

today="$(date +%F)"

for kind in design plan record; do
  out="$(cd "$WB" && bash "$SCRIPT" "$kind" "My Topic" 2>&1)"; status=$?
  assert_status "$status" 0 "doc_path $kind exits 0"
  assert_eq "$out" "$WB/docs/plans/$today-my-topic-$kind.md" "doc_path $kind builds dated .md path"
done
if [ -d "$WB/docs/plans" ]; then ok "doc_path creates docs/plans"; else fail "docs/plans not created"; fi

out="$(cd "$WB" && bash "$SCRIPT" tasks "My Topic" 2>&1)"
assert_eq "$out" "$WB/docs/plans/$today-my-topic-tasks.json" "doc_path tasks ends in .json"

out="$(cd "$WB" && bash "$SCRIPT" approvals "My Topic" 2>&1)"
assert_eq "$out" "$WB/docs/plans/$today-my-topic-approvals.json" "doc_path approvals ends in .json"

out="$(cd "$WB" && bash "$SCRIPT" research "My Topic" 2>&1)"
assert_eq "$out" "$WB/docs/research/$today-my-topic.md" "doc_path research uses the research dir"
if [ -d "$WB/docs/research" ]; then ok "doc_path creates the research dir"; else fail "research dir not created"; fi

out="$(cd "$WB/code/foo" && bash "$SCRIPT" plan "My Topic" 2>&1)"
assert_eq "$out" "$WB/docs/plans/$today-my-topic-plan.md" "doc_path from code/<repo> resolves to the workbench"
if [ ! -d "$WB/code/foo/docs" ]; then ok "doc_path leaves the submodule untouched"; else fail "docs dir created inside submodule"; fi

PLAIN="$TMPDIR_ROOT/plain"
mkdir -p "$PLAIN"
git -C "$PLAIN" init -q
top="$(git -C "$PLAIN" rev-parse --show-toplevel)"
out="$(cd "$PLAIN" && bash "$SCRIPT" design "My Topic" 2>&1)"
assert_eq "$out" "$top/docs/plans/$today-my-topic-design.md" "doc_path works in a plain git repo"

out="$(cd "$WB" && bash "$SCRIPT" bogus "My Topic" 2>&1)"; status=$?
assert_status "$status" 1 "doc_path exits 1 on an unknown kind"
assert_contains "$out" "usage:" "doc_path prints usage on an unknown kind"

(cd "$WB" && bash "$SCRIPT" plan >/dev/null 2>&1); assert_status "$?" 1 "doc_path exits 1 on a missing topic"
out="$(cd "$WB" && bash "$SCRIPT" plan "" 2>&1)"; status=$?
assert_status "$status" 1 "doc_path exits 1 on an empty topic"
assert_contains "$out" "usage:" "doc_path prints usage on an empty topic"
(cd "$WB" && bash "$SCRIPT" plan "!!!" >/dev/null 2>&1); assert_status "$?" 1 "doc_path exits 1 on an empty slug"

echo "----"
echo "passed: $PASS failed: $FAIL"
[ "$FAIL" -eq 0 ]
