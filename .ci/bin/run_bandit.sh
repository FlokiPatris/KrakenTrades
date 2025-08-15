#!/usr/bin/env bash
# Purpose: Run Bandit against the repository, never fail the job on findings,
#          convert JSON → SARIF, and harden the SARIF artifact.
# Behavior: Non-blocking. Findings propagate to GitHub Security tab via SARIF.
# CI-friendly: Strict shell, safe perms, no secrets echoed.

set -Eeuo pipefail
umask 077
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# Trap with concise GitHub annotation on error
trap 'c=$?; echo "::error title=run_bandit.sh failed,line=${LINENO}::exit ${c}"; exit ${c}' ERR

# -----------------------------
# Config (env overrides allowed)
# -----------------------------
: "${SARIF_DIR:=sarif-reports}"
: "${BANDIT_VERSION:=1.8.6}"
: "${GITHUB_WORKSPACE:=${PWD}}"
: "${BANDIT_SEVERITY_LEVEL:=low}"   # low, medium, high
: "${BANDIT_QUIET:=true}"           # true -> add -q
: "${BANDIT_TARGETS:=${GITHUB_WORKSPACE}}"
: "${BANDIT_EXCLUDE:=}"             # comma-separated paths for -x
: "${SKIP_PIP_INSTALL:=false}"      # true -> skip pip install

# -----------------------------
# Helpers
# -----------------------------
write_empty_sarif() {
  # usage: write_empty_sarif <file> <tool> <version>
  local out="$1" tool="$2" ver="$3"
  mkdir -p "$(dirname "$out")"
  printf '{"version":"2.1.0","runs":[{"tool":{"driver":{"name":"%s","version":"%s"}},"results":[]}]} \n' "$tool" "$ver" > "$out"
  chmod 600 "$out" 2>/dev/null || true
}

harden_artifact() {
  chmod 600 "$1" 2>/dev/null || true
}

# -----------------------------
# Install Bandit (optional)
# -----------------------------
if [[ "${SKIP_PIP_INSTALL}" != "true" ]]; then
  echo "::group::Install Bandit ${BANDIT_VERSION}"
  python -m pip install --upgrade pip >/dev/null
  # pin exact version for reproducibility
  pip install --disable-pip-version-check --no-cache-dir "bandit[toml]==${BANDIT_VERSION}"
  echo "::endgroup::"
else
  echo "::notice title=Bandit install skipped::SKIP_PIP_INSTALL=${SKIP_PIP_INSTALL}"
fi

# -----------------------------
# Run Bandit → JSON (non-fatal)
# -----------------------------
mkdir -p "${SARIF_DIR}"
tmpdir="${RUNNER_TEMP:-/tmp}"
BANDIT_JSON="$(mktemp -p "${tmpdir}" bandit-XXXX.json)"

echo "::group::Run Bandit scan"
bandit_args=(
  "-r" "${BANDIT_TARGETS}"
  "--severity-level" "${BANDIT_SEVERITY_LEVEL}"
  "-f" "json"
  "-o" "${BANDIT_JSON}"
)
if [[ "${BANDIT_QUIET}" == "true" ]]; then
  bandit_args+=("-q")
fi
if [[ -n "${BANDIT_EXCLUDE}" ]]; then
  bandit_args+=("-x" "${BANDIT_EXCLUDE}")
fi

# IMPORTANT: Do not fail the job if Bandit finds issues
# Bandit exits non-zero when issues are found; swallow to keep pipeline green.
bandit "${bandit_args[@]}" || true
echo "::endgroup::"

# Quick visibility: print a small summary to logs without leaking code
python - <<'PY'
import json, os
path = os.environ.get("BANDIT_JSON","")
try:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    results = data.get("results") or []
    print(f"::notice title=Bandit summary::results={len(results)}")
    for r in results[:5]:
        tid = r.get("test_id")
        sev = r.get("issue_severity")
        fn  = r.get("filename")
        ln  = r.get("line_number")
        print(f"::notice title=Bandit sample::{tid} {sev} {fn}:{ln}")
except Exception as e:
    print(f"::warning title=Bandit JSON parse failed::{e}")
PY

# -----------------------------
# Convert JSON → SARIF
# -----------------------------
export BANDIT_JSON_PATH="${BANDIT_JSON}"
export BANDIT_VERSION
export SARIF_DIR
export GITHUB_WORKSPACE

echo "::group::Convert Bandit JSON to SARIF"
if python "$(dirname "$0")/bandit_to_sarif.py"; then
  :
else
  echo "::warning title=bandit_to_sarif.py failed::Writing empty SARIF"
  write_empty_sarif "${SARIF_DIR}/bandit.sarif" "bandit" "${BANDIT_VERSION}"
fi
harden_artifact "${SARIF_DIR}/bandit.sarif"
echo "::endgroup::"

# -----------------------------
# Cleanup
# -----------------------------
rm -f -- "${BANDIT_JSON}"
exit 0
