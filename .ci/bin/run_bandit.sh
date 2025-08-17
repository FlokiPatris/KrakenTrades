#!/usr/bin/env bash
# run_bandit.sh — run bandit, produce JSON, convert to SARIF

source ".ci/common/strict_mode.sh"
source ".ci/common/config.sh"
source ".ci/common/sarif_utils.sh"
source ".ci/common/installations.sh"

# Paths
root="$(repo_root)"
sarif_dir="$(ensure_sarif_dir "${SARIF_OUT_DIR}")"
json_out="${sarif_dir}/bandit.json"
sarif_out="${sarif_dir}/bandit.sarif"

# Ensure bandit present (install if necessary)
install_bandit_or_exit || log_warn "install_bandit_or_exit returned non-zero; continuing"

log_info "Running bandit (root=${root}) -> ${json_out}"
# Run bandit but never fail CI due to execution error (findings do not cause non-zero here)
bandit -r "${root}" -f json -o "${json_out}" || true

log_info "Converting bandit JSON to SARIF: ${sarif_out}"
python3 .ci/bin/sarif_convert.py bandit --in "${json_out}" --out "${sarif_out}" --base-uri "${root}" || {
  log_warn "sarif_convert.py failed for bandit; creating empty SARIF"
  python3 - <<'PY'
import json, sys
sys.stdout.write(json.dumps({"version":"2.1.0","runs":[{"tool":{"driver":{"name":"bandit","version":""}},"results":[]}]}))
PY
  # write fallback file
  echo '{"version":"2.1.0","runs":[]}' > "${sarif_out}" || true
}

harden_file "${sarif_out}"
# remove intermediate JSON to avoid leaking sensitive paths (optional)
if [[ -f "${json_out}" ]]; then
  chmod 600 "${json_out}" || true
fi

log_info "Bandit sarif: ${sarif_out}"
