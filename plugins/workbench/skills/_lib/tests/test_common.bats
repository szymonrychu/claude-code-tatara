#!/usr/bin/env bats

setup() {
  LIB="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)/common.sh"
  WB="$BATS_TEST_TMPDIR/workbench"
  mkdir -p "$WB/code/foo" "$WB/code/bar"
  cat > "$WB/.gitmodules" <<'EOF'
[submodule "foo"]
	path = code/foo
	url = https://example.com/foo.git
	branch = develop
[submodule "bar"]
	path = code/bar
	url = https://example.com/bar.git
EOF
  git -C "$WB/code/foo" init -q
  source "$LIB"
}

@test "repo_root finds workbench root from cwd" {
  cd "$WB"
  run repo_root
  [ "$status" -eq 0 ]
  [ "$output" = "$WB" ]
}

@test "repo_root finds workbench root from subdir" {
  cd "$WB/code/foo"
  run repo_root
  [ "$status" -eq 0 ]
  [ "$output" = "$WB" ]
}

@test "repo_root fails when no workbench found" {
  # source an isolated copy so the script-location fallback can't find
  # this real repo (BASH_SOURCE is read-only, can't fake it directly)
  EMPTY="$BATS_TEST_TMPDIR/empty"
  ISO="$BATS_TEST_TMPDIR/isolated_lib"
  mkdir -p "$EMPTY" "$ISO"
  cp "$LIB" "$ISO/common.sh"
  cd "$EMPTY"
  run bash -c "source '$ISO/common.sh'; repo_root"
  [ "$status" -ne 0 ]
}

@test "all_repos lists submodules from .gitmodules" {
  cd "$WB"
  run all_repos
  [ "$status" -eq 0 ]
  [ "$(echo "$output" | sed -n 1p)" = "foo" ]
  [ "$(echo "$output" | sed -n 2p)" = "bar" ]
}

@test "all_repos falls back to code/ dirs when .gitmodules has no entries" {
  WB2="$BATS_TEST_TMPDIR/wb2"
  mkdir -p "$WB2/code/alpha" "$WB2/code/beta"
  : > "$WB2/.gitmodules"
  cd "$WB2"
  run all_repos
  [ "$status" -eq 0 ]
  [ "$(echo "$output" | sed -n 1p)" = "alpha" ]
  [ "$(echo "$output" | sed -n 2p)" = "beta" ]
}

@test "resolve_repo echoes abs path for known submodule" {
  cd "$WB"
  run resolve_repo foo
  [ "$status" -eq 0 ]
  [ "$output" = "$WB/code/foo" ]
}

@test "resolve_repo fails with stderr for unknown repo" {
  cd "$WB"
  run resolve_repo nope
  [ "$status" -ne 0 ]
  [[ "$output" == *"unknown repo"* ]]
}

@test "tracked_branch returns explicit branch" {
  cd "$WB"
  run tracked_branch foo
  [ "$status" -eq 0 ]
  [ "$output" = "develop" ]
}

@test "tracked_branch defaults to main" {
  cd "$WB"
  run tracked_branch bar
  [ "$status" -eq 0 ]
  [ "$output" = "main" ]
}

@test "worktree_path builds expected path" {
  cd "$WB"
  run worktree_path my-branch foo
  [ "$status" -eq 0 ]
  [ "$output" = "$WB/.worktrees/my-branch/foo" ]
}

@test "report_add and report_print render table" {
  report_add foo ok "up to date"
  report_add bar skipped "no changes"
  run report_print
  [ "$status" -eq 0 ]
  [[ "$output" == *"foo"*"ok"*"up to date"* ]]
  [[ "$output" == *"bar"*"skipped"*"no changes"* ]]
}

@test "report_failed returns success (0) when a repo failed" {
  report_add foo ok "up to date"
  report_add bar failed "non-fast-forward"
  run report_failed
  [ "$status" -eq 0 ]
}

@test "report_failed returns failure (1) when no repo failed" {
  report_add foo ok "up to date"
  report_add bar skipped "no changes"
  run report_failed
  [ "$status" -eq 1 ]
}

@test "log_info/log_warn/log_err write to stderr with prefix" {
  run bash -c "source '$LIB'; log_info hello 2>&1 1>/dev/null"
  [[ "$output" == *"[INFO]"*"hello"* ]]
  run bash -c "source '$LIB'; log_warn hello 2>&1 1>/dev/null"
  [[ "$output" == *"[WARN]"*"hello"* ]]
  run bash -c "source '$LIB'; log_err hello 2>&1 1>/dev/null"
  [[ "$output" == *"[ERR]"*"hello"* ]]
}

@test "common.sh refuses to run directly" {
  run bash "$LIB"
  [ "$status" -ne 0 ]
  [[ "$output" == *"must be sourced"* ]]
}

@test "docs_root echoes the workbench root inside a workbench" {
  cd "$WB/code/foo"
  run docs_root
  [ "$status" -eq 0 ]
  [ "$output" = "$WB" ]
}

@test "docs_root falls back to the git toplevel of a plain repo" {
  REPO="$BATS_TEST_TMPDIR/plain"
  ISO="$BATS_TEST_TMPDIR/isolated_lib"
  mkdir -p "$REPO/sub" "$ISO"
  git -C "$REPO" init -q
  cp "$LIB" "$ISO/common.sh"
  expected="$(git -C "$REPO" rev-parse --show-toplevel)"
  cd "$REPO/sub"
  run bash -c "source '$ISO/common.sh'; docs_root"
  [ "$status" -eq 0 ]
  [ "$output" = "$expected" ]
}

@test "docs_root fails outside a workbench and a git repo" {
  EMPTY="$BATS_TEST_TMPDIR/empty"
  ISO="$BATS_TEST_TMPDIR/isolated_lib"
  mkdir -p "$EMPTY" "$ISO"
  cp "$LIB" "$ISO/common.sh"
  cd "$EMPTY"
  run bash -c "source '$ISO/common.sh'; docs_root 2>&1"
  [ "$status" -ne 0 ]
  [[ "$output" == *"docs root not found (no workbench and not a git repo)"* ]]
}

@test "slugify lowercases and collapses non-alphanumeric runs" {
  run slugify "Keycloak OIDC & PKCE!!"
  [ "$status" -eq 0 ]
  [ "$output" = "keycloak-oidc-pkce" ]
}

@test "slugify trims leading and trailing dashes" {
  run slugify "  --Hello World--  "
  [ "$output" = "hello-world" ]
}

@test "slugify yields an empty string for no alphanumerics" {
  run slugify "!!!"
  [ "$output" = "" ]
}

@test "slugify caps at 60 chars with no trailing dash" {
  run slugify "$(printf 'a%.0s' $(seq 1 59)) tail"
  [ "${#output}" -le 60 ]
  [[ "$output" != *- ]]
  [ "$output" = "$(printf 'a%.0s' $(seq 1 59))" ]
}

# Shared with test_common.py: text|max (empty = default 60)|expected.
@test "slugify shared case table" {
  local texts=("Keycloak OIDC & PKCE!!" "  --Hello World--  " $'a   b\t\tc' "one,two;three.four" "MiXeD CaSe 42" "Zażółć gęślą Jaźń" "!!!" "$(printf 'word %.0s' $(seq 1 14))" "abcdefg hij" "abcdefgh ij" "Epic title that is rather long indeed" "$(printf 'x%.0s' $(seq 1 70))")
  local maxes=("" "" "" "" "" "" "" "" 8 9 28 28)
  local want=("keycloak-oidc-pkce" "hello-world" "a-b-c" "one-two-three-four" "mixed-case-42" "za-g-l-ja" "" "$(printf 'word-%.0s' $(seq 1 11))word" "abcdefg" "abcdefgh" "epic-title-that-is-rather-lo" "$(printf 'x%.0s' $(seq 1 28))")
  local i got
  for i in "${!texts[@]}"; do
    if [ -z "${maxes[$i]}" ]; then got="$(slugify "${texts[$i]}")"; else got="$(slugify "${texts[$i]}" "${maxes[$i]}")"; fi
    [ "$got" = "${want[$i]}" ] || { echo "case $i: got '$got' want '${want[$i]}'"; return 1; }
  done
}
