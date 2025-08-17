#!/usr/bin/env bash
# strict_mode.sh — Enable strict shell flags and tiny logging helpers.
#
# Source this as the very first file in any CI script:
#   source ".ci/common/strict_mode.sh"
#
# Purpose:
# - Enforce fail-fast behavior: set -Eeuo pipefail
# - Use safe IFS
# - Provide log_info / log_warn / log_error / die helpers
# - Prevent leaking secrets to logs by default (no echo of envs here)

set -Eeuo pipefail
IFS=$'\n\t'
# make shell more predictable in some environments
shopt -s lastpipe 2>/dev/null || true
umask 077

# Locale fallback (avoids Unicode surprises in some CI images)
export LC_ALL="${LC_ALL:-C.UTF-8}"
export LANG="${LANG:-C.UTF-8}"

# Timestamped logging helpers (send to stderr)
_ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log_info()  { printf '[%s] [INFO]  %s\n' "$(_ts)" "$*" >&2; }
log_warn()  { printf '[%s] [WARN]  %s\n' "$(_ts)" "$*" >&2; }
log_error() { printf '[%s] [ERROR] %s\n' "$(_ts)" "$*" >&2; }
die()       { log_error "$*"; exit 1; }

# Trap ERR and print contextual info for CI observability
trap 'rc=$?; log_error "Error in ${BASH_SOURCE[0]} at line ${LINENO}: exit ${rc}"; exit ${rc}' ERR
