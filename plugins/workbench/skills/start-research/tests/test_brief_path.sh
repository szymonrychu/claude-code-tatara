#!/usr/bin/env bash
# Plain-bash fallback for test_brief_path.bats, for use when bats is unavailable.
set -u

SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/scripts/brief_path.sh"
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
cat > "$WB/.gitmodules" <<EOF
[submodule "foo"]
	path = code/foo
	url = x
	branch = main
EOF

today="$(date +%F)"

out="$(cd "$WB" && bash "$SCRIPT" "My Topic" 2>&1)"; status=$?
assert_status "$status" 0 "brief_path exits 0 for a normal topic"
assert_eq "$out" "$WB/docs/research/$today-my-topic.md" "brief_path builds dated slug path"
if [ -d "$WB/docs/research" ]; then ok "brief_path creates the research dir"; else fail "research dir not created"; fi

out="$(cd "$WB" && bash "$SCRIPT" "Keycloak OIDC & PKCE!!" 2>&1)"; status=$?
assert_status "$status" 0 "brief_path exits 0 for a special-char topic"
assert_contains "$out" "-keycloak-oidc-pkce.md" "brief_path slugs and collapses separators"

out="$(cd "$WB" && bash "$SCRIPT" "" 2>&1)"; status=$?
assert_status "$status" 1 "brief_path exits non-zero for an empty topic"

out="$(cd "$WB" && bash "$SCRIPT" "!!!" 2>&1)"; status=$?
assert_status "$status" 1 "brief_path exits non-zero when slug is empty"

PLAIN="$TMPDIR_ROOT/plain"
mkdir -p "$PLAIN"
git -C "$PLAIN" init -q
top="$(git -C "$PLAIN" rev-parse --show-toplevel)"
out="$(cd "$PLAIN" && bash "$SCRIPT" "My Topic" 2>&1)"; status=$?
assert_status "$status" 0 "brief_path works in a plain git repo"
assert_eq "$out" "$top/docs/research/$today-my-topic.md" "brief_path uses the git toplevel in a plain repo"

echo "----"
echo "passed: $PASS failed: $FAIL"
[ "$FAIL" -eq 0 ]
