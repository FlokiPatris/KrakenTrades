#!/usr/bin/env bash
# run_pip_audit.sh — run pip-audit, convert to SARIF
source ".ci/common/strict_mode.sh"
source ".ci/common/config.sh"
source ".ci/common/sarif_utils.sh"
source ".ci/common/installations.sh"

root="$(repo_root)"
sarif_dir="$(ensure_sarif_dir "${SARIF_OUT_DIR}")"
json_out="${sarif_dir}/pip-audit.json"
sarif_out="${sarif_dir}/pip-audit.sarif"

install_pip_audit_or_exit || log_warn "install_pip_audit_or_exit returned non-zero; continuing"

log_info "Running pip-audit -> ${json_out}"
# try pip-audit CLI, fallback to module invocation
if command -v pip-audit >/dev/null 2>&1; then
  pip-audit -f json -o "${json_out}" || true
else
  python3 -m pip_audit -f json -o "${json_out}" || true
fi

log_info "Converting pip-audit JSON to SARIF"
python3 .ci/bin/sarif_convert.py pip-audit --in "${json_out}" --out "${sarif_out}" --base-uri "${root}" 

harden_file "${sarif_out}"
log_info "pip-audit sarif: ${sarif_out}"
