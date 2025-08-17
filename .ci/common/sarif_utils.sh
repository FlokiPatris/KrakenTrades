#!/usr/bin/env bash
#
# sarif_utils.sh — Reusable SARIF helpers for CI scripts.
# Source AFTER strict_mode.sh and config.sh:
#   source ".ci/common/strict_mode.sh"
#   source ".ci/common/config.sh"
#   source ".ci/common/sarif_utils.sh"
#
# Exposed functions:
#  - log_info|log_warn|log_error|die  (strict_mode.sh provides these)
#  - require_tools <tool>...
#  - ensure_sarif_dir
#  - make_tmp
#  - secure_move <src> <dst>
#  - json_validate <file>
#  - repo_root
#
# Security notes:
#  - SARIF files are written under SARIF_OUT_DIR
#  - SARIF files are chmod 600 and SARIF directories are chmod 700
#  - Tempfiles are cleaned on EXIT via trap

# shellcheck disable=SC1090

# --- Logging wrappers (delegated to strict_mode.sh) ---
# log_info, log_warn, log_error, die are expected to exist

# --- Tool availability checker ---
require_tools() {
  local missing=0
  for tool in "$@"; do
    if ! command -v "$tool" >/dev/null 2>&1; then
      log_error "Required tool not found in PATH: $tool"
      missing=1
    fi
  done
  if [[ $missing -ne 0 ]]; then
    die "Missing required tools; aborting."
  fi
}

# --- SARIF output directory handling ---
ensure_sarif_dir() {
  local dir="${1:-${SARIF_OUT_DIR:-./sarif-reports}}"
  umask 077
  mkdir -p "$dir"
  chmod 700 "$dir" || true
  printf "%s" "$dir"
}

# --- Secure move / permission helpers ---
secure_move() {
  local src="$1" dst="$2"
  if [[ -z "$src" || -z "$dst" ]]; then
    die "secure_move requires <src> and <dst>"
  fi
  if [[ ! -s "$src" ]]; then
    die "secure_move: source missing or empty: $src"
  fi
  umask 077
  mv -f -- "$src" "$dst"
  chmod 600 "$dst" 2>/dev/null || true
}

harden_file() {
  local f="$1"
  [[ -e "$f" ]] || return 0
  chmod 600 "$f" 2>/dev/null || true
}

# --- Tempfile helpers & cleanup ---
_tmpfiles=()
make_tmp() {
  local tmp
  tmp="$(mktemp -t ci.XXXXXX)" || die "mktemp failed"
  _tmpfiles+=("$tmp")
  printf "%s" "$tmp"
}
_cleanup_tmpfiles() {
  for f in "${_tmpfiles[@]:-}"; do
    [[ -e "$f" ]] && rm -f -- "$f" || true
  done
}
trap _cleanup_tmpfiles EXIT

# --- Optional JSON validation ---
json_validate() {
  local file="$1"
  if [[ -z "$file" ]]; then
    die "json_validate requires a filename"
  fi
  if ! [[ -s "$file" ]]; then
    log_warn "json_validate: file empty or missing: $file"
    return 1
  fi
  if command -v jq >/dev/null 2>&1; then
    jq empty "$file" 2>/dev/null || { log_error "Invalid JSON: $file"; return 1; }
  else
    log_warn "jq not found; skipping strict JSON validation for $file"
  fi
  return 0
}

# --- Repo root helper ---
repo_root() {
  if git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
    printf "%s" "$git_root"
  else
    printf "%s" "${GITHUB_WORKSPACE:-$(pwd)}"
  fi
}
