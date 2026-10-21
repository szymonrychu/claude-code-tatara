#!/usr/bin/env bash
# PostToolUse Edit|Write auto-format. Best-effort: never blocks, never errors the turn.
f=$(jq -r '.tool_input.file_path // .tool_response.filePath // empty' 2>/dev/null) || f=""
[ -z "$f" ] && exit 0
[ -f "$f" ] || exit 0

case "$f" in
  *.py)
    command -v ruff >/dev/null 2>&1 && { ruff check --fix -q "$f"; ruff format -q "$f"; } ;;
  *.go)
    command -v gofmt >/dev/null 2>&1 && gofmt -w "$f" ;;
  *.tf|*.tfvars)
    command -v terraform >/dev/null 2>&1 && terraform fmt "$f" ;;
esac 2>/dev/null || true
exit 0
