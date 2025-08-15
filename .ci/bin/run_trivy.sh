set -euo pipefail

# ==========================
# Trivy install runner
# ==========================
TRIVY_VERSION="${TRIVY_VERSION:-}"   # Set to e.g. 0.51.4, or leave empty for latest
ARCH="64bit"
OS="Linux"

echo "==> Installing prerequisites..."
sudo apt-get update -y
sudo apt-get install -y wget apt-transport-https gnupg lsb-release

if [[ -n "$TRIVY_VERSION" ]]; then
    echo "==> Installing Trivy $TRIVY_VERSION from GitHub release..."
    DEB_FILE="trivy_${TRIVY_VERSION}_${OS}-${ARCH}.deb"
    wget -q "https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/${DEB_FILE}" \
        -O "/tmp/${DEB_FILE}" || {
        echo "❌ Failed to download version ${TRIVY_VERSION}. Please check if it exists."
        exit 1
    }
    sudo dpkg -i "/tmp/${DEB_FILE}"
else
    echo "==> Installing latest Trivy from official Aqua Security repo..."
    wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key \
        | sudo gpg --dearmor -o /usr/share/keyrings/trivy.gpg
    echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb \
        $(lsb_release -sc) main" | \
        sudo tee /etc/apt/sources.list.d/trivy.list
    sudo apt-get update -y
    sudo apt-get install -y trivy
fi

echo "==> Trivy installation complete!"
echo "==> Running Trivy scan..."
trivy --version
# Place your scan command(s) below
# e.g., trivy fs .

echo "✅ Trivy scan finished."
