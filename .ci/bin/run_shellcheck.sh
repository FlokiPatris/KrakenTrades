#!/usr/bin/env bash
# -------------------------
# 🐚 ShellCheck — Lint shell scripts → SARIF (CI-friendly)
# -------------------------
# - Strict mode, safe IFS, secure umask
# - Uses shared CI helpers for directory hardening and SARIF conversion
# - Scans *.sh and executable shebang'd shell scripts
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
  local severity="${SHELLCHECK_SEVERITY:-warning}"     # error|warning|info|style (warning is a good default in CI)
  local fail_on="${SHELLCHECK_FAIL_ON:-any}"           # any|none
  local globs="${SHELLCHECK_GLOBS:-*.sh}"              # space-separated patterns, e.g. "*.sh *.bash"
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
  log_info "ShellCheck version: $(shellcheck --version | awk '/version:/{print $2}')"

  # ----------------------------
  # Helpers
  # ----------------------------
  build_find_excludes() {
    # Produces: -path root/.git -prune -o -path root/.venv -prune -o ...
    local -a preds=()
    for d in ${exclude_dirs}; do
      preds+=(-path "${root_dir}/${d}" -prune -o)
    done
    printf '%s\n' "${preds[@]}"
  }

  # ----------------------------
  # Discover files to lint
  # ----------------------------
  local -a files=()
  # 1) By glob(s)
  read -r -a patterns <<< "${globs}"
  if ((${#patterns[@]} > 0)); then
    # Build a name expression: -name p1 -o -name p2 ...
    local -a name_expr=()
    for p in "${patterns[@]}"; do
      [[ ${#name_expr[@]} -gt 0 ]] && name_expr+=(-o)
      name_expr+=(-name "$p")
    done
    # Use find with excludes
    while IFS= read -r -d '' f; do
      files+=("$f")
    done < <(
      # shellcheck disable=SC2046
      find "${root_dir}" $(build_find_excludes) -type f \( "${name_expr[@]}" \) -print0
    )
  fi

  # 2) Executables with a shell shebang
  while IFS= read -r -d '' f; do
    if head -n1 "$f" | grep -qE '^#!.*\b(bash|sh|dash|ksh|zsh)\b'; then
      files+=("$f")
    fi
  done < <(
    # shellcheck disable=SC2046
    find "${root_dir}" $(build_find_excludes) -type f -perm -u+x -print0
  )

  # Deduplicate while preserving order
  if ((${#files[@]} > 0)); then
    declare -A seen=()
    local -a uniq=()
    for f in "${files[@]}"; do
      [[ -n "${seen[$f]:-}" ]] && continue
      seen["$f"]=1
      uniq+=("$f")
    done
    files=("${uniq[@]}")
  fi

  log_info "Lint targets (${#files[@]}):"
  if ((${#files[@]} > 0)); then
    printf '%s\n' "${files[@]}" | sed 's/^/ • /'
  else
    log_info "No matching shell scripts found (globs='${globs}')."
  fi

  # ----------------------------
  # Run ShellCheck
  # ----------------------------
  local rc=0
  : > "${json_out}"  # create/truncate
  if ((${#files[@]} > 0)); then
    # shellcheck disable=SC2086
    if ! shellcheck --severity="${severity}" --format=json "${files[@]}" >"${json_out}"; then
      rc=$?
      # ShellCheck exits 1 when it found issues; keep JSON content for conversion
      if [[ $rc -ne 1 && $rc -ne 0 ]]; then
        log_error "ShellCheck failed with exit code ${rc}"
      fi
    fi
  else
    printf '[]\n' > "${json_out}"
  fi

  harden_artifact "${json_out}"

  # ----------------------------
  # Convert or write empty SARIF
  # ----------------------------
  local shellcheck_version
  shellcheck_version="$(shellcheck --version | awk '/version:/{print $2}')"

  if [[ -s "${json_out}" && "$(wc -c <"${json_out}")" -gt 3 && "$(head -c 1 "${json_out}")" != "" ]]; then
    SHELLCHECK_SRCROOT="${src_root}" \
      json_to_sarif "${json_out}" "${sarif_out}" "shellcheck" "${shellcheck_version}"
  else
    write_empty_sarif "${sarif_out}" "shellcheck" "${shellcheck_version}"
  fi

  harden_artifact "${sarif_out}"

  [[ "${fail_on}" == "none" ]] && return 0 || return "${rc}"
}

main "$@"
