# sarif_utils.sh — SARIF helper functions for CI/CD
# Ensures predictable shell behavior, minimal permissions, and no secrets leakage.

set -Eeuo pipefail
shopt -s lastpipe
umask 077

# === Constants ===
SARIF_VERSION="2.1.0"
DEFAULT_SARIF_DIR="${SARIF_DIR:-sarif-reports}"

# === Logging helpers ===
log_info()   { printf '[INFO] %s\n' "$*" >&2; }
log_error()  { printf '[ERROR] %s\n' "$*" >&2; }

# === Permission hardening ===
harden_artifact() {
    # chmod 600 for the given file, ignore if non‑existent
    local file="$1"
    if [[ -f "$file" ]]; then
        chmod 600 "$file" 2>/dev/null || true
        log_info "Hardened permissions for $file"
    else
        log_error "File not found: $file"
    fi
}

# === SARIF generators ===
write_empty_sarif() {
    # usage: write_empty_sarif <file> <tool> <version>
    local out_file="$1"
    local tool_name="$2"
    local tool_version="$3"

    mkdir -p "$(dirname "$out_file")"
    printf '{"version":"%s","runs":[{"tool":{"driver":{"name":"%s","version":"%s"}},"results":[]}]} \n' \
        "$SARIF_VERSION" "$tool_name" "$tool_version" > "$out_file"

    harden_artifact "$out_file"
    log_info "Created empty SARIF for $tool_name@$tool_version"
}

json_to_sarif() {
    # usage: json_to_sarif <json_in> <sarif_out> <tool> <version>
    local json_in="$1"
    local sarif_out="$2"
    local tool_name="$3"
    local tool_version="$4"

    if [[ ! -f "$json_in" ]]; then
        log_error "JSON input not found: $json_in"
        return 1
    fi

    python .ci/bin/pip_audit_to_sarif.py "$json_in" "$sarif_out" "$tool_name" "$tool_version"
    harden_artifact "$sarif_out"
    log_info "Converted $json_in to SARIF for $tool_name@$tool_version"
}

# === Env validation (fail early in CI) ===
validate_env() {
    local missing=false
    for var in SARIF_DIR; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Missing required env var: $var"
            missing=true
        fi
    done
    $missing && return 1 || return 0
}

# Only run validation if executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    validate_env || exit 1
fi
