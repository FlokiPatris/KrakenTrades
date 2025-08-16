#!/usr/bin/env bash
# -------------------------
# 🐚 ShellCheck — Lint shell scripts → SARIF (CI-friendly)
# -------------------------
# - Strict mode, safe IFS, secure umask
# - Uses shared CI helpers for directory hardening and SARIF conversion
# - Outputs JSON and SARIF for GitHub Code Scanning
# -------------------------

set -Eeuo pipefail
IFS=$'\n\t'
umask 077
LC_ALL=C

source ".ci/bin/common.sh"
source ".ci/bin/sarif_utils.sh"

main() {
  # ----------------------------
  # Config (override via env)
  # ----------------------------
  local root_dir="${ROOT_DIR:-$(pwd)}"
  local sarif_dir="${SARIF_DIR:-${root_dir}/sarif-reports}"
  local severity="${SHELLCHECK_SEVERITY:-style}"       # error|warning|info|style
  local fail_on="${SHELLCHECK_FAIL_ON:-any}"           # any|none
  local globs="${SHELLCHECK_GLOBS:-*.sh}"
  local exclude_dirs="${SHELLCHECK_EXCLUDE_DIRS:-.git .venv venv node_modules vendor dist build .mypy_cache .pytest_cache}"
  local json_out="${sarif_dir}/shellcheck.json"
  local sarif_out="${sarif_dir}/shellcheck.sarif"
  local src_root="${GITHUB_WORKSPACE:-$root_dir}"

  ensure_dir_secure "${sarif_dir}"

  if ! command -v shellcheck >/dev/null 2>&1; then
    log_error "shellcheck not found. Install via: sudo apt-get install shellcheck"
    exit 127
  fi

  log_info "🔍 ShellCheck: severity=${severity} fail_on=${fail_on}"
  log_info "Root: ${root_dir}"
  log_info "Excludes: ${exclude_dirs}"
  log_info "Source root for SARIF: ${src_root}"

  # ----------------------------
  # Build find excludes
  # ----------------------------
  build_find_excludes() {
    local -a preds=()
    for d in ${exclude_dirs}; do
      preds+=(-path "${root_dir}/${d}" -prune -o)
    done
    printf '%s\n' "${preds[@]}"
  }

  # ----------------------------
  # Collect and scan
  # ----------------------------
  local rc=0
  if ! find "${root_dir}" $(build_find_excludes) -type f -name "${globs}" -print0 \
      | xargs -0 --no-run-if-empty shellcheck --severity="${severity}" --format=json >"${json_out}"; then
    rc=$?
  fi

  harden_artifact "${json_out}"

  # ----------------------------
  # Convert or write empty SARIF
  # ----------------------------
  if [[ -s "${json_out}" ]]; then
    local shellcheck_version
    shellcheck_version="$(shellcheck --version | awk '/version:/{print $2}')"
    SHELLCHECK_SRCROOT="${src_root}" \
      json_to_sarif "${json_out}" "${sarif_out}" "shellcheck" "${shellcheck_version}"
  else
    write_empty_sarif "${sarif_out}" "shellcheck" "$(shellcheck --version | awk '/version:/{print $2}')"
  fi

  harden_artifact "${sarif_out}"

  [[ "${fail_on}" == "none" ]] && return 0 || return "${rc}"
}

main "$@"
