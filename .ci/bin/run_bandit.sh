# Purpose: Run Bandit, convert findings to SARIF, and keep CI green.
# Behavior: Non-blocking; outputs SARIF for GitHub Security tab.
# CI: Strict shell, secure perms, minimal noise.

set -Eeuo pipefail
umask 077
export LC_ALL=C.UTF-8 LANG=C.UTF-8

trap 'c=$?; echo "::error title=run_bandit.sh failed,line=${LINENO}::exit ${c}"; exit ${c}' ERR

# -----------------------------
# Config (env overrides allowed)
# -----------------------------
: "${SARIF_DIR:=sarif-reports}"
: "${BANDIT_VERSION:=1.8.6}"
: "${GITHUB_WORKSPACE:=${PWD}}"
: "${BANDIT_SEVERITY_LEVEL:=low}"   # low|medium|high
: "${BANDIT_QUIET:=true}"
: "${BANDIT_TARGETS:=${GITHUB_WORKSPACE}}"
: "${BANDIT_EXCLUDE:=}"             # comma-separated paths for -x
: "${SKIP_PIP_INSTALL:=false}"

# -----------------------------
# Helpers
# -----------------------------
write_empty_sarif() {
  local out="$1" tool="$2" ver="$3"
  mkdir -p "$(dirname "$out")"
  printf '{"version":"2.1.0","runs":[{"tool":{"driver":{"name":"%s","version":"%s"}},"results":[]}]} \n' \
    "$tool" "$ver" > "$out"
  chmod 600 "$out" 2>/dev/null || true
}

harden_artifact() { chmod 600 "$1" 2>/dev/null || true; }

# -----------------------------
# Install Bandit (optional)
# -----------------------------
if [[ "${SKIP_PIP_INSTALL}" != "true" ]]; then
  echo "::group::Install Bandit ${BANDIT_VERSION}"
  python -m pip install --upgrade pip >/dev/null
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
[[ "${BANDIT_QUIET}" == "true" ]] && bandit_args+=("-q")
[[ -n "${BANDIT_EXCLUDE}" ]] && bandit_args+=("-x" "${BANDIT_EXCLUDE}")

bandit "${bandit_args[@]}" || true
echo "::endgroup::"

# Summary log
python - <<'PY'
import json, os
path = os.environ.get("BANDIT_JSON","")
try:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    results = data.get("results") or []
    print(f"::notice title=Bandit summary::results={len(results)}")
    for r in results[:5]:
        print(f"::notice title=Bandit sample::{r.get('test_id')} {r.get('issue_severity')} {r.get('filename')}:{r.get('line_number')}")
except Exception as e:
    print(f"::warning title=Bandit JSON parse failed::{e}")
PY

# -----------------------------
# Convert JSON → SARIF
# -----------------------------
export BANDIT_JSON_PATH="${BANDIT_JSON}" BANDIT_VERSION SARIF_DIR GITHUB_WORKSPACE

echo "::group::Convert Bandit JSON to SARIF"
if ! python "$(dirname "$0")/bandit_to_sarif.py"; then
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
