#!/usr/bin/env bats

setup() {
  SCRIPT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)/scripts/brief_path.sh"
  WB="$BATS_TEST_TMPDIR/workbench"
  mkdir -p "$WB/code/foo"
  cat > "$WB/.gitmodules" <<EOF
[submodule "foo"]
	path = code/foo
	url = x
	branch = main
EOF
}

@test "brief_path builds a dated slug path under the research dir" {
  cd "$WB"
  run bash "$SCRIPT" "My Topic"
  [ "$status" -eq 0 ]
  today="$(date +%F)"
  [ "$output" = "$WB/docs/research/$today-my-topic.md" ]
  [ -d "$WB/docs/research" ]
}

@test "brief_path slugs special chars and collapses separators" {
  cd "$WB"
  run bash "$SCRIPT" "Keycloak OIDC & PKCE!!"
  [ "$status" -eq 0 ]
  [[ "$output" == *"-keycloak-oidc-pkce.md" ]]
}

@test "brief_path fails on an empty topic" {
  cd "$WB"
  run bash "$SCRIPT" ""
  [ "$status" -ne 0 ]
}

@test "brief_path fails when the topic has no alphanumerics" {
  cd "$WB"
  run bash "$SCRIPT" "!!!"
  [ "$status" -ne 0 ]
}

@test "brief_path caps the slug at 60 chars with no trailing dash" {
  cd "$WB"
  run bash "$SCRIPT" "$(printf 'a%.0s' $(seq 1 100)) tail"
  [ "$status" -eq 0 ]
  name="${output##*/}"; name="${name%.md}"; name="${name#????-??-??-}"
  [ "${#name}" -le 60 ]
  [[ "$name" != *- ]]
}

@test "brief_path works in a plain git repo" {
  # the script finds the workbench that contains it, so the plain-repo fallback only exists
  # in the uninitialised template (no code/ and .gitmodules above the script)
  root="$(cd "$(dirname "$SCRIPT")/../../../../.." && pwd)"
  if [ -d "$root/code" ] && [ -f "$root/.gitmodules" ]; then
    skip "the script lives inside an initialised workbench"
  fi
  REPO="$BATS_TEST_TMPDIR/plain"
  mkdir -p "$REPO"
  git -C "$REPO" init -q
  expected="$(git -C "$REPO" rev-parse --show-toplevel)"
  cd "$REPO"
  run bash "$SCRIPT" "My Topic"
  [ "$status" -eq 0 ]
  [ "$output" = "$expected/docs/research/$(date +%F)-my-topic.md" ]
  [ -d "$expected/docs/research" ]
}
