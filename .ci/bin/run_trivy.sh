# Purpose: Run Trivy filesystem scan (vulnerabilities + secrets), output SARIF
# Security: No secrets echoed; fails fast on missing env vars; runs in CI & Docker
# CI: Blocking or non-blocking based on TRIVY_EXIT_ON_FINDINGS

set -Eeuo pipefail
umask 077
export LC_ALL=C.UTF-8 LANG=C.UTF-8

trap 'c=$?; echo "::error title=run_trivy.sh failed,line=${LINENO}::exit ${c}"; exit ${c}' ERR

# -----------------------------
# Config (env overrides allowed)
# -----------------------------
: "${SARIF_DIR:=sarif-reports}"
: "${TRIVY_VERSION:=0.51.4}"                # pin exact version
: "${TRIVY_SEVERITY:=HIGH,CRITICAL}"        # severities to scan/fail on
: "${TRIVY_TARGET:=.}"                      # default: current repo
: "${TRIVY_EXIT_ON_FINDINGS:=true}"         # fail pipeline if true positives found
: "${SKIP_INSTALL:=false}"

# -----------------------------
# Validate critical vars
# -----------------------------
missing_vars=()
for v in SARIF_DIR TRIVY_VERSION TRIVY_SEVERITY TRIVY_TARGET; do
  [[ -z "${!v}" ]] && missing_vars+=("$v")
done
if [[ ${#missing_vars[@]} -gt 0 ]]; then
  echo "::error title=Missing required variables::${missing_vars[*]}"
  exit 1
fi

# -----------------------------
# Helpers
# -----------------------------
write_empty_sarif() {
  local out="$1" tool="$2" ver="$3"
  mkdir -p "$(dirname "$out")"
  printf '{"version":"2.1.0","runs":[{"tool":{"driver":{"name":"%s","version":"%s"}},"results":[]}]} \n' \
    "$tool" "$ver" > "$out"
  chmod 600 "$out"
}

secure_install_trivy() {
  sudo apt-get update -qq
  sudo apt-get install -y wget apt-transport-https gnupg lsb-release
  wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key \
    | sudo gpg --dearmor -o /usr/share/keyrings/trivy.gpg
  echo deb [signed-by=/usr/share/keyrings/trivy.gpg] \
    https://aquasecurity.github.io/trivy-repo/deb "$(lsb_release -sc)" main \
    | sudo tee /etc/apt/sources.list.d/trivy.list >/dev/null
  sudo apt-get update -qq
  sudo apt-get install -y "trivy=${TRIVY_VERSION}"
}

# -----------------------------
# Install Trivy if needed
# -----------------------------
if [[ "${SKIP_INSTALL}" != "true" ]]; then
  echo "::group::Install Trivy ${TRIVY_VERSION}"
  secure_install_trivy
  echo "::endgroup::"
else
  echo "::notice title=Trivy install skipped::SKIP_INSTALL=${SKIP_INSTALL}"
fi

# -----------------------------
# Run scan
# -----------------------------
mkdir -p "${SARIF_DIR}"
SARIF_OUT="${SARIF_DIR}/trivy.sarif"

echo "::group::Run Trivy filesystem scan"
trivy fs \
  --quiet \
  --format sarif \
  --output "${SARIF_OUT}" \
  --severity "${TRIVY_SEVERITY}" \
  "${TRIVY_TARGET}" || true
chmod 600 "${SARIF_OUT}"
echo "::endgroup::"

# -----------------------------
# Conditional exit on findings
# -----------------------------
if [[ "${TRIVY_EXIT_ON_FINDINGS}" == "true" ]]; then
  if grep -q '"results":\s*

\[' "${SARIF_OUT}" && ! grep -q '"results":\s*

\[\s*\]

' "${SARIF_OUT}"; then
    echo "🚨 Trivy found issues meeting severity threshold (${TRIVY_SEVERITY})"
    exit 1
  fi
fi

exit 0
