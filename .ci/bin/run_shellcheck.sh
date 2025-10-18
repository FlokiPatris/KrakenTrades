#!/usr/bin/env bash
# run_shellcheck.sh — Run ShellCheck linter on shell scripts and convert results to SARIF.

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
json_out="${sarif_dir}/shellcheck.json"    # JSON output path
sarif_out="${sarif_dir}/shellcheck.sarif"  # SARIF output path

# -------------------------------
# Ensure ShellCheck is installed
# -------------------------------
install_shellcheck_or_exit || log_warn "install_shellcheck_or_exit returned non-zero; continuing"

# -------------------------------
# Collect shell scripts to lint
# -------------------------------
log_info "Collecting shell scripts under ${root}"

# Try git to list tracked & untracked shell scripts
mapfile -t files < <(git -C "${root}" ls-files --others --cached --exclude-standard | grep -E '\.sh$' || true)

# Fallback to find if git returns no files
if [[ ${#files[@]} -eq 0 ]]; then
  mapfile -t files < <(find "${root}" -type f -name '*.sh' -not -path '*/.git/*' || true)
fi

log_info "Running shellcheck on ${#files[@]} files"

# -------------------------------
# Run ShellCheck
# -------------------------------
# -f json: output in JSON format
# Redirect stdout to JSON file, stderr suppressed to avoid CI noise
shellcheck -f json "${files[@]}" > "${json_out}" 2>/dev/null || true

# -------------------------------
# Convert JSON to SARIF
# -------------------------------
python3 .ci/bin/sarif_convert.py shellcheck \
  --in "${json_out}" \
  --out "${sarif_out}" \
  --base-uri "${root}"

# -------------------------------
# Harden SARIF file permissions
# -------------------------------
harden_file "${sarif_out}"

log_info "ShellCheck SARIF: ${sarif_out}"
