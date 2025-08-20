#!/usr/bin/env bash
#
# sarif_utils.sh — Reusable SARIF helpers for CI/CD pipelines
#
# Usage:
#   source ".ci/common/sarif_utils.sh"
#   ensure_sarif_dir
#
# Provides secure helpers for:
#   - Logging (delegated to strict_mode.sh)
#   - Ensuring required CLI tools exist
#   - Handling SARIF output directories securely
#   - Creating tracked temporary files
#   - Moving files securely with strict permissions
#   - Optional JSON validation
#   - Resolving the repository root directory
#
# Security & CI/CD:
#   - SARIF files: chmod 600
#   - Directories: chmod 700
#   - Tempfiles auto-cleaned on exit
#   - Safe handling of filenames and paths

# -------------------------------
# Tool availability checker
# -------------------------------
# Ensures required CLI tools are installed, aborts if missing
require_tools() {
    local missing=0                  # local variable to track missing tools
    for tool in "$@"; do             # iterate over all arguments ($@)
        # command -v returns 0 if command exists; >/dev/null 2>&1 hides output
        if ! command -v "$tool" >/dev/null 2>&1; then
            log_error "Required tool not found in PATH: $tool"
            missing=1
        fi
    done
    # [[ ... ]] is Bash conditional; && die ... means call die if missing != 0
    [[ $missing -ne 0 ]] && die "Missing required tools; aborting."
}

# -------------------------------
# SARIF output directory helper
# -------------------------------
# Creates directory with secure owner-only permissions
ensure_sarif_dir() {
    # Use argument $1, or fallback to SARIF_OUT_DIR, or finally default ./sarif-reports
    local dir="${1:-${SARIF_OUT_DIR:-./sarif-reports}}"

    umask 077                  # Restrict creation permissions for safety
    mkdir -p "$dir"            # create directory including parents
    chmod 700 "$dir" || true   # force owner-only access; ignore errors

    printf "%s" "$dir"         # return the directory path
}

# -------------------------------
# Secure file move helper
# -------------------------------
# Moves a file while enforcing strict permissions
secure_move() {
    local src="$1" dst="$2"

    # Fail if src or dst are empty
    [[ -z "$src" || -z "$dst" ]] && die "secure_move requires <src> and <dst>"

    # Fail if source file missing or empty
    [[ ! -s "$src" ]] && die "secure_move: source missing or empty: $src"

    umask 077                         # ensure strict permissions
    mv -f -- "$src" "$dst"            # move file safely; -- prevents issues with filenames starting with -
    chmod 600 "$dst" 2>/dev/null      # restrict permissions on destination
}

# Restrict permissions on an existing file
harden_file() {
    local f="$1"
    [[ -e "$f" ]] || return 0          # do nothing if file doesn’t exist
    chmod 600 "$f" 2>/dev/null        # set owner-only permissions
}

# -------------------------------
# Temporary file helpers
# -------------------------------
_tmpfiles=()  # Array to track tempfiles for cleanup

# Create a tracked tempfile
make_tmp() {
    local tmp
    # mktemp generates a unique tempfile; || die aborts if it fails
    tmp="$(mktemp -t ci.XXXXXX)" || die "mktemp failed"
    _tmpfiles+=("$tmp")                # add to tracking array
    printf "%s" "$tmp"                 # return tempfile path
}

# Cleanup tracked tempfiles on exit
_cleanup_tmpfiles() {
    for f in "${_tmpfiles[@]:-}"; do  # iterate over array; :- prevents error if empty
        [[ -e "$f" ]] && rm -f -- "$f" || true
    done
}
trap _cleanup_tmpfiles EXIT          # call cleanup function when script exits

# -------------------------------
# Optional JSON validation
# -------------------------------
# Validates JSON file if jq is installed
json_validate() {
    local file="$1"

    [[ -z "$file" ]] && die "json_validate requires a filename"
    [[ ! -s "$file" ]] && { log_warn "json_validate: file empty or missing: $file"; return 1; }

    # Check if jq exists and run it to validate JSON
    if command -v jq >/dev/null 2>&1; then
        jq empty "$file" 2>/dev/null || { log_error "Invalid JSON: $file"; return 1; }
    else
        log_warn "jq not found; skipping strict JSON validation for $file"
    fi
    return 0
}

# -------------------------------
# Repository root helper
# -------------------------------
# Resolves repo root via git or fallback
repo_root() {
    # git rev-parse returns top-level git dir; if fails, fallback to env or current dir
    if git_root="$(git rev-parse --show-toplevel 2>/dev/null)"; then
        printf "%s" "$git_root"
    else
        printf "%s" "${GITHUB_WORKSPACE:-$(pwd)}"
    fi
}
