#!/usr/bin/env bash
# Plain-bash fallback for test_common.bats, for use when bats is unavailable.
set -u

LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/common.sh"
TMPDIR_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_ROOT"' EXIT

PASS=0
FAIL=0

ok() {
  PASS=$((PASS + 1))
  echo "ok - $1"
}

fail() {
  FAIL=$((FAIL + 1))
  echo "not ok - $1"
}

assert_eq() {
  if [ "$1" = "$2" ]; then
    ok "$3"
  else
    fail "$3 (expected [$2] got [$1])"
  fi
}

assert_status() {
  if [ "$1" -eq "$2" ]; then
    ok "$3"
  else
    fail "$3 (expected status $2 got $1)"
  fi
}

assert_contains() {
  case "$1" in
    *"$2"*) ok "$3" ;;
    *) fail "$3 (expected [$1] to contain [$2])" ;;
  esac
}

new_workbench() {
  local wb="$TMPDIR_ROOT/workbench_$$_$RANDOM"
  mkdir -p "$wb/code/foo" "$wb/code/bar"
  cat > "$wb/.gitmodules" <<'EOF'
[submodule "foo"]
	path = code/foo
	url = https://example.com/foo.git
	branch = develop
[submodule "bar"]
	path = code/bar
	url = https://example.com/bar.git
EOF
  git -C "$wb/code/foo" init -q
  echo "$wb"
}

WB="$(new_workbench)"

out="$( cd "$WB" && source "$LIB" && repo_root )"
assert_eq "$out" "$WB" "repo_root finds workbench root from cwd"

out="$( cd "$WB/code/foo" && source "$LIB" && repo_root )"
assert_eq "$out" "$WB" "repo_root finds workbench root from subdir"

EMPTY="$TMPDIR_ROOT/empty"
ISO="$TMPDIR_ROOT/isolated_lib"
mkdir -p "$EMPTY" "$ISO"
cp "$LIB" "$ISO/common.sh"
( cd "$EMPTY" && source "$ISO/common.sh" && repo_root ) >/dev/null 2>&1
assert_status "$?" 1 "repo_root fails when no workbench found"

out="$( cd "$WB" && source "$LIB" && all_repos )"
assert_eq "$(echo "$out" | sed -n 1p)" "foo" "all_repos first entry from .gitmodules"
assert_eq "$(echo "$out" | sed -n 2p)" "bar" "all_repos second entry from .gitmodules"

WB2="$TMPDIR_ROOT/wb2"
mkdir -p "$WB2/code/alpha" "$WB2/code/beta"
: > "$WB2/.gitmodules"
out="$( cd "$WB2" && source "$LIB" && all_repos )"
assert_eq "$(echo "$out" | sed -n 1p)" "alpha" "all_repos fallback first dir"
assert_eq "$(echo "$out" | sed -n 2p)" "beta" "all_repos fallback second dir"

out="$( cd "$WB" && source "$LIB" && resolve_repo foo )"
assert_eq "$out" "$WB/code/foo" "resolve_repo echoes abs path for known submodule"

out="$( cd "$WB" && source "$LIB" && resolve_repo nope 2>&1 1>/dev/null )"
assert_contains "$out" "unknown repo" "resolve_repo stderr message for unknown repo"
( cd "$WB" && source "$LIB" && resolve_repo nope ) >/dev/null 2>&1
assert_status "$?" 1 "resolve_repo fails (nonzero) for unknown repo"

out="$( cd "$WB" && source "$LIB" && tracked_branch foo )"
assert_eq "$out" "develop" "tracked_branch returns explicit branch"

out="$( cd "$WB" && source "$LIB" && tracked_branch bar )"
assert_eq "$out" "main" "tracked_branch defaults to main"

out="$( cd "$WB" && source "$LIB" && worktree_path my-branch foo )"
assert_eq "$out" "$WB/.worktrees/my-branch/foo" "worktree_path builds expected path"

out="$( source "$LIB"; report_add foo ok "up to date"; report_add bar skipped "no changes"; report_print )"
assert_contains "$out" "foo" "report_print contains repo foo"
assert_contains "$out" "skipped" "report_print contains status skipped"

( source "$LIB"; report_add foo ok "up to date"; report_add bar failed "non-fast-forward"; report_failed )
assert_status "$?" 0 "report_failed returns 0 when a repo failed"

( source "$LIB"; report_add foo ok "up to date"; report_add bar skipped "no changes"; report_failed )
assert_status "$?" 1 "report_failed returns 1 when no repo failed"

out="$( source "$LIB"; log_info hello 2>&1 1>/dev/null )"
assert_contains "$out" "[INFO]" "log_info prefixes with [INFO]"

out="$( source "$LIB"; log_warn hello 2>&1 1>/dev/null )"
assert_contains "$out" "[WARN]" "log_warn prefixes with [WARN]"

out="$( source "$LIB"; log_err hello 2>&1 1>/dev/null )"
assert_contains "$out" "[ERR]" "log_err prefixes with [ERR]"

bash "$LIB" >/dev/null 2>&1
assert_status "$?" 1 "common.sh refuses to run directly"

out="$( cd "$WB/code/foo" && source "$LIB" && docs_root )"
assert_eq "$out" "$WB" "docs_root echoes the workbench root inside a workbench"

PLAIN="$TMPDIR_ROOT/plain"
mkdir -p "$PLAIN/sub"
git -C "$PLAIN" init -q
expected="$(git -C "$PLAIN" rev-parse --show-toplevel)"
out="$( cd "$PLAIN/sub" && source "$ISO/common.sh" && docs_root )"
assert_eq "$out" "$expected" "docs_root falls back to the git toplevel of a plain repo"

out="$( cd "$EMPTY" && source "$ISO/common.sh" && docs_root 2>&1 )"; st=$?
assert_status "$st" 1 "docs_root fails outside a workbench and a git repo"
assert_contains "$out" "docs root not found (no workbench and not a git repo)" "docs_root explains the failure"

out="$( source "$LIB"; slugify "Keycloak OIDC & PKCE!!" )"
assert_eq "$out" "keycloak-oidc-pkce" "slugify lowercases and collapses runs"
out="$( source "$LIB"; slugify "  --Hello World--  " )"
assert_eq "$out" "hello-world" "slugify trims leading and trailing dashes"
out="$( source "$LIB"; slugify "!!!" )"
assert_eq "$out" "" "slugify is empty for no alphanumerics"
long="$(printf 'a%.0s' $(seq 1 59))"
out="$( source "$LIB"; slugify "$long tail" )"
assert_eq "$out" "$long" "slugify caps at 60 chars with no trailing dash"

echo "----"
echo "passed: $PASS failed: $FAIL"
[ "$FAIL" -eq 0 ]
