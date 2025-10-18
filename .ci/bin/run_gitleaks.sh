#!/usr/bin/env bash
# run_gitleaks.sh — Run Gitleaks secret detection and convert results to SARIF format.
#
# Usage:
#   Source common scripts first (strict_mode.sh, config.sh, sarif_utils.sh, installations.sh)
#   Then run this script in CI or locally
#
# Notes:
#   - Gitleaks is often run via Docker in CI.
#   - Local binary fallback is supported if available.

# -------------------------------
# Load common scripts
# -------------------------------
source ".ci/common/strict_mode.sh"    # Enforce strict bash mode
source ".ci/common/config.sh"         # Load configuration variables
source ".ci/common/sarif_utils.sh"    # SARIF helper functions
source ".ci/common/installations.sh"  # Installation helpers

# -------------------------------
# Paths
# -------------------------------
root="$(repo_root)"                     # Repository root directory
sarif_dir="$(ensure_sarif_dir "${SARIF_OUT_DIR}")" # Ensure SARIF output directory exists
sarif_out="${sarif_dir}/gitleaks.sarif" # SARIF output path

# -------------------------------
# Ensure Gitleaks is installed
# -------------------------------
install_gitleaks_or_exit || log_warn "Gitleaks may not be installed locally; consider Docker usage in CI"

log_info "Running Gitleaks scan (root=${root}) -> ${sarif_out}"

# -------------------------------
# Run Gitleaks
# -------------------------------
# Prefer local binary; Docker fallback is implied but not automatic
if command -v gitleaks >/dev/null 2>&1; then
    gitleaks detect \
        --source "${root}" \
        --report-format sarif \
        --report-path "${sarif_out}" || true
else
    log_warn "Gitleaks binary not found; skipping local scan. Use Docker image in CI."
fi

# -------------------------------
# Harden SARIF file permissions
# -------------------------------
harden_file "${sarif_out}"

log_info "Gitleaks SARIF: ${sarif_out}"
