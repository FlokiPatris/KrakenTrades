#!/usr/bin/env bash
# run_gitleaks.sh — run gitleaks via Docker image (recommended) and write SARIF
source ".ci/common/strict_mode.sh"
source ".ci/common/config.sh"
source ".ci/common/sarif_utils.sh"

root="$(repo_root)"
sarif_dir="$(ensure_sarif_dir "${SARIF_OUT_DIR}")"
sarif_out="${sarif_dir}/gitleaks.sarif"

image="${GITLEAKS_IMAGE:-zricethezav/gitleaks}"
tag="${GITLEAKS_IMAGE_TAG:-latest}"

log_info "Running gitleaks ${image}:${tag} via Docker"

if command -v gitleaks >/dev/null 2>&1; then
  gitleaks detect --source . \
    --report-format sarif \
    --report-path "$sarif_out" || true
  if [[ -f "$sarif_out" ]]; then
    harden_file "$sarif_out"
    log_info "Gitleaks SARIF written to $sarif_out"
  else
    log_warn "Gitleaks did not produce SARIF (check version and permissions)"
  fi
else
  log_warn "Gitleaks není nainstalovaný; spusť přes GitHub Action nebo si ho nainstaluj."
fi
