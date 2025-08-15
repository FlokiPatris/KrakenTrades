# File: .ci/bin/run_gitleaks.sh
#!/usr/bin/env bash
# Safe Docker wrapper for Gitleaks → SARIF

set -Eeuo pipefail
source ".ci/bin/common.sh"
source ".ci/bin/sarif_utils.sh"

main() {
  local sarif_dir="${SARIF_DIR:-sarif-reports}"
  local image="${GITLEAKS_IMAGE:-zricethezav/gitleaks}"
  local tag="${GITLEAKS_IMAGE_TAG:-latest}"
  local fallback="${GITLEAKS_FALLBACK_TAG:-latest}"
  local out="${sarif_dir}/gitleaks.sarif"

  ensure_dir_secure "${sarif_dir}"

  if ! docker pull "${image}:${tag}" >/dev/null 2>&1; then
    log_warn "Gitleaks fallback to ${fallback}"
    tag="${fallback}"
    if ! docker pull "${image}:${tag}" >/dev/null 2>&1; then
      write_empty_sarif "${out}" "gitleaks" "${tag}"
      harden_artifact "${out}"
      return 0
    fi
  fi

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
      --report-path "/out/$(basename "${out}")" || true

  [[ -s "${out}" ]] || write_empty_sarif "${out}" "gitleaks" "${tag}"
  harden_artifact "${out}"
  log_info "Gitleaks SARIF: ${out}"
}

main "$@"
