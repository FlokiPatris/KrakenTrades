#!/usr/bin/env bash
# run_pip_audit.sh — Run pip-audit vulnerability scanner and convert results to SARIF format.

# Load common scripts
source ".ci/common/strict_mode.sh"    # Enforce strict bash mode
source ".ci/common/config.sh"         # Load configuration variables
source ".ci/common/sarif_utils.sh"    # SARIF helper functions
source ".ci/common/installations.sh"  # Installation helpers

# -------------------------------
# Paths
# -------------------------------
root="$(repo_root)"  # Repository root directory
sarif_dir="$(ensure_sarif_dir "${SARIF_OUT_DIR}")"  # Ensure SARIF output directory exists
json_out="${sarif_dir}/pip-audit.json"  # JSON output path
sarif_out="${sarif_dir}/pip-audit.sarif"  # SARIF output path

# -------------------------------
# Ensure pip-audit is installed
# -------------------------------
# Will attempt installation; logs warning if installation fails but continues execution
install_pip_audit_or_exit || log_warn "install_pip_audit_or_exit returned non-zero; continuing"

log_info "Running pip-audit -> ${json_out}"

# -------------------------------
# Run pip-audit
# -------------------------------
# Prefer CLI if available; fallback to module invocation using python3
if command -v pip-audit >/dev/null 2>&1; then
  pip-audit -f json -o "${json_out}" || true  # Generate JSON output; never fail CI
else
  python3 -m pip_audit -f json -o "${json_out}" || true
fi

# -------------------------------
# Convert JSON to SARIF
# -------------------------------
python3 .ci/bin/sarif_convert.py pip-audit \
  --in "${json_out}" \
  --out "${sarif_out}" \
  --base-uri "${root}"

# -------------------------------
# Harden SARIF file permissions
# -------------------------------
harden_file "${sarif_out}"

log_info "pip-audit SARIF: ${sarif_out}"
