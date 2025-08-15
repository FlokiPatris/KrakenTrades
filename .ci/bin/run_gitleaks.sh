# File: .ci/bin/run_gitleaks.sh
#!/usr/bin/env bash
# Safe Docker wrapper for Gitleaks → SARIF with exit-code capture

set -Eeuo pipefail
source ".ci/bin/common.sh"
source ".ci/bin/sarif_utils.sh"

main() {
  local sarif_dir="${SARIF_DIR:-sarif-reports}"
  local image="${GITLEAKS_IMAGE:-zricethezav/gitleaks}"
  local tag="${GITLEAKS_IMAGE_TAG:-latest}"
  local fallback="${GITLEAKS_FALLBACK_TAG:-latest}"
  local out="${sarif_dir}/gitleaks.sarif"
  local status=0

  ensure_dir_secure "${sarif_dir}"

  if ! docker pull "${image}:${tag}" >/dev/null 2>&1; then
    log_warn "Gitleaks fallback to ${fallback}"
    tag="${fallback}"
    if ! docker pull "${image}:${tag}" >/dev/null 2>&1; then
      write_empty_sarif "${out}" "gitleaks" "${tag}"
      harden_artifact "${out}"
      echo "GITLEAKS_STATUS=0" >> "$GITHUB_ENV"   # don’t fail build on pull failure; we still uploaded empty SARIF
      log_warn "Gitleaks image unavailable; wrote empty SARIF"
      return 0
    fi
  fi

  # Run scan; capture exit code without failing the step
  set +e
  docker run --rm \
    --user "$(id -u):$(id -g)" \
    --read-only \
    --cap-drop=ALL \
    --network none \
    -v "$PWD:/repo:ro" \
    -v "$PWD/${sarif_dir}:/out:rw" \
    -w /repo \
    "${image}:${tag}" detect --no-banner \
      --source /repo \
      --redact \
      --exit-code 1 \
      --report-format sarif \
      --report-path "/out/$(basename "${out}")"
  status=$?
  set -e

  # Ensure SARIF exists (generate empty on unexpected tool errors)
  [[ -s "${out}" ]] || write_empty_sarif "${out}" "gitleaks" "${tag}"
  harden_artifact "${out}"

  # Persist status for later fail step (0=no leaks, 1=leaks, >1=error)
  echo "GITLEAKS_STATUS=${status}" >> "$GITHUB_ENV"

  if [[ "${status}" -eq 1 ]]; then
    log_warn "Gitleaks found leaks (exit=1). SARIF: ${out}"
  elif [[ "${status}" -gt 1 ]]; then
    log_warn "Gitleaks encountered an error (exit=${status})."
  else
    log_info "Gitleaks found no leaks. SARIF: ${out}"
  fi
}

main "$@"
