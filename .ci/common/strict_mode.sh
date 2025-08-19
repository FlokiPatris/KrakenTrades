#!/usr/bin/env bash
# strict_mode.sh — Enable strict shell flags and provide tiny logging helpers.
#
# Usage:
#   source ".ci/common/strict_mode.sh"
#
# Purpose:
#   - Fail-fast behavior for CI scripts
#   - Safe IFS and predictable shell environment
#   - Timestamped logging helpers: log_info, log_warn, log_error, die
#   - Avoid leaking secrets by default

# -------------------------------
# Strict shell options
# -------------------------------
set -Eeuo pipefail         # Exit on errors, undefined variables, and failed pipes
IFS=$'\n\t'                # Safe word splitting

# Make shell more predictable in certain environments
shopt -s lastpipe 2>/dev/null || true
umask 077                   # Restrictive default file creation permissions

# -------------------------------
# Locale fallback
# -------------------------------
export LC_ALL="${LC_ALL:-C.UTF-8}"
export LANG="${LANG:-C.UTF-8}"

# -------------------------------
# Logging helpers
# -------------------------------
_ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log_info()  { printf '[%s] [INFO]  %s\n' "$(_ts)" "$*" >&2; }
log_warn()  { printf '[%s] [WARN]  %s\n' "$(_ts)" "$*" >&2; }
log_error() { printf '[%s] [ERROR] %s\n' "$(_ts)" "$*" >&2; }
die()       { log_error "$*"; exit 1; }

# -------------------------------
# Error trapping for CI observability
# -------------------------------
trap 'rc=$?; log_error "Error in ${BASH_SOURCE[0]} at line ${LINENO}: exit ${rc}"; exit ${rc}' ERR
