#!/usr/bin/env bash
# ShellCheck runner with secure defaults, CI-ready SARIF, and safe file handling.
# - Strict mode, safe IFS, and umask 077
# - Finds .sh files robustly (null-delimited), supports directory excludes
# - Writes SARIF to a locked-down folder when format=sarif
# - Configurable via env vars (see .env.example)

set -euo pipefail
IFS=$'\n\t'
umask 077

# ----------------------------
# Config (overridable via env)
# ----------------------------
: "${ROOT_DIR:="$(pwd)"}"
: "${SARIF_DIR:="${ROOT_DIR}/sarif-reports"}"
: "${SHELLCHECK_FORMAT:="${CI:+sarif}"}"  # 'sarif' in CI, 'tty' locally by default
: "${SHELLCHECK_SEVERITY:=style}"        # error|warning|info|style
: "${SHELLCHECK_FAIL_ON:=any}"           # any|none (none = don’t fail build)
: "${SHELLCHECK_GLOBS:=*.sh}"            # file name pattern
# Default excludes for common junk dirs; override with space-separated names
: "${SHELLCHECK_EXCLUDE_DIRS:=".git .venv venv node_modules vendor dist build .mypy_cache .pytest_cache"}"

# ----------------------------
# Preflight
# ----------------------------
if ! command -v shellcheck >/dev/null 2>&1; then
  echo "ERROR: shellcheck not found. Install via: 'sudo apt-get install shellcheck' (Debian/Ubuntu) or 'brew install shellcheck' (macOS)." >&2
  exit 127
fi

# Only create SARIF dir if needed
if [[ "${SHELLCHECK_FORMAT}" == "sarif" ]]; then
  mkdir -p "${SARIF_DIR}"
  chmod 700 "${SARIF_DIR}"
fi

# Compute excluded path predicates for find (null-delimited safe)
build_find_excludes() {
  local -a preds=()
  for d in ${SHELLCHECK_EXCLUDE_DIRS}; do
    preds+=(-path "${ROOT_DIR}/${d}" -prune -o)
  done
  printf '%s\n' "${preds[@]}"
}

# Collect candidate files, null-delimited, honoring excludes
collect_targets() {
  # shellcheck disable=SC2046
  find "${ROOT_DIR}" $(build_find_excludes) -type f -name "${SHELLCHECK_GLOBS}" -print0
}

# ----------------------------
# Run ShellCheck
# ----------------------------
scan() {
  local -a args=(--severity="${SHELLCHECK_SEVERITY}")
  case "${SHELLCHECK_FORMAT}" in
    sarif) args+=(--format=sarif) ;;
    tty|"") args+=(--format=tty) ;;
    checkstyle) args+=(--format=checkstyle) ;;
    gcc) args+=(--format=gcc) ;;
    *) echo "WARN: Unknown format '${SHELLCHECK_FORMAT}', defaulting to tty." >&2; args+=(--format=tty) ;;
  esac

  local sarif_out=
  if [[ "${SHELLCHECK_FORMAT}" == "sarif" ]]; then
    sarif_out="${SARIF_DIR}/shellcheck.sarif"
  fi

  local rc=0
  if [[ -n "${sarif_out}" ]]; then
    # Read files safely and stream single shellcheck run to SARIF
    # We pass files as arguments in batches to avoid huge command lines.
    # For simplicity and portability: run once with xargs -0 (safe).
    if ! collect_targets | xargs -0 --no-run-if-empty shellcheck "${args[@]}" >"${sarif_out}"; then
      rc=$?
    fi
    chmod 600 "${sarif_out}" || true
    echo "ShellCheck SARIF written to: ${sarif_out}"
  else
    if ! collect_targets | xargs -0 --no-run-if-empty shellcheck "${args[@]}"; then
      rc=$?
    fi
  fi

  # Control failure behavior
  if [[ "${SHELLCHECK_FAIL_ON}" == "none" ]]; then
    return 0
  fi
  return "${rc}"
}

echo "🔍 ShellCheck: format=${SHELLCHECK_FORMAT} severity=${SHELLCHECK_SEVERITY} fail_on=${SHELLCHECK_FAIL_ON}"
echo "Root: ${ROOT_DIR}"
echo "Excludes: ${SHELLCHECK_EXCLUDE_DIRS}"

scan
