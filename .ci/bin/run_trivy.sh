#!/usr/bin/env bash
# run_trivy.sh — Run Trivy vulnerability scanner and output results in SARIF format.

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
sarif_out="${sarif_dir}/trivy.sarif"  # SARIF output file

# -------------------------------
# Ensure Trivy is installed
# -------------------------------
install_trivy_or_exit || log_warn "install_trivy_or_exit failed or skipped"

# -------------------------------
# Scan configuration
# -------------------------------
# Target defaults to repository root unless TRIVY_TARGET is set
target="${TRIVY_TARGET:-${root}}"
mode="${TRIVY_MODE:-fs}"  # fs = filesystem scan, image = container image scan
severity="${TRIVY_SEVERITY:-CRITICAL,HIGH,MEDIUM}"  # Vulnerability severities to include
timeout="${TRIVY_TIMEOUT:-5m}"  # Scan timeout

log_info "Running trivy mode=${mode} target=${target} -> ${sarif_out}"

# -------------------------------
# Run Trivy scan
# -------------------------------
if [[ "${mode}" == "fs" ]]; then
  # Filesystem scan
  trivy fs --format sarif --severity "${severity}" --timeout "${timeout}" -o "${sarif_out}" "${target}" || true
elif [[ "${mode}" == "image" ]]; then
  # Container image scan
  trivy image --format sarif --severity "${severity}" --timeout "${timeout}" -o "${sarif_out}" "${target}" || true
else
  log_warn "Unsupported TRIVY_MODE=${mode}; skipping trivy"
  exit 0
fi

# -------------------------------
# Post-scan SARIF processing
# -------------------------------
if [[ -f "${sarif_out}" && -s "${sarif_out}" ]]; then
  harden_file "${sarif_out}"  # Restrict file permissions

  # Check if SARIF contains results
  if grep -q '"results":' "${sarif_out}" 2>/dev/null; then
    # Exit with TRIVY_EXIT_CODE if set and non-zero
    if [[ "${TRIVY_EXIT_CODE:-0}" -ne 0 ]]; then
      log_warn "Trivy reported findings; exiting with ${TRIVY_EXIT_CODE}"
      exit "${TRIVY_EXIT_CODE}"
    fi
  fi
else
  log_warn "Trivy did not produce a SARIF file"
fi

log_info "Trivy SARIF: ${sarif_out}"
