#!/usr/bin/env bash
set -euo pipefail

# ==========================
# Config (override via env)
# ==========================
TRIVY_VERSION="${TRIVY_VERSION:-}"           # e.g., 0.51.4; empty = latest from repo
TRIVY_MODE="${TRIVY_MODE:-fs}"               # fs | config | image | sbom
TRIVY_TARGET="${TRIVY_TARGET:-.}"            # Path, image ref, or SBOM file depending on mode
TRIVY_SCANNERS="${TRIVY_SCANNERS:-vuln,secret,misconfig}" # fs/sbom modes
TRIVY_SEVERITY="${TRIVY_SEVERITY:-CRITICAL,HIGH,MEDIUM,LOW}"
TRIVY_IGNORE_UNFIXED="${TRIVY_IGNORE_UNFIXED:-true}"      # true|false
TRIVY_EXIT_CODE="${TRIVY_EXIT_CODE:-0}"      # 0 to never fail CI; 1 to fail on findings (see --severity filter)
TRIVY_TIMEOUT="${TRIVY_TIMEOUT:-5m}"

SARIF_DIR="${SARIF_DIR:-sarif-reports}"
SARIF_FILE="${SARIF_FILE:-trivy.sarif}"
SARIF_PATH="${SARIF_DIR}/${SARIF_FILE}"

ARCH="64bit"
OS="Linux"

echo "==> Installing prerequisites..."
sudo apt-get update -y
sudo apt-get install -y wget apt-transport-https gnupg lsb-release

if [[ -n "$TRIVY_VERSION" ]]; then
  echo "==> Installing Trivy ${TRIVY_VERSION} from GitHub release..."
  DEB_FILE="trivy_${TRIVY_VERSION}_${OS}-${ARCH}.deb"
  wget -q "https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/${DEB_FILE}" -O "/tmp/${DEB_FILE}"
  sudo dpkg -i "/tmp/${DEB_FILE}"
else
  echo "==> Installing latest Trivy from Aqua Security apt repo..."
  wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo gpg --dearmor -o /usr/share/keyrings/trivy.gpg
  echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" \
    | sudo tee /etc/apt/sources.list.d/trivy.list
  sudo apt-get update -y
  sudo apt-get install -y trivy
fi

echo "==> Trivy version:"
trivy --version

echo "==> Preparing SARIF output directory: ${SARIF_DIR}"
mkdir -p "${SARIF_DIR}"

echo "==> Running Trivy scan (mode=${TRIVY_MODE}, target=${TRIVY_TARGET})..."
set +e
case "$TRIVY_MODE" in
  fs)
    trivy fs \
      --scanners "${TRIVY_SCANNERS}" \
      --severity "${TRIVY_SEVERITY}" \
      --ignore-unfixed="${TRIVY_IGNORE_UNFIXED}" \
      --timeout "${TRIVY_TIMEOUT}" \
      --no-progress \
      --format sarif \
      --output "${SARIF_PATH}" \
      "${TRIVY_TARGET}"
    ;;
  config)
    trivy config \
      --severity "${TRIVY_SEVERITY}" \
      --timeout "${TRIVY_TIMEOUT}" \
      --no-progress \
      --format sarif \
      --output "${SARIF_PATH}" \
      "${TRIVY_TARGET}"
    ;;
  image)
    trivy image \
      --severity "${TRIVY_SEVERITY}" \
      --ignore-unfixed="${TRIVY_IGNORE_UNFIXED}" \
      --timeout "${TRIVY_TIMEOUT}" \
      --no-progress \
      --format sarif \
      --output "${SARIF_PATH}" \
      "${TRIVY_TARGET}"
    ;;
  sbom)
    trivy sbom \
      --scanners "${TRIVY_SCANNERS}" \
      --severity "${TRIVY_SEVERITY}" \
      --ignore-unfixed="${TRIVY_IGNORE_UNFIXED}" \
      --timeout "${TRIVY_TIMEOUT}" \
      --no-progress \
      --format sarif \
      --output "${SARIF_PATH}" \
      "${TRIVY_TARGET}"
    ;;
  *)
    echo "Unknown TRIVY_MODE: ${TRIVY_MODE} (expected: fs|config|image|sbom)"
    exit 2
    ;;
esac
scan_rc=$?
set -e

# Honor desired CI behavior
if [[ "${TRIVY_EXIT_CODE}" != "0" ]]; then
  # Fail build if Trivy found issues (non-zero) and user wants failures to surface
  if [[ $scan_rc -ne 0 ]]; then
    echo "❌ Trivy detected issues and TRIVY_EXIT_CODE=${TRIVY_EXIT_CODE} — failing."
    exit "${TRIVY_EXIT_CODE}"
  fi
fi

# Ensure SARIF file exists
if [[ ! -s "${SARIF_PATH}" ]]; then
  echo "⚠️ SARIF not generated or empty at ${SARIF_PATH}"
  echo "Listing directory for debugging:"
  ls -la "${SARIF_DIR}" || true
  exit 3
fi

echo "✅ Trivy SARIF written to ${SARIF_PATH}"
