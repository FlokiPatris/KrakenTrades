#!/usr/bin/env bash
# -------------------------
# 🐚 ShellCheck — Lint shell scripts → SARIF (CI-friendly)
# -------------------------
set -Eeuo pipefail
IFS=$'\n\t'
umask 077
LC_ALL=C

ROOT_DIR="${ROOT_DIR:-$(pwd)}"
SARIF_DIR="${SARIF_DIR:-${ROOT_DIR}/sarif-reports}"
SEVERITY="${SHELLCHECK_SEVERITY:-style}"
FAIL_ON="${SHELLCHECK_FAIL_ON:-any}"
GLOBS="${SHELLCHECK_GLOBS:-*.sh}"
EXCLUDE_DIRS="${SHELLCHECK_EXCLUDE_DIRS:-.git .venv venv node_modules vendor dist build .mypy_cache .pytest_cache}"
JSON_OUT="${SARIF_DIR}/shellcheck.json"
NORMALIZED_JSON="${SARIF_DIR}/shellcheck.normalized.json"
SARIF_OUT="${SARIF_DIR}/shellcheck.sarif"
SRC_ROOT="${GITHUB_WORKSPACE:-$ROOT_DIR}"

mkdir -p "$SARIF_DIR"
chmod 700 "$SARIF_DIR"

log_info()  { printf '[INFO] %s\n' "$*" >&2; }
log_error() { printf '[ERROR] %s\n' "$*" >&2; }

# Ensure shellcheck is installed
if ! command -v shellcheck >/dev/null 2>&1; then
  log_error "shellcheck not found."
  exit 127
fi

log_info "🔍 ShellCheck: severity=$SEVERITY fail_on=$FAIL_ON"
log_info "Root: $ROOT_DIR"
log_info "Source root for SARIF: $SRC_ROOT"

# Build find excludes
build_find_excludes() {
  local -a preds=()
  for d in $EXCLUDE_DIRS; do
    preds+=(-path "$ROOT_DIR/$d" -prune -o)
  done
  printf '%s\n' "${preds[@]}"
}

rc=0
: > "$JSON_OUT"

if ! find "$ROOT_DIR" $(build_find_excludes) -type f -name "$GLOBS" -print0 \
  | xargs -0 --no-run-if-empty shellcheck --severity="$SEVERITY" --format=json >"$JSON_OUT"; then
  rc=$?
  if [[ $rc -ne 0 && $rc -ne 1 ]]; then
    log_error "ShellCheck failed with exit code $rc"
  fi
fi
chmod 600 "$JSON_OUT"

# Normalise to {comments:[…]} if it's a JSON array
if [[ -s "$JSON_OUT" ]]; then
  if command -v jq >/dev/null 2>&1 && jq -e 'type=="array"' "$JSON_OUT" >/dev/null; then
    jq -c '{comments: .}' "$JSON_OUT" >"$NORMALIZED_JSON"
  else
    first_char=$(tr -d '\r\n\t ' <"$JSON_OUT" | head -c1)
    if [[ "$first_char" == "[" ]]; then
      { printf '{"comments":'; cat "$JSON_OUT"; printf '}\n'; } >"$NORMALIZED_JSON"
    else
      cp "$JSON_OUT" "$NORMALIZED_JSON"
    fi
  fi
else
  printf '{"comments":[]}\n' >"$NORMALIZED_JSON"
fi
chmod 600 "$NORMALIZED_JSON"

# Convert to SARIF using Python converter
if [[ -s "$NORMALIZED_JSON" ]] && grep -q '"file"' "$NORMALIZED_JSON"; then
  python3 .ci/bin/shellcheck_to_sarif.py "$NORMALIZED_JSON" "$SARIF_OUT" "shellcheck" "$(shellcheck --version | awk '/version:/{print $2}')"
else
  log_info "No ShellCheck findings — creating empty SARIF"
  python3 - <<EOF
import json, sys
sarif = {"version": "$SARIF_VERSION", "runs": [{"tool": {"driver": {"name": "shellcheck", "version": "$(shellcheck --version | awk '/version:/{print $2}')", "informationUri": "https://www.shellcheck.net/", "rules": []}}, "results": []}]}
json.dump(sarif, open("$SARIF_OUT","w"), indent=2)
EOF
fi
chmod 600 "$SARIF_OUT"

[[ "$FAIL_ON" == "none" ]] && exit 0 || exit "$rc"
