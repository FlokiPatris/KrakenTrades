#!/usr/bin/env bash
# run_trivy.sh — run trivy with sarif output
source ".ci/common/strict_mode.sh"
source ".ci/common/config.sh"
source ".ci/common/sarif_utils.sh"
source ".ci/common/installations.sh"

root="$(repo_root)"
sarif_dir="$(ensure_sarif_dir "${SARIF_OUT_DIR}")"
sarif_out="${sarif_dir}/trivy.sarif"

install_trivy_or_exit || log_warn "install_trivy_or_exit failed or skipped"

# default scan: filesystem root of repo
target="${TRIVY_TARGET:-${root}}"
mode="${TRIVY_MODE:-fs}"
severity="${TRIVY_SEVERITY:-CRITICAL,HIGH,MEDIUM}"
timeout="${TRIVY_TIMEOUT:-5m}"

log_info "Running trivy mode=${mode} target=${target} -> ${sarif_out}"

if [[ "${mode}" == "fs" ]]; then
  trivy fs --format sarif --severity "${severity}" --timeout "${timeout}" -o "${sarif_out}" "${target}" || true
elif [[ "${mode}" == "image" ]]; then
  trivy image --format sarif --severity "${severity}" --timeout "${timeout}" -o "${sarif_out}" "${target}" || true
else
  log_warn "Unsupported TRIVY_MODE=${mode}; skipping trivy"
  exit 0
fi

if [[ -f "${sarif_out}" && -s "${sarif_out}" ]]; then
  harden_file "${sarif_out}"
  if grep -q '"results":' "${sarif_out}" 2>/dev/null; then
    if [[ "${TRIVY_EXIT_CODE:-0}" -ne 0 ]]; then
      log_warn "Trivy reported findings; exiting with ${TRIVY_EXIT_CODE}"
      exit "${TRIVY_EXIT_CODE}"
    fi
  fi
else
  log_warn "Trivy did not produce a SARIF file"
fi

log_info "Trivy SARIF: ${sarif_out}"
