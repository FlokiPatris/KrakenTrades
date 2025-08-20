#!/usr/bin/env bash
# run_bandit.sh — Run Bandit security linter and convert results to SARIF format.

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
json_out="${sarif_dir}/bandit.json"    # Intermediate JSON output
sarif_out="${sarif_dir}/bandit.sarif"  # Final SARIF output

# -------------------------------
# Ensure Bandit is installed
# -------------------------------
install_bandit_or_exit || log_warn "install_bandit_or_exit returned non-zero; continuing"

log_info "Running Bandit scan (root=${root}) -> ${json_out}"

# -------------------------------
# Run Bandit
# -------------------------------
# Recursive scan; JSON output; do not fail CI if issues are found
bandit -r "${root}" -f json -o "${json_out}" || true

# -------------------------------
# Convert JSON to SARIF
# -------------------------------
python3 .ci/bin/sarif_convert.py bandit \
    --in "${json_out}" \
    --out "${sarif_out}" \
    --base-uri "${root}"

# -------------------------------
# Harden SARIF file permissions
# -------------------------------
harden_file "${sarif_out}"

# Optional: secure intermediate JSON output
if [[ -f "${json_out}" ]]; then
    chmod 600 "${json_out}" || true
fi

log_info "Bandit SARIF: ${sarif_out}"
