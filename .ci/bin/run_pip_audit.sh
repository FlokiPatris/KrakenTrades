# Install + run pip-audit, convert to SARIF, export AUDIT_STATUS

set -Eeuo pipefail
source ".ci/bin/common.sh"
source ".ci/bin/sarif_utils.sh"

main() {
  local sarif_dir="${SARIF_DIR:-sarif-reports}"
  local ver="${PIP_AUDIT_VERSION:-latest}"
  local json_out="${sarif_dir}/pip-audit.json"
  local sarif_out="${sarif_dir}/pip-audit.sarif"
  local artifact="environment"
  local audit_status=0

  ensure_dir_secure "${sarif_dir}"

  python -m pip install --upgrade pip >/dev/null
  if [[ "${ver}" == "latest" ]]; then
    pip install --disable-pip-version-check --no-cache-dir pip-audit >/dev/null
  else
    pip install --disable-pip-version-check --no-cache-dir "pip-audit==${ver}" >/dev/null
  fi

  if [[ -f requirements.txt ]];
    artifact="requirements.txt"
    set -o pipefail
    pip-audit -r requirements.txt --format json --output "${json_out}" --strict || audit_status=$?
    set +o pipefail
  else
    set -o pipefail
    pip-audit --format json --output "${json_out}" --strict || audit_status=$?
    set +o pipefail

  export PIP_AUDIT_ARTIFACT_URI="${artifact}"
  if [[ -s "${json_out}" ]]; then
    json_to_sarif "${json_out}" "${sarif_out}" "pip-audit" "${ver}"
  else
    write_empty_sarif "${sarif_out}" "pip-audit" "${ver}"
  fi

  echo "AUDIT_STATUS=${audit_status}" >> "${GITHUB_ENV}"
  harden_artifact "${sarif_out}"
  [[ -f "${json_out}" ]] && harden_artifact "${json_out}"
  log_info "pip-audit status=${audit_status} SARIF=${sarif_out}"
}

main "$@"
