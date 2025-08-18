#!/usr/bin/env bash
# run_shellcheck.sh — run shellcheck and convert to SARIF
source ".ci/common/strict_mode.sh"
source ".ci/common/config.sh"
source ".ci/common/sarif_utils.sh"
source ".ci/common/installations.sh"

root="$(repo_root)"
sarif_dir="$(ensure_sarif_dir "${SARIF_OUT_DIR}")"
json_out="${sarif_dir}/shellcheck.json"
sarif_out="${sarif_dir}/shellcheck.sarif"

install_shellcheck_or_exit || log_warn "install_shellcheck_or_exit returned non-zero; continuing"

# Find shell scripts to lint
log_info "Collecting shell scripts under ${root}"
mapfile -t files < <(git -C "${root}" ls-files --others --cached --exclude-standard | grep -E '\.sh$' || true)
if [[ ${#files[@]} -eq 0 ]]; then
  # fallback to find
  mapfile -t files < <(find "${root}" -type f -name '*.sh' -not -path '*/.git/*' || true)
fi

log_info "Running shellcheck on ${#files[@]} files"
# Run shellcheck -f json prints to stdout; redirect to JSON file
shellcheck -f json "${files[@]}" > "${json_out}" 2>/dev/null || true

log_info "Converting shellcheck JSON to SARIF"
python3 .ci/bin/sarif_convert.py shellcheck --in "${json_out}" --out "${sarif_out}" --base-uri "${root}"

harden_file "${sarif_out}"
log_info "ShellCheck sarif: ${sarif_out}"
